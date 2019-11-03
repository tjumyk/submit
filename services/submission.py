import json
import logging
import math
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

import tzlocal
from celery.result import AsyncResult
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import joinedload
from werkzeug.datastructures import FileStorage

from error import BasicError
from models import Submission, Task, UserAlias, Team, SubmissionFile, db, UserTeamAssociation, AutoTest, AutoTestConfig, \
    SubmissionComment
from services.auto_test import AutoTestService
from services.task import TaskService
from testbot import bot

logger = logging.getLogger(__name__)


class SubmissionServiceError(BasicError):
    pass


class AutoTestConclusionExtractionError(BasicError):
    pass


class UserSubmissionSummary:
    def __init__(self, user: UserAlias, total_submissions: int, first_submit_time: datetime,
                 last_submit_time: datetime):
        self.user = user
        self.total_submissions = total_submissions
        self.first_submit_time = first_submit_time
        self.last_submit_time = last_submit_time

    def to_dict(self):
        d = dict(user=self.user.to_dict(),
                 total_submissions=self.total_submissions,
                 first_submit_time=self.first_submit_time,
                 last_submit_time=self.last_submit_time)
        return d


class TeamSubmissionSummary:
    def __init__(self, team: Team, total_submissions: int, first_submit_time: datetime, last_submit_time: datetime):
        self.team = team
        self.total_submissions = total_submissions
        self.first_submit_time = first_submit_time
        self.last_submit_time = last_submit_time

    def to_dict(self):
        d = dict(team=self.team.to_dict(),
                 total_submissions=self.total_submissions,
                 first_submit_time=self.first_submit_time,
                 last_submit_time=self.last_submit_time)
        return d


class DailySubmissionSummary:
    def __init__(self, date: str, total: int):
        self.date = date
        self.total = total

    def to_dict(self):
        return dict(date=self.date, total=self.total)


class SubmissionCommentSummary:
    def __init__(self, submission: Submission, total_comments: int,
                 last_comment: SubmissionComment):
        self.submission = submission
        self.total_comments = total_comments
        self.last_comment = last_comment

    def to_dict(self):
        return dict(submission=self.submission.to_dict(with_submitter=True), total_comments=self.total_comments,
                    last_comment=self.last_comment.to_dict())


class LatePenalty:
    """
    In this implementation, I just store the cut numbers as-is because I'm lazy now. A better implementation is to store
    the segments (from_day, to_day, penalty). The front-end is using the latter implementation for better UI
    presentation.
    """

    def __init__(self, repr_string: str = None):
        self._cuts = []

        if repr_string:
            self._cuts = self._parse(repr_string)

    @classmethod
    def _parse(cls, repr_string: str):
        try:
            raw_cuts = [float(c) for c in repr_string.strip().split()]
        except ValueError as e:
            raise ValueError('Invalid format in late penalty string', str(e))
        if any(c < 0 for c in raw_cuts):
            raise ValueError('Invalid format in late penalty string', 'negative number found')

        cuts = []
        index = 0
        num_raw_cuts = len(raw_cuts)
        total = 0
        while True:
            cut = raw_cuts[index]
            if index == num_raw_cuts - 1 and cut < 1e-6:  # no further penalty
                break
            if total + cut > 1.0:  # fix overflow
                cut = cls._round(1.0 - total)  # remove long tails due to precision loss
                if cut > 0:
                    total += cut
                    cuts.append(cut)
                break
            total += cut
            cuts.append(cut)
            if index < num_raw_cuts - 1:  # otherwise keep using the last cut
                index += 1

        return cuts

    @staticmethod
    def _round(num: float) -> float:
        """
        Round a float to remove long tails
        """
        return round(num * 100000) / 100000

    def __repr__(self):
        return '<LatePenalty %s>' % ' '.join(str(c) for c in self._cuts)

    def compute_penalty(self, late: timedelta) -> float:
        if not self._cuts:  # no late penalty
            return 0.0
        seconds = late.total_seconds()
        if seconds <= 0:
            return 0.0
        days = math.ceil(seconds / (3600 * 24))
        return self._round(sum(self._cuts[0:days]))


