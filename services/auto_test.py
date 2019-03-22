from typing import Optional

from celery.result import AsyncResult
from sqlalchemy import func

from error import BasicError
from models import AutoTest, Submission, AutoTestOutputFile, db, AutoTestConfig, EXCEPTION_MESSAGE_SAFE_LENGTH
from testbot import bot


class AutoTestServiceError(BasicError):
    pass


class AutoTestService:
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
        return bot.run_test.AsyncResult(test.work_id)

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
    def test_to_dict(cls, test: AutoTest, with_advanced_fields=False) ->dict:
        """
        Get a dumped dictionary with additional information from the temporary result
        """
        test_obj = test.to_dict(with_advanced_fields=with_advanced_fields)
        if not test.final_state:  # running tests
            result_obj = cls.result_to_dict(cls.get_result(test), with_advanced_fields=with_advanced_fields)
            test_obj.update(result_obj)  # merge temporary result
        return test_obj
