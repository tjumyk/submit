import json
import math
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

from celery.result import AsyncResult
from sqlalchemy import desc, func
from werkzeug.datastructures import FileStorage

from error import BasicError
from models import Submission, Task, UserAlias, Team, SubmissionFile, db, UserTeamAssociation, AutoTest, AutoTestConfig
from services.auto_test import AutoTestService
from services.task import TaskService
from testbot import bot


class SubmissionServiceError(BasicError):
    pass


class UserSubmissionSummary:
    def __init__(self, user: UserAlias, total_submissions: int, last_submit_time: datetime):
        self.user = user
        self.total_submissions = total_submissions
        self.last_submit_time = last_submit_time

    def to_dict(self):
        d = dict(user=self.user.to_dict(),
                 total_submissions=self.total_submissions,
                 last_submit_time=self.last_submit_time)
        return d


class TeamSubmissionSummary:
    def __init__(self, team: Team, total_submissions: int, last_submit_time: datetime):
        self.team = team
        self.total_submissions = total_submissions
        self.last_submit_time = last_submit_time

    def to_dict(self):
        d = dict(team=self.team.to_dict(),
                 total_submissions=self.total_submissions,
                 last_submit_time=self.last_submit_time)
        return d


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

    @staticmethod
    def _parse(repr_string: str):
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
                cut = round((1.0 - total) * 10000) / 10000  # remove long tails due to precision loss
                if cut > 0:
                    total += cut
                    cuts.append(cut)
                break
            total += cut
            cuts.append(cut)
            if index < num_raw_cuts - 1:  # otherwise keep using the last cut
                index += 1

        return cuts

    def __repr__(self):
        return '<LatePenalty %s>' % ' '.join(str(c) for c in self._cuts)

    def compute_penalty(self, late: timedelta):
        if not self._cuts:  # no late penalty
            return 0
        seconds = late.total_seconds()
        if seconds <= 0:
            return 0
        days = math.ceil(seconds / (3600 * 24))
        return sum(self._cuts[0:days])


