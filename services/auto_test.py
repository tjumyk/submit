from typing import Optional

from celery.result import AsyncResult
from sqlalchemy import func

import celery_app
from error import BasicError
from models import AutoTest, Submission, AutoTestOutputFile, db


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
    def add(submission: Submission, work_id: str) -> AutoTest:
        return AutoTest(submission=submission, work_id=work_id)

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
        return celery_app.run_test.AsyncResult(test.work_id)

    @staticmethod
    def result_to_dict(result: AsyncResult, with_advanced_fields=False) -> dict:
        d = dict(state=result.state)
        if with_advanced_fields:
            d['work_id'] = result.id
        if result.result:
            if isinstance(result.result, BaseException):
                exception = result.result
                d['exception_class'] = type(exception).__name__
                d['exception_message'] = str(exception)
                if with_advanced_fields:
                    d['exception_traceback'] = result.traceback
            else:
                d['result'] = result.result
        return d
