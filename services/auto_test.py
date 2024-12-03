from collections import defaultdict
from typing import Optional

from celery.result import AsyncResult
from sqlalchemy import func

from error import BasicError
from models import AutoTest, Submission, AutoTestOutputFile, db, AutoTestConfig, EXCEPTION_MESSAGE_SAFE_LENGTH
from testbot import bot


class AutoTestServiceError(BasicError):
    pass


class AutoTestService:
    _summary_head_limit = 10

    @staticmethod
    def get(_id: int) -> Optional[AutoTest]:
        if _id is None:
            raise AutoTestServiceError('id is required')
        if type(_id) is not int:
            raise AutoTestServiceError('id must be an integer')

        return AutoTest.query.get(_id)

    @staticmethod
    def get_by_submission_work_id(submission_id: int, work_id: str) -> Optional[AutoTest]:
        if submission_id is None:
            raise AutoTestServiceError('submission id is required')
        if work_id is None:
            raise AutoTestServiceError('work task id is required')

        return AutoTest.query.filter_by(submission_id=submission_id, work_id=work_id).first()

    @staticmethod
    def add(submission: Submission, config: AutoTestConfig, work_id: str) -> AutoTest:
        test = AutoTest(submission=submission, config=config, work_id=work_id)
        db.session.add(test)
        return test

    @staticmethod
    def add_output_file(test: AutoTest, path: str, save_path: str) -> AutoTestOutputFile:
        if db.session.query(func.count()). \
                filter(AutoTestOutputFile.auto_test_id == test.id,
                       AutoTestOutputFile.path == path).scalar():
            raise AutoTestServiceError('file already exists')
        return AutoTestOutputFile(auto_test=test, path=path, save_path=save_path)

    @staticmethod
    def get_output_file(file_id: int) -> Optional[AutoTestOutputFile]:
        return AutoTestOutputFile.query.get(file_id)

    @staticmethod
    def get_result(test: AutoTest) -> AsyncResult:
        if test is None:
            raise AutoTestServiceError('auto_test is required')

        config_type = test.config.type
        task_entry = bot.task_entries.get(config_type)
        if task_entry is None:
            raise AutoTestServiceError('task entry not found for config type: %s', config_type)
        return task_entry.AsyncResult(test.work_id)

    @staticmethod
    def result_to_dict(result: AsyncResult, with_advanced_fields=False) -> dict:
        d = dict(state=result.state)
        if with_advanced_fields:
            d['work_id'] = result.id
        if result.result is not None:
            if result.state == 'SUCCESS':
                d['result'] = result.result
            elif result.state == 'FAILURE':
                exception = result.result
                d['exception_class'] = type(exception).__name__
                # limit the length of message to avoid 'Exception Attack'
                exception_message = str(exception)
                if not with_advanced_fields and len(exception_message) > EXCEPTION_MESSAGE_SAFE_LENGTH:
                    exception_message = exception_message[0: EXCEPTION_MESSAGE_SAFE_LENGTH] + '...'
                d['exception_message'] = exception_message
                if with_advanced_fields:
                    d['exception_traceback'] = result.traceback
            elif result.state == 'STARTED':
                worker_info = result.result
                d['hostname'] = worker_info.get('hostname')
                if with_advanced_fields:
                    d['pid'] = worker_info.get('pid')
        return d

    @classmethod
    def test_to_dict(cls, test: AutoTest, with_advanced_fields=False, with_pending_tests_ahead=True) -> dict:
        """
        Get a dumped dictionary with additional information from the temporary result
        """
        test_obj = test.to_dict(with_advanced_fields=with_advanced_fields)
        if not test.final_state:  # pending/running tests
            result = cls.get_result(test)
            result_obj = cls.result_to_dict(result, with_advanced_fields=with_advanced_fields)
            test_obj.update(result_obj)  # merge temporary result
            if result.state == 'PENDING' and with_pending_tests_ahead:
                test_obj['pending_tests_ahead'] = cls.get_pending_tests_ahead(test)
        return test_obj

    @classmethod
    def get_pending_tests_ahead(cls, test: AutoTest) -> int:
        if test is None:
            raise AutoTestServiceError('auto_test is required')

        # assume all tests with the same config type go into the same task queue (although in fact not necessarily)
        config = test.config
        return db.session.query(func.count()) \
            .filter(AutoTest.started_at.is_(None),
                    AutoTestConfig.id == AutoTest.config_id,
                    AutoTestConfig.type == config.type,
                    AutoTest.id < test.id).scalar()

    @classmethod
    def get_summaries(cls, with_advanced_fields=False) -> dict:
        from .team import TeamService, TeamServiceError
        # counts
        counts = defaultdict(dict)
        for _type, state, count in db.session.query(AutoTestConfig.type, AutoTest.final_state, func.count()) \
                .filter(AutoTest.config_id == AutoTestConfig.id) \
                .group_by(AutoTestConfig.type, AutoTest.final_state):
            if not state:
                state = 'active'
            counts[_type][state.lower()] = count
        for _type, type_counts in counts.items():
            type_counts['total'] = sum(type_counts.values())
            for state in ['active', 'success', 'failure']:
                type_counts[state] = type_counts.get(state, 0)

        # head of queues
        heads = {}
        for _type, start_id in db.session.query(AutoTestConfig.type, func.min(AutoTest.id)) \
                .filter(AutoTest.config_id == AutoTestConfig.id,
                        AutoTest.final_state == None) \
                .group_by(AutoTestConfig.type):

            type_heads = []
            for t in db.session.query(AutoTest) \
                    .filter(AutoTest.id >= start_id,
                            AutoTest.config_id == AutoTestConfig.id,
                            AutoTest.final_state == None,
                            AutoTestConfig.type == _type) \
                    .order_by(AutoTest.id) \
                    .limit(cls._summary_head_limit):
                d = cls.test_to_dict(t, with_advanced_fields=with_advanced_fields, with_pending_tests_ahead=False)
                task = t.submission.task
                submitter = t.submission.submitter
                if task.is_team_task:
                    try:
                        ass = TeamService.get_team_association(task, submitter)
                    except TeamServiceError as e:
                        raise AutoTestServiceError('failed to get team association', e.msg)
                    if not ass:
                        raise AutoTestServiceError('no team association found')
                    d['_link'] = '/terms/%d/tasks/%d/team-submissions/%d/%d' % (task.term_id, task.id, ass.team_id,
                                                                                t.submission_id)
                else:
                    d['_link'] = '/terms/%d/tasks/%d/user-submissions/%d/%d' % (task.term_id, task.id, submitter.id,
                                                                                t.submission_id)
                type_heads.append(d)
            heads[_type] = type_heads

        return dict({_type: dict(counts=counts[_type], heads=heads.get(_type)) for _type in counts})


    @classmethod
    def remove_pending_tests_for_config(cls, config: AutoTestConfig) -> int:
        incomplete_tests = db.session.query(AutoTest).filter(
            AutoTest.config_id == config.id,
            AutoTest.final_state.is_(None)
        ).all()
        removed = 0
        for test in incomplete_tests:
            result = cls.get_result(test)
            if result.state == 'PENDING':
                result.forget()
                db.session.delete(test)  # should be no files or file objs associated
                db.session.commit()  # instantly commit to avoid any inconsistency
                removed += 1
        return removed