class SubmissionService:
    _COMMENT_MAX_LENGTH = 512
    COMMENT_SESSION_EXPIRY = timedelta(minutes=5)

    @staticmethod
    def get(_id: int) -> Optional[Submission]:
        if _id is None:
            raise SubmissionServiceError('id is required')
        if type(_id) is not int:
            raise SubmissionServiceError('id must be an integer')
        return Submission.query.get(_id)

    @staticmethod
    def get_user_summaries(task: Task) -> List[UserSubmissionSummary]:
        if task is None:
            raise SubmissionServiceError('task is required')

        sub_query = db.session.query(UserAlias.id.label('user_id'),
                                     func.count().label('total_submissions'),
                                     func.min(Submission.created_at).label('first_submit_time'),
                                     func.max(Submission.created_at).label('last_submit_time')) \
            .filter(UserAlias.id == Submission.submitter_id,
                    Submission.task_id == task.id) \
            .group_by(UserAlias.id).subquery()
        query = db.session.query(UserAlias,
                                 sub_query.c.total_submissions,
                                 sub_query.c.first_submit_time,
                                 sub_query.c.last_submit_time) \
            .filter(sub_query.c.user_id == UserAlias.id) \
            .order_by(sub_query.c.last_submit_time)
        return [UserSubmissionSummary(user, total, first_time, last_time)
                for user, total, first_time, last_time in query.all()]

    @staticmethod
    def get_team_summaries(task: Task) -> List[TeamSubmissionSummary]:
        if task is None:
            raise SubmissionServiceError('task is required')
        if not task.is_team_task:
            raise SubmissionServiceError('task is not team task')

        sub_query = db.session.query(Team.id.label('team_id'),
                                     func.count().label('total_submissions'),
                                     func.min(Submission.created_at).label('first_submit_time'),
                                     func.max(Submission.created_at).label('last_submit_time')) \
            .filter(Team.id == UserTeamAssociation.team_id,
                    Team.task_id == task.id,
                    Submission.submitter_id == UserTeamAssociation.user_id,
                    Submission.task_id == task.id) \
            .group_by(Team.id).subquery()
        query = db.session.query(Team,
                                 sub_query.c.total_submissions,
                                 sub_query.c.first_submit_time,
                                 sub_query.c.last_submit_time) \
            .filter(sub_query.c.team_id == Team.id) \
            .order_by(sub_query.c.last_submit_time)
        return [TeamSubmissionSummary(team, total, first_time, last_submit)
                for team, total, first_time, last_submit in query.all()]

    @staticmethod
    def get_daily_summaries(task: Task) -> List[DailySubmissionSummary]:
        if task is None:
            raise SubmissionServiceError('task is required')

        # cast the 'Submission.created_at' field to the precision of days in the local timezone
        db_type = db.session.bind.dialect.name
        if db_type == 'sqlite':
            # https://www.sqlite.org/lang_datefunc.html
            created_at_day = func.date(Submission.created_at, 'localtime')
        elif db_type == 'postgresql':
            # Get the geographical local timezone, e.g. 'Australia/Sydney', to avoid the Daylight Saving Time issue.
            timezone = tzlocal.get_localzone().zone
            # https://www.postgresql.org/docs/current/functions-datetime.html
            created_at_day = func.date(func.timezone(timezone, func.timezone('utc', Submission.created_at)))
        else:  # TODO support other DB types
            raise NotImplementedError('DB type not supported for local date computation: %s' % db_type)

        sub_query = db.session.query(Submission.id.label('sid'),
                                     created_at_day.label('date')) \
            .filter(Submission.task_id == task.id)\
            .subquery()
        query = db.session.query(sub_query.c.date,
                                 func.count())\
            .group_by(sub_query.c.date) \
            .order_by(sub_query.c.date)

        if db_type == 'sqlite':
            return [DailySubmissionSummary(date, count) for date, count in query.all()]
        elif db_type == 'postgresql':
            return [DailySubmissionSummary(date.strftime('%Y-%m-%d'), count) for date, count in query.all()]
        return []  # logic should never reach here

    @staticmethod
    def get_for_task_and_user(task: Task, user: UserAlias, include_cleared=False, submitted_after: datetime = None) \
            -> List[Submission]:
        if task is None:
            raise SubmissionServiceError('task is required')
        if user is None:
            raise SubmissionServiceError('user is required')
        query = Submission.query.with_parent(task).with_parent(user)
        if not include_cleared:
            query = query.filter_by(is_cleared=False)
        if submitted_after is not None:
            query = query.filter(Submission.created_at > submitted_after)
        return query.order_by(Submission.id).all()

    @classmethod
    def get_last_auto_tests_for_task_and_user(cls, task: Task, user: UserAlias, include_cleared=False,
                                              include_private_tests=False, only_for_first_submission=False,
                                              only_for_last_submission=False) \
            -> Dict[int, Dict[int, AutoTest]]:
        if task is None:
            raise SubmissionServiceError('task is required')
        if user is None:
            raise SubmissionServiceError('user is required')

        filters = [
            Submission.task_id == task.id,
            Submission.submitter_id == user.id
        ]
        if not include_cleared:
            filters.append(Submission.is_cleared == False)
        if only_for_first_submission or only_for_last_submission:
            if only_for_first_submission and only_for_last_submission:
                raise SubmissionServiceError('cannot select both first-only and last-only submission')
            agg_method = func.max if only_for_last_submission else func.min
            sub_sub_query = db.session.query(agg_method(Submission.id).label('submission_id')) \
                .filter(*filters).subquery()
            sub_query = db.session.query(sub_sub_query.c.submission_id.label('submission_id'),
                                         func.max(AutoTest.id).label('last_test_id')) \
                .outerjoin(AutoTest, AutoTest.submission_id == sub_sub_query.c.submission_id) \
                .group_by(sub_sub_query.c.submission_id, AutoTest.config_id).subquery()
        else:
            sub_query = db.session.query(Submission.id.label('submission_id'),
                                         func.max(AutoTest.id).label('last_test_id')) \
                .outerjoin(AutoTest, AutoTest.submission_id == Submission.id) \
                .filter(*filters) \
                .group_by(Submission.id, AutoTest.config_id).subquery()
        results = db.session.query(sub_query.c.submission_id, AutoTest) \
            .outerjoin(AutoTest, AutoTest.id == sub_query.c.last_test_id) \
            .all()

        public_config_ids = None
        if not include_private_tests:  # have to run another query to get public config ids
            id_results = db.session.query(AutoTestConfig.id) \
                .filter(AutoTestConfig.is_private == False, AutoTestConfig.task_id == task.id) \
                .all()
            public_config_ids = set(r[0] for r in id_results)

        last_tests = {}
        for submission_id, test in results:
            tests = last_tests.get(submission_id)
            if tests is None:
                last_tests[submission_id] = tests = {}  # make sure all submission_ids are in last_tests even if no test
            if test is None:
                continue  # no test for this submission (we are using outer-join)
            if not include_private_tests and test.config_id not in public_config_ids:
                continue  # skip private tests
            tests[test.config_id] = test
        return last_tests

    @classmethod
    def get_auto_test_conclusions_for_task_and_user(cls, task: Task, user: UserAlias, include_private_tests=False) \
            -> Dict[int, object]:
        if task is None:
            raise SubmissionServiceError('task is required')
        if user is None:
            raise SubmissionServiceError('user is required')

        configs = task.auto_test_configs
        if not configs:
            return {}

        # NOTICE: The following logic will break if no config
        last_submission_only = True
        first_submission_only = True
        for config in configs:
            acc_method = config.results_conclusion_accumulate_method
            if acc_method != 'last':
                last_submission_only = False
            if acc_method != 'first':
                first_submission_only = False
        last_tests = cls.get_last_auto_tests_for_task_and_user(task, user, include_cleared=False,
                                                               include_private_tests=include_private_tests,
                                                               only_for_first_submission=first_submission_only,
                                                               only_for_last_submission=last_submission_only)

        late_penalties = cls.get_late_penalties_for_task_and_user(task, user)
        return cls.extract_conclusions_for_configs(configs, last_tests, late_penalties, include_private_tests)

    @classmethod
    def get_late_penalties_for_task_and_user(cls, task: Task, user: UserAlias) -> Optional[Dict[int, float]]:
        if task is None:
            raise SubmissionServiceError('task is required')
        if user is None:
            raise SubmissionServiceError('user is required')

        if not task.late_penalty:
            return None
        late_penalty = LatePenalty(task.late_penalty)

        due_time = task.due_time
        if due_time is None:
            return None

        special = TaskService.get_special_consideration_for_task_user(task, user)
        if special is not None and special.due_time_extension:
            due_time += timedelta(hours=special.due_time_extension)

        penalties = {}
        for submission in cls.get_for_task_and_user(task, user, include_cleared=False,
                                                    submitted_after=due_time):
            penalty = late_penalty.compute_penalty(submission.created_at - due_time)
            if penalty:
                penalties[submission.id] = penalty
        return penalties

    @staticmethod
    def count_for_task_and_user(task: Task, user: UserAlias, include_cleared=False) -> int:
        if task is None:
            raise SubmissionServiceError('task is required')
        if user is None:
            raise SubmissionServiceError('user is required')
        query = db.session.query(func.count()) \
            .filter(Submission.task_id == task.id,
                    Submission.submitter_id == user.id)
        if not include_cleared:
            query = query.filter(Submission.is_cleared == False)
        return query.scalar()

    @staticmethod
    def get_for_team(team: Team, include_cleared=False, submitted_after: datetime = None) -> List[Submission]:
        if team is None:
            raise SubmissionServiceError('team is required')
        query = Submission.query.filter(Submission.submitter_id == UserTeamAssociation.user_id,
                                        UserTeamAssociation.team_id == team.id,
                                        Submission.task_id == team.task_id)
        if not include_cleared:
            query = query.filter_by(is_cleared=False)
        if submitted_after is not None:
            query = query.filter(Submission.created_at > submitted_after)
        return query.order_by(Submission.id).all()

    @staticmethod
    def get_last_auto_tests_for_team(team: Team, include_cleared=False, include_private_tests=False,
                                     only_for_first_submission=False, only_for_last_submission=False) \
            -> Dict[int, Dict[int, AutoTest]]:
        if team is None:
            raise SubmissionServiceError('team is required')

        filters = [
            Submission.submitter_id == UserTeamAssociation.user_id,
            UserTeamAssociation.team_id == team.id,
            Submission.task_id == team.task_id
        ]
        if not include_cleared:
            filters.append(Submission.is_cleared == False)
        if only_for_first_submission or only_for_last_submission:
            if only_for_first_submission and only_for_last_submission:
                raise SubmissionServiceError('cannot select both first-only and last-only submission')
            agg_method = func.max if only_for_last_submission else func.min
            sub_sub_query = db.session.query(agg_method(Submission.id).label('submission_id')) \
                .filter(*filters).subquery()
            sub_query = db.session.query(sub_sub_query.c.submission_id.label('submission_id'),
                                         func.max(AutoTest.id).label('last_test_id')) \
                .outerjoin(AutoTest, AutoTest.submission_id == sub_sub_query.c.submission_id) \
                .group_by(sub_sub_query.c.submission_id, AutoTest.config_id).subquery()
        else:
            sub_query = db.session.query(Submission.id.label('submission_id'),
                                         func.max(AutoTest.id).label('last_test_id')) \
                .outerjoin(AutoTest, AutoTest.submission_id == Submission.id) \
                .filter(*filters).group_by(Submission.id, AutoTest.config_id) \
                .subquery()
        results = db.session.query(sub_query.c.submission_id, AutoTest) \
            .outerjoin(AutoTest, AutoTest.id == sub_query.c.last_test_id) \
            .all()

        public_config_ids = None
        if not include_private_tests:  # have to run another query to get public config ids
            id_results = db.session.query(AutoTestConfig.id) \
                .filter(AutoTestConfig.is_private == False, AutoTestConfig.task_id == team.task_id) \
                .all()
            public_config_ids = set(r[0] for r in id_results)

        last_tests = {}
        for submission_id, test in results:
            tests = last_tests.get(submission_id)
            if tests is None:
                last_tests[submission_id] = tests = {}  # make sure all submission_ids are in last_tests even if no test
            if test is None:
                continue  # no test for this submission (we are using outer-join)
            if not include_private_tests and test.config_id not in public_config_ids:
                continue  # skip private tests
            tests[test.config_id] = test
        return last_tests

    @classmethod
    def get_auto_test_conclusions_for_team(cls, team: Team, include_private_tests=False) \
            -> Dict[int, object]:
        if team is None:
            raise SubmissionServiceError('team is required')

        task = team.task
        configs = task.auto_test_configs
        if not configs:
            return {}

        # NOTICE: The following logic will break if no config
        last_submission_only = True
        first_submission_only = True
        for config in configs:
            acc_method = config.results_conclusion_accumulate_method
            if acc_method != 'last':
                last_submission_only = False
            if acc_method != 'first':
                first_submission_only = False
        last_tests = cls.get_last_auto_tests_for_team(team, include_cleared=False,
                                                      include_private_tests=include_private_tests,
                                                      only_for_first_submission=first_submission_only,
                                                      only_for_last_submission=last_submission_only)

        late_penalties = cls.get_late_penalties_for_team(team)
        return cls.extract_conclusions_for_configs(configs, last_tests, late_penalties, include_private_tests)

    @classmethod
    def get_late_penalties_for_team(cls, team: Team) -> Optional[Dict[int, float]]:
        if team is None:
            raise SubmissionServiceError('team is required')

        task = team.task
        if not task.late_penalty:
            return None
        late_penalty = LatePenalty(task.late_penalty)

        due_time = task.due_time
        if due_time is None:
            return None

        special = TaskService.get_special_consideration_for_team(team)
        if special and special.due_time_extension:
            due_time += timedelta(hours=special.due_time_extension)

        penalties = {}
        for submission in cls.get_for_team(team, include_cleared=False, submitted_after=due_time):
            penalty = late_penalty.compute_penalty(submission.created_at - due_time)
            if penalty:
                penalties[submission.id] = penalty
        return penalties

    @staticmethod
    def count_for_team(team: Team, include_cleared=False) -> int:
        if team is None:
            raise SubmissionServiceError('team is required')
        query = db.session.query(func.count()) \
            .filter(Submission.submitter_id == UserTeamAssociation.user_id,
                    UserTeamAssociation.team_id == team.id,
                    Submission.task_id == team.task_id)
        if not include_cleared:
            query = query.filter(Submission.is_cleared == False)
        return query.scalar()

    @staticmethod
    def get_file(_id: int) -> Optional[SubmissionFile]:
        if _id is None:
            raise SubmissionServiceError('id is required')
        if type(_id) is not int:
            raise SubmissionServiceError('id must be an integer')
        return SubmissionFile.query.get(_id)

    @staticmethod
    def get_files(requirement_id: int) -> List[Tuple[int, int, SubmissionFile]]:
        return db.session.query(Submission.id, Submission.submitter_id, SubmissionFile) \
            .filter(SubmissionFile.requirement_id == requirement_id,
                    Submission.id == SubmissionFile.submission_id) \
            .all()

    @staticmethod
    def get_team_files(requirement_id: int) -> List[Tuple[int, int, SubmissionFile]]:
        return db.session.query(Submission.id, Team.id, SubmissionFile) \
            .filter(SubmissionFile.requirement_id == requirement_id,
                    Submission.id == SubmissionFile.submission_id,
                    Submission.submitter_id == UserTeamAssociation.user_id,
                    UserTeamAssociation.team_id == Team.id,
                    Team.task_id == Submission.task_id) \
            .all()

    @staticmethod
    def add(task: Task, submitter: UserAlias, files: Dict[int, FileStorage], save_paths: Dict[int, str]) \
            -> Tuple[Submission, List[Submission], Optional[Team]]:
        # assume role has been checked (to minimize dependency)

        if task is None:
            raise SubmissionServiceError('task is required')
        if submitter is None:
            raise SubmissionServiceError('submitter is required')

        # time check
        now = datetime.utcnow()
        if not task.open_time or now < task.open_time:
            raise SubmissionServiceError('task has not yet open')
        if task.close_time and now > task.close_time:
            raise SubmissionServiceError('task has closed')

        if task.is_team_task:
            # team check
            from .team import TeamService
            ass = TeamService.get_team_association(task, submitter)
            if not ass:
                raise SubmissionServiceError('user is not in a team')
            team = ass.team
            if not team.is_finalised:
                raise SubmissionServiceError('team is not finalised')

            # get special considerations
            special = TaskService.get_special_consideration_for_team(team)

            # team submission attempt limit check
            attempt_limit = task.submission_attempt_limit
            if attempt_limit is not None:
                if special and special.submission_attempt_limit_extension:
                    attempt_limit += special.submission_attempt_limit_extension
                all_submissions = db.session.query(func.count()) \
                    .filter(UserTeamAssociation.user_id == Submission.submitter_id,
                            UserTeamAssociation.team_id == team.id,
                            Submission.task_id == task.id) \
                    .scalar()
                if all_submissions >= attempt_limit:
                    raise SubmissionServiceError('submission attempt limit exceeded')

            # team submission history limit check
            submissions_to_clear = []
            if task.submission_history_limit is not None:
                submissions_to_clear = Submission.query \
                    .filter(UserTeamAssociation.user_id == Submission.submitter_id,
                            UserTeamAssociation.team_id == team.id,
                            Submission.task_id == task.id) \
                    .filter_by(is_cleared=False) \
                    .order_by(desc(Submission.id)) \
                    .offset(task.submission_history_limit - 1).all()
        else:
            team = None

            # get special considerations
            special = TaskService.get_special_consideration_for_task_user(task, submitter)

            # user submission attempt limit check
            attempt_limit = task.submission_attempt_limit
            if attempt_limit is not None:
                if special and special.submission_attempt_limit_extension:
                    attempt_limit += special.submission_attempt_limit_extension
                all_submissions = db.session.query(func.count()) \
                    .filter(Submission.task_id == task.id,
                            Submission.submitter_id == submitter.id) \
                    .scalar()
                if all_submissions >= attempt_limit:
                    raise SubmissionServiceError('submission attempt limit exceeded')

            # user submission history limit check
            submissions_to_clear = []
            if task.submission_history_limit is not None:
                submissions_to_clear = Submission.query.with_parent(task).with_parent(submitter) \
                    .filter_by(is_cleared=False) \
                    .order_by(desc(Submission.id)) \
                    .offset(task.submission_history_limit - 1).all()

        # create submission object
        submission = Submission(task=task, submitter=submitter)

        # file check
        requirements = {r.id: r for r in task.file_requirements}
        for req_id, file in files.items():
            try:
                req = requirements.pop(req_id)  # pop matched requirement
            except KeyError:
                raise SubmissionServiceError('invalid requirement id', '%r' % req_id)

            # Notice: file sizes must be checked after the files are saved

            # extension check
            ext = os.path.splitext(req.name)[1]
            if ext and os.path.splitext(file.filename)[1] != ext:
                raise SubmissionServiceError('invalid file extension', file.filename)

            # append file object
            save_path = save_paths.get(req.id)
            if not save_path:
                raise SubmissionServiceError('save path is required', req.name)
            file = SubmissionFile(submission=submission, requirement=req, path=save_path)
            submission.files.append(file)

        # check remaining requirements
        for req in requirements.values():
            if not req.is_optional:
                raise SubmissionServiceError('unmet requirement', req.name)

        db.session.add(submission)
        return submission, submissions_to_clear, team

    @staticmethod
    def clear_submission(submission: Submission) -> List[str]:
        if submission is None:
            raise SubmissionServiceError('submission is required')
        if submission.is_cleared:
            raise SubmissionServiceError('submission is already cleared')

        file_paths = [f.path for f in submission.files]
        for file in submission.files:
            db.session.delete(file)
        submission.is_cleared = True
        return file_paths

    @staticmethod
    def run_auto_test(submission: Submission, config: AutoTestConfig) -> Tuple[AutoTest, AsyncResult]:
        if submission is None:
            raise SubmissionServiceError('submission is required')
        if config is None:
            raise SubmissionServiceError('auto test config is required')

        if submission.task.evaluation_method != 'auto_test':
            raise SubmissionServiceError('evaluation method is not auto testing')
        if not config.is_enabled:
            raise SubmissionServiceError('auto test config is disabled')

        # TODO how to use priority support in Celery properly?
        task_entry = bot.task_entries.get(config.type)
        if task_entry is None:
            raise SubmissionServiceError('task entry not found for config type: %s' % config.type)
        result = task_entry.apply_async((submission.id, config.id), countdown=3)  # wait 3 seconds to allow db commit
        test = AutoTestService.add(submission, config, result.id)
        return test, result

    @staticmethod
    def get_auto_tests(submission: Submission, joined_load_output_files=False, include_private: bool = False,
                       update_after_timestamp: float = None, timestamp_safe_margin: float = 3.0) \
            -> List[AutoTest]:
        if submission is None:
            raise SubmissionServiceError('submission is required')

        query = db.session.query(AutoTest)
        if joined_load_output_files:
            query = query.options(joinedload(AutoTest.output_files))

        filters = [AutoTest.submission_id == submission.id]
        if not include_private:
            filters.extend((
                AutoTest.config_id == AutoTestConfig.id,
                AutoTestConfig.is_private == False
            ))
        if update_after_timestamp:
            # Exclude tests that finished before the given timestamp (with a safe margin)
            timestamp = datetime.utcfromtimestamp(update_after_timestamp - timestamp_safe_margin)
            filters.append(or_(AutoTest.stopped_at.is_(None), AutoTest.stopped_at > timestamp))

        return query.filter(*filters).order_by(AutoTest.id).all()

    @staticmethod
    def get_last_auto_tests(submission: Submission, include_private: bool = False,
                            update_after_timestamp: float = None, timestamp_safe_margin: float = 3.0) \
            -> List[AutoTest]:
        if submission is None:
            raise SubmissionServiceError('submission is required')

        filters = [AutoTest.submission_id == submission.id]
        if not include_private:
            filters.extend((
                AutoTest.config_id == AutoTestConfig.id,
                AutoTestConfig.is_private == False
            ))

        if update_after_timestamp:
            # Exclude tests that finished before the given timestamp (with a safe margin)
            timestamp = datetime.utcfromtimestamp(update_after_timestamp - timestamp_safe_margin)
            filters.append(or_(AutoTest.stopped_at.is_(None), AutoTest.stopped_at > timestamp))

        sub_query = db.session.query(func.max(AutoTest.id).label('last_test_id')) \
            .filter(*filters) \
            .group_by(AutoTest.config_id).subquery()
        return db.session.query(AutoTest) \
            .filter(AutoTest.id == sub_query.c.last_test_id) \
            .order_by(AutoTest.config_id).all()

    @classmethod
    def extract_conclusions_for_configs(cls, configs: List[AutoTestConfig], last_tests: Dict[int, Dict[int, AutoTest]],
                                        late_penalties: Optional[Dict[int, float]],
                                        include_private_tests: bool = False):
        # re-structure dict
        test_results = defaultdict(list)
        for sid, tests in last_tests.items():
            for cid, test in tests.items():
                test_results[cid].append(test)

        ret = {}
        for config in configs:
            if not include_private_tests and config.is_private:
                continue
            tests = test_results.get(config.id)
            if not tests:  # no tests for this config
                ret[config.id] = None
                continue
            if config.results_conclusion_accumulate_method == 'first' \
                    and not last_tests[min(last_tests.keys())].get(config.id) \
                    or config.results_conclusion_accumulate_method == 'last' \
                    and not last_tests[max(last_tests.keys())].get(config.id):
                # If the REAL first/last submission has no AutoTest for this config but other submissions have, we must
                # return None.
                # We must explicitly handle this case here, otherwise the `extract_conclusion_for_config` method
                # will get the result from the last submission *that has an AutoTest*.
                ret[config.id] = None
                continue
            try:
                ret[config.id] = cls.extract_conclusion_for_config(config, tests, late_penalties)
            except AutoTestConclusionExtractionError as e:
                ret[config.id] = None
                logger.warning('%s: %s' % (e.msg, e.detail))
        return ret

    @classmethod
    def extract_conclusion_for_config(cls, config: AutoTestConfig, tests: List[AutoTest],
                                      submission_penalties: Dict[int, float] = None):
        if config is None:
            raise SubmissionServiceError('auto test config is required')
        if tests is None:
            raise SubmissionServiceError('auto test list is required')
        if not tests:
            return None

        conclusion_type = config.result_conclusion_type
        acc_method = config.results_conclusion_accumulate_method

        tests.sort(key=lambda t: t.submission_id)  # ensure the order

        if acc_method == 'first' or acc_method == 'last':
            # strictly use the test of the first or last submission in the given test list,
            # no matter whether the test is successful or not
            target_test = tests[0] if acc_method == 'first' else tests[-1]
            if target_test.final_state != 'SUCCESS':
                return None
            candidate_tests = [target_test]  # remove all the other candidates
        else:
            # like the NULL handling in database, we filter out non-successful tests before arithmetic aggregation
            candidate_tests = [t for t in tests if t.final_state == 'SUCCESS']
            if not candidate_tests:  # no successful test
                return None

        conclusions = [cls.extract_result_conclusion(t.result, config.result_conclusion_path) for t in candidate_tests]
        conclusions = cls.convert_result_conclusions_type(conclusions, conclusion_type)

        if config.result_conclusion_apply_late_penalty and submission_penalties and conclusion_type in {'int', 'float'}:
            penalties = [submission_penalties.get(t.submission_id) for t in candidate_tests]
            conclusions = [c if p is None or p == 0 else c * (1 - p) for c, p in zip(conclusions, penalties)]

        final_conclusion = cls.accumulate_result_conclusions(conclusions, acc_method)

        # normalize numerical final conclusion as we may have used penalty or average
        if conclusion_type == 'int':
            # TODO add options to use round/ceil/floor
            final_conclusion = round(final_conclusion)
        elif conclusion_type == 'float':
            # TODO add options to set the precision
            final_conclusion = round(final_conclusion * 100) / 100
        return final_conclusion

    @staticmethod
    def convert_result_conclusions_type(conclusions: list, _type) -> list:
        try:
            if _type == 'int':
                return [int(c) for c in conclusions]
            if _type == 'float':
                return [float(c) for c in conclusions]
            if _type == 'bool':
                return [bool(c) for c in conclusions]
            if _type == 'string':
                return [str(c) for c in conclusions]
            if _type == 'json':
                return conclusions
            raise SubmissionServiceError('unknown conclusion type: %s' % _type)
        except (TypeError, ValueError) as e:
            raise AutoTestConclusionExtractionError('failed to convert conclusions to type %s'
                                                    % _type, str(e))

    @staticmethod
    def accumulate_result_conclusions(conclusions: list, accumulate_method: str):
        try:
            if accumulate_method == 'last':
                return conclusions[-1]
            if accumulate_method == 'first':
                return conclusions[0]
            if accumulate_method == 'highest':
                return max(conclusions)
            if accumulate_method == 'lowest':
                return min(conclusions)
            if accumulate_method == 'average':
                return sum(conclusions) / len(conclusions)
            if accumulate_method == 'and':
                return all(conclusions)
            if accumulate_method == 'or':
                return any(conclusions)
        except TypeError as e:
            raise AutoTestConclusionExtractionError('failed to accumulate conclusions with method: %s'
                                                    % accumulate_method, str(e))
        raise SubmissionServiceError('unknown conclusion accumulate method: %s' % accumulate_method)

    @staticmethod
    def extract_result_conclusion(result: Optional[str], conclusion_path: Optional[str]):
        if not result:
            ret = None
        else:
            try:
                ret = json.loads(result)
            except (ValueError, TypeError) as e:
                raise AutoTestConclusionExtractionError('result is not a valid JSON object', str(e))
        if conclusion_path:
            for segment in conclusion_path.split('.'):
                if not segment:
                    raise SubmissionServiceError('invalid result path', 'empty segment found')
                if type(ret) is not dict:
                    raise AutoTestConclusionExtractionError('failed to evaluate path on result',
                                                            'tried to get value of key "%s" on non-dict object'
                                                            % segment)
                try:
                    ret = ret[segment]
                except KeyError as e:
                    raise AutoTestConclusionExtractionError('failed to evaluate path on result', str(e))
        return ret

    @classmethod
    def get_auto_test_conclusions_for_task(cls, task: Task, include_private_tests=False) \
            -> Dict[int, Dict[int, object]]:
        if task is None:
            raise SubmissionServiceError('task is required')

        configs = task.auto_test_configs
        if not configs:
            return {}

        all_last_tests = cls.get_last_auto_tests_for_task(task, include_cleared=False,
                                                          include_private_tests=include_private_tests)

        all_late_penalties = cls.get_late_penalties_for_task(task)

        all_ret = {}
        for unit_id, last_tests in all_last_tests.items():
            # unit_id is submitter_id for user-task, or team_id for team-task
            late_penalties = all_late_penalties.get(unit_id) if all_late_penalties else None
            all_ret[unit_id] = cls.extract_conclusions_for_configs(configs, last_tests, late_penalties,
                                                                   include_private_tests)
        return all_ret

    @staticmethod
    def get_for_task(task: Task, include_cleared=False, submitted_after: datetime = None) \
            -> Dict[int, List[Submission]]:
        if task is None:
            raise SubmissionServiceError('task is required')

        filters = [
            Submission.task_id == task.id
        ]
        if not include_cleared:
            filters.append(Submission.is_cleared == False)
        if submitted_after is not None:
            filters.append(Submission.created_at > submitted_after)

        if task.is_team_task:
            filters.extend([
                Submission.submitter_id == UserTeamAssociation.user_id,
                UserTeamAssociation.team_id == Team.id,
                Team.task_id == task.id
            ])
            results = db.session.query(Team.id, Submission) \
                .filter(*filters) \
                .order_by(Submission.id)
        else:
            results = ((s.submitter_id, s) for s in db.session.query(Submission)
                .filter(*filters)
                .order_by(Submission.id))

        ret = {}
        for unit_id, submission in results:  # unit_id is submitter_id for user-task, or team_id for team-task
            ret_unit = ret.get(unit_id)
            if ret_unit is None:
                ret[unit_id] = ret_unit = []
            ret_unit.append(submission)
        return ret

    @classmethod
    def get_late_penalties_for_task(cls, task: Task) -> Optional[Dict[int, Dict[int, float]]]:
        if task is None:
            raise SubmissionServiceError('task is required')

        if not task.late_penalty:
            return None
        late_penalty = LatePenalty(task.late_penalty)

        due_time = task.due_time
        if due_time is None:
            return None

        all_specials = TaskService.get_special_considerations_for_task(task)
        if task.is_team_task:
            due_time_extensions = {special.team_id: special.due_time_extension
                                   for special in all_specials
                                   if special.due_time_extension is not None}
        else:
            due_time_extensions = {special.user_id: special.due_time_extension
                                   for special in all_specials
                                   if special.due_time_extension is not None}

        all_penalties = {}
        for unit_id, submissions in cls.get_for_task(task, include_cleared=False, submitted_after=due_time).items():
            unit_due_time = due_time
            extension = due_time_extensions.get(unit_id)
            if extension:
                unit_due_time += timedelta(hours=extension)

            penalties = {}
            for submission in submissions:
                penalty = late_penalty.compute_penalty(submission.created_at - unit_due_time)
                if penalty:
                    penalties[submission.id] = penalty
            if penalties:
                all_penalties[unit_id] = penalties

        return all_penalties

    @classmethod
    def get_last_auto_tests_for_task(cls, task: Task, include_cleared=False, include_private_tests=False) \
            -> Dict[int, Dict[int, AutoTest]]:
        if task is None:
            raise SubmissionServiceError('task is required')

        filters = [
            Submission.task_id == task.id
        ]
        if not include_cleared:
            filters.append(Submission.is_cleared == False)

        public_config_ids = None
        if not include_private_tests:  # have to run another query to get public config ids
            id_results = db.session.query(AutoTestConfig.id) \
                .filter(AutoTestConfig.is_private == False, AutoTestConfig.task_id == task.id)
            public_config_ids = set(r[0] for r in id_results)

        sub_query = db.session.query(Submission.id.label('submission_id'),
                                     func.max(AutoTest.id).label('last_test_id')) \
            .outerjoin(AutoTest, AutoTest.submission_id == Submission.id) \
            .filter(*filters) \
            .group_by(Submission.id, AutoTest.config_id).subquery()

        if task.is_team_task:
            sub_sub_query = db.session.query(Team.id.label('team_id'),
                                             sub_query.c.submission_id.label('submission_id'),
                                             sub_query.c.last_test_id.label('last_test_id')) \
                .filter(Submission.id == sub_query.c.submission_id,
                        Submission.submitter_id == UserTeamAssociation.user_id,
                        UserTeamAssociation.team_id == Team.id,
                        Team.task_id == task.id).subquery()
            results = db.session.query(sub_sub_query.c.team_id, sub_sub_query.c.submission_id, AutoTest) \
                .outerjoin(AutoTest, AutoTest.id == sub_sub_query.c.last_test_id)
        else:
            results = db.session.query(Submission.submitter_id, Submission.id, AutoTest) \
                .join(sub_query, Submission.id == sub_query.c.submission_id) \
                .outerjoin(AutoTest, AutoTest.id == sub_query.c.last_test_id)

        all_last_tests = {}
        for unit_id, submission_id, test in results:  # unit_id is submitter_id for user-task, or team_id for team-task
            last_tests = all_last_tests.get(unit_id)
            if last_tests is None:
                all_last_tests[unit_id] = last_tests = {}
            tests = last_tests.get(submission_id)
            if tests is None:
                last_tests[submission_id] = tests = {}  # make sure all submission_ids are in last_tests even if no test
            if test is None:
                continue  # no test for this submission (we are using outer-join)
            if not include_private_tests and test.config_id not in public_config_ids:
                continue  # skip private tests
            tests[test.config_id] = test
        return all_last_tests

    @staticmethod
    def get_previous_file_for_submitter(file: SubmissionFile) -> Optional[SubmissionFile]:
        if file is None:
            raise SubmissionServiceError('file is required')

        submission = file.submission
        # Find the previous file submitted by the same user. Be careful, a file may be optional.
        return db.session.query(SubmissionFile) \
            .filter(SubmissionFile.requirement_id == file.requirement_id,
                    SubmissionFile.submission_id == Submission.id,
                    Submission.task_id == submission.task_id,
                    Submission.submitter_id == submission.submitter_id,
                    Submission.id < submission.id) \
            .order_by(Submission.id.desc()) \
            .first()

    @staticmethod
    def get_previous_file_for_team(file: SubmissionFile) -> Optional[SubmissionFile]:
        if file is None:
            raise SubmissionServiceError('file is required')

        submission = file.submission
        task = submission.task

        from .team import TeamService
        ass = TeamService.get_team_association(task, submission.submitter)
        if ass is None:
            raise SubmissionServiceError('submitter not in a team')

        # Find the previous file submitted by the same team. Be careful, a file may be optional.
        return db.session.query(SubmissionFile) \
            .filter(SubmissionFile.requirement_id == file.requirement_id,
                    SubmissionFile.submission_id == Submission.id,
                    Submission.task_id == submission.task_id,
                    Submission.submitter_id == UserTeamAssociation.user_id,
                    UserTeamAssociation.team_id == ass.team_id,
                    Submission.id < submission.id) \
            .order_by(Submission.id.desc()) \
            .first()

    @staticmethod
    def get_comment(_id: int) -> Optional[SubmissionComment]:
        if _id is None:
            raise SubmissionServiceError('id is required')
        if type(_id) is not int:
            raise SubmissionServiceError('id must be an integer')
        return SubmissionComment.query.get(_id)

    @staticmethod
    def get_comments(submission: Submission) -> List[SubmissionComment]:
        if submission is None:
            raise SubmissionServiceError('submission is required')

        return SubmissionComment.query.with_parent(submission).all()

    @classmethod
    def add_comment(cls, submission: Submission, author: Optional[UserAlias], content: str) -> SubmissionComment:
        if submission is None:
            raise SubmissionServiceError('submission is required')
        if content is None:
            raise SubmissionServiceError('content is required')

        if not content:
            raise SubmissionServiceError('content must not be empty')
        if len(content) > cls._COMMENT_MAX_LENGTH:
            raise SubmissionServiceError('content too long')

        comment = SubmissionComment(submission=submission, author=author, content=content)
        db.session.add(comment)
        return comment

    @classmethod
    def update_comment(cls, comment: SubmissionComment, content: str):
        if comment is None:
            raise SubmissionServiceError('comment is required')
        if content is None:
            raise SubmissionServiceError('content is required')

        if not content:
            raise SubmissionServiceError('content must not be empty')
        if len(content) > cls._COMMENT_MAX_LENGTH:
            raise SubmissionServiceError('content too long')

        comment.content = content

    @staticmethod
    def get_last_comment(submission: Submission) -> Optional[SubmissionComment]:
        if submission is None:
            raise SubmissionServiceError('submission is required')

        return SubmissionComment.query.with_parent(submission).order_by(SubmissionComment.id.desc()).first()

    @staticmethod
    def get_comment_summaries(task: Task) -> List[SubmissionCommentSummary]:
        if task is None:
            raise SubmissionServiceError('task is required')

        sub_query = db.session.query(Submission.id.label('sid'), func.count().label('total'),
                                     func.max(SubmissionComment.id).label('last_cid')) \
            .filter(Submission.task_id == task.id,
                    SubmissionComment.submission_id == Submission.id) \
            .group_by(Submission) \
            .subquery()

        results = []
        for submission, total, last_comment in db.session.query(Submission, sub_query.c.total,
                                                               SubmissionComment) \
                .filter(Submission.id == sub_query.c.sid, SubmissionComment.id == sub_query.c.last_cid) \
                .order_by(SubmissionComment.modified_at).all():
            results.append(SubmissionCommentSummary(submission, total, last_comment))
        return results