class SubmissionService:
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
                                     func.max(Submission.created_at).label('last_submit_time')) \
            .filter(UserAlias.id == Submission.submitter_id,
                    Submission.task_id == task.id) \
            .group_by(UserAlias.id).subquery()
        query = db.session.query(UserAlias,
                                 sub_query.c.total_submissions,
                                 sub_query.c.last_submit_time) \
            .filter(sub_query.c.user_id == UserAlias.id) \
            .order_by(sub_query.c.last_submit_time)
        return [UserSubmissionSummary(user, total, last_time) for user, total, last_time in query.all()]

    @staticmethod
    def get_team_summaries(task: Task) -> List[TeamSubmissionSummary]:
        if task is None:
            raise SubmissionServiceError('task is required')
        if not task.is_team_task:
            raise SubmissionServiceError('task is not team task')

        sub_query = db.session.query(Team.id.label('team_id'),
                                     func.count().label('total_submissions'),
                                     func.max(Submission.created_at).label('last_submit_time')) \
            .filter(Team.id == UserTeamAssociation.team_id,
                    Team.task_id == task.id,
                    Submission.submitter_id == UserTeamAssociation.user_id,
                    Submission.task_id == task.id) \
            .group_by(Team.id).subquery()
        query = db.session.query(Team,
                                 sub_query.c.total_submissions,
                                 sub_query.c.last_submit_time) \
            .filter(sub_query.c.team_id == Team.id) \
            .order_by(sub_query.c.last_submit_time)
        return [TeamSubmissionSummary(team, total, last_submit) for team, total, last_submit in query.all()]

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
        late_penalty = LatePenalty(task.late_penalty)
        configs = task.auto_test_configs
        if not configs:
            return {}

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

        submission_late_penalties = {}
        due_time = task.due_time
        if due_time is not None:
            special = TaskService.get_special_consideration_for_task_user(task, user)
            if special is not None and special.due_time_extension:
                due_time += timedelta(hours=special.due_time_extension)

            # compute penalties if any
            for submission in cls.get_for_task_and_user(task, user, include_cleared=False, submitted_after=due_time):
                penalty = late_penalty.compute_penalty(submission.created_at - due_time)
                if penalty:
                    submission_late_penalties[submission.id] = penalty

        # re-structure dict
        test_results = defaultdict(list)
        for sid, tests in last_tests.items():
            for cid, test in tests.items():
                test_results[cid].append(test)

        ret = {}
        for config in configs:
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
                # We must explicitly handle this case here, otherwise the `extract_conclusion_from_auto_tests` method
                # will get the result from the last submission *that has an AutoTest*.
                ret[config.id] = None
                continue
            ret[config.id] = cls.extract_conclusion_from_auto_tests(config, tests, submission_late_penalties)
        return ret

    @classmethod
    def get_auto_test_conclusions_for_user_task(cls, task: Task, include_private_tests=False):
        for summary in cls.get_user_summaries(task):
            try:
                conclusion = cls.get_auto_test_conclusions_for_task_and_user(task, summary.user,
                                                                             include_private_tests=
                                                                             include_private_tests)
            except Exception as e:
                conclusion = e
            yield (summary.user, conclusion)

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
        task = team.task
        late_penalty = LatePenalty(task.late_penalty)
        configs = task.auto_test_configs
        if not configs:
            return {}

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

        submission_late_penalties = {}
        due_time = task.due_time
        if due_time is not None:
            special = TaskService.get_special_consideration_for_team(team)
            if special and special.due_time_extension:
                due_time += timedelta(hours=special.due_time_extension)

            # compute penalties if any
            for submission in cls.get_for_team(team, include_cleared=False, submitted_after=due_time):
                penalty = late_penalty.compute_penalty(submission.created_at - due_time)
                if penalty:
                    submission_late_penalties[submission.id] = penalty

        # re-structure dict
        test_results = defaultdict(list)
        for sid, tests in last_tests.items():
            for cid, test in tests.items():
                test_results[cid].append(test)

        ret = {}
        for config in configs:
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
                # We must explicitly handle this case here, otherwise the `extract_conclusion_from_auto_tests` method
                # will get the result from the last submission *that has an AutoTest*.
                ret[config.id] = None
                continue
            ret[config.id] = cls.extract_conclusion_from_auto_tests(config, tests, submission_late_penalties)
        return ret

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
    def add(task: Task, submitter: UserAlias, files: Dict[int, FileStorage], save_paths: Dict[int, str]) \
            -> Tuple[Submission, List[Submission]]:
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
        return submission, submissions_to_clear

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
        result = bot.run_test.apply_async((submission.id, config.id), countdown=3)  # wait 3 seconds to allow db commit
        test = AutoTestService.add(submission, config, result.id)
        return test, result

    @staticmethod
    def get_last_auto_tests(submission: Submission) -> List[Tuple[AutoTestConfig, AutoTest]]:
        if submission is None:
            raise SubmissionServiceError('submission is required')

        sub_query = db.session.query(func.max(AutoTest.id).label('last_test_id')) \
            .filter(AutoTest.submission_id == submission.id) \
            .group_by(AutoTest.config_id).subquery()
        return db.session.query(AutoTestConfig, AutoTest) \
            .filter(AutoTestConfig.id == AutoTest.config_id,
                    AutoTest.id == sub_query.c.last_test_id) \
            .order_by(AutoTest.config_id).all()

    @classmethod
    def extract_conclusion_from_auto_tests(cls, config: AutoTestConfig, tests: List[AutoTest],
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

        if submission_penalties and conclusion_type in {'int', 'float'}:
            # TODO add an option to use late_penalty or not for this AutoTestConfig
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
    def convert_result_conclusions_type(conclusions, _type):
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
            raise SubmissionServiceError('failed to convert conclusions to type %s'
                                         % _type, str(e))

    @staticmethod
    def accumulate_result_conclusions(conclusions, accumulate_method):
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
            raise SubmissionServiceError('failed to accumulate conclusions with method: %s' % accumulate_method, str(e))
        raise SubmissionServiceError('unknown conclusion accumulate method: %s' % accumulate_method)

    @staticmethod
    def extract_result_conclusion(result: Optional[str], conclusion_path: Optional[str]):
        if not result:
            ret = None
        else:
            try:
                ret = json.loads(result)
            except (ValueError, TypeError) as e:
                raise SubmissionServiceError('result is not a valid JSON object', str(e))
        if conclusion_path:
            for segment in conclusion_path.split('.'):
                if not segment:
                    raise SubmissionServiceError('invalid result path', 'empty segment found')
                if type(ret) is not dict:
                    raise SubmissionServiceError('failed to evaluate path on result',
                                                 'tried to get value of key "%s" on non-dict object' % segment)
                try:
                    ret = ret[segment]
                except KeyError as e:
                    raise SubmissionServiceError('failed to evaluate path on result', str(e))
        return ret
