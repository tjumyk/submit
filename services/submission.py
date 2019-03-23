import json
import os
from collections import defaultdict
from datetime import datetime
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
    def get_for_task_and_user(task: Task, user: UserAlias, include_cleared=False) -> List[Submission]:
        if task is None:
            raise SubmissionServiceError('task is required')
        if user is None:
            raise SubmissionServiceError('user is required')
        query = Submission.query.with_parent(task).with_parent(user)
        if not include_cleared:
            query = query.filter_by(is_cleared=False)
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
            if test is None:
                continue  # no test for this submission (we are using outer-join)
            if not include_private_tests and test.config_id not in public_config_ids:
                continue  # skip private tests
            tests = last_tests.get(submission_id)
            if tests is None:
                last_tests[submission_id] = tests = {}
            tests[test.config_id] = test
        return last_tests

    @classmethod
    def get_auto_test_conclusions_for_task_and_user(cls, task: Task, user: UserAlias, include_private_tests=False) \
            -> Dict[int, object]:
        configs = task.auto_test_configs

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
        # re-structure dict
        test_results = defaultdict(list)
        for sid, tests in last_tests.items():
            for cid, test in tests.items():
                test_results[cid].append(test)

        ret = {}
        for config in configs:
            tests = test_results.get(config.id)
            if not tests:
                continue  # no tests
            conclusion = cls.extract_auto_test_conclusion(config, tests)
            ret[config.id] = conclusion
        return ret

    @classmethod
    def extract_auto_test_conclusion(cls, config: AutoTestConfig, tests: List[AutoTest]):
        if not config:
            raise SubmissionServiceError('auto test config is required')
        if not tests:
            raise SubmissionServiceError('at least one auto test is required')

        results = [cls.evaluate_object_path(t.result, config.result_conclusion_path) for t in tests]

        conclusion_type = config.result_conclusion_type
        try:
            # type conversion
            if conclusion_type == 'int':
                results = [int(r) for r in results]
            elif conclusion_type == 'float':
                results = [float(r) for r in results]
            elif conclusion_type == 'bool':
                results = [bool(r) for r in results]
            elif conclusion_type == 'string':
                results = [str(r) for r in results]
        except ValueError as e:
            raise SubmissionServiceError('failed to convert conclusion to type %s'
                                         % conclusion_type, str(e))

        acc_method = config.results_conclusion_accumulate_method
        if acc_method == 'last':
            return results[-1]
        if acc_method == 'first':
            return results[0]
        if acc_method == 'highest':
            return max(results)
        if acc_method == 'lowest':
            return min(results)
        if acc_method == 'average':
            return sum(results) / len(results)
        if acc_method == 'and':
            return all(results)
        if acc_method == 'or':
            return any(results)
        raise SubmissionServiceError('unknown result conclusion accumulate method: %s' % acc_method)

    @staticmethod
    def evaluate_object_path(obj: str, path: str):
        try:
            ret = json.loads(obj)
        except ValueError as e:
            raise SubmissionServiceError('result is not a valid JSON object', str(e))
        if path:
            for segment in path.split('.'):
                if not segment:
                    raise SubmissionServiceError('invalid result path', 'empty segment found')
                if type(ret) is not dict:
                    raise SubmissionServiceError('failed to evaluate path on result',
                                                 'tried to get value of key "%s" on non-dict object' % segment)
                ret = ret[segment]
        return ret

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
    def get_for_team(team: Team, include_cleared=False) -> List[Submission]:
        if team is None:
            raise SubmissionServiceError('team is required')
        query = Submission.query.filter(Submission.submitter_id == UserTeamAssociation.user_id,
                                        UserTeamAssociation.team_id == team.id,
                                        Submission.task_id == team.task_id)
        if not include_cleared:
            query = query.filter_by(is_cleared=False)
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
            if test is None:
                continue  # no test for this submission (we are using outer-join)
            if not include_private_tests and test.config_id not in public_config_ids:
                continue  # skip private tests
            tests = last_tests.get(submission_id)
            if tests is None:
                last_tests[submission_id] = tests = {}
            tests[test.config_id] = test
        return last_tests

    @classmethod
    def get_auto_test_conclusions_for_team(cls, team: Team, include_private_tests=False) \
            -> Dict[int, object]:
        configs = team.task.auto_test_configs

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
        # re-structure dict
        test_results = defaultdict(list)
        for sid, tests in last_tests.items():
            for cid, test in tests.items():
                test_results[cid].append(test)

        ret = {}
        for config in configs:
            tests = test_results.get(config.id)
            if not tests:
                continue  # no tests
            conclusion = cls.extract_auto_test_conclusion(config, tests)
            ret[config.id] = conclusion
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
