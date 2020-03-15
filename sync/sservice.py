import os
from base64 import b64encode, b64decode
from datetime import datetime
from typing import List, Tuple, Iterable

from flask import current_app as app
from sqlalchemy.orm import joinedload

from error import BasicError
from models import Task, db, Submission, AutoTest, SubmissionFile, AutoTestOutputFile
from services.account import AccountService
from sync.smodel import SubmissionData, SubmissionFileData, AutoTestOutputFileData, AutoTestData

_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'


class SyncServiceError(BasicError):
    pass


class SyncService:
    @staticmethod
    def _get_submissions(task: Task, after_id: int) -> List[Submission]:
        return db.session.query(Submission) \
            .options(joinedload(Submission.submitter)) \
            .filter(Submission.task_id == task.id,
                    Submission.id > after_id) \
            .order_by(Submission.id).all()

    @classmethod
    def list_submissions(cls, task: Task, after_id: int) -> List[Tuple[int, str, str]]:
        return [(s.id, s.submitter.name, str(s.created_at)) for s in cls._get_submissions(task, after_id)]

    @classmethod
    def diff_submissions(cls, task: Task, compare_list: Iterable[Tuple[int, str, str]]) -> List[int]:
        mapping = {(item[1], item[2]): item[0] for item in compare_list}
        for sub in cls._get_submissions(task, 0):
            key = (sub.submitter.name, str(sub.created_at))
            mapping.pop(key, None)
        return list(mapping.values())

    @staticmethod
    def prepare_submissions(id_list: List[int]) -> List[SubmissionData]:
        data_folder = app.config['DATA_FOLDER']
        data = []
        for sub in db.session.query(Submission) \
                .options(joinedload(Submission.submitter),
                         joinedload(Submission.files)) \
                .filter(Submission.id.in_(id_list)) \
                .order_by(Submission.id):

            files_data = []
            for f in sorted(sub.files, key=lambda x: x.id):
                with open(os.path.join(data_folder, f.path), 'rb') as fi:
                    content = b64encode(fi.read()).decode()
                sub_path = f.path.split('/', 4)[-1]
                files_data.append(SubmissionFileData(f.requirement.name, sub_path, content,
                                                     f.size, f.md5, str(f.created_at), str(f.modified_at)))

            tests_data = []
            for test in db.session.query(AutoTest) \
                    .options(joinedload(AutoTest.output_files)) \
                    .filter(AutoTest.submission_id == sub.id) \
                    .order_by(AutoTest.id):

                output_files_data = []
                for _f in sorted(test.output_files, key=lambda x: x.id):
                    with open(os.path.join(data_folder, _f.save_path), 'rb') as _fi:
                        _content = b64encode(_fi.read()).decode()
                    output_files_data.append(AutoTestOutputFileData(_f.path, _content,
                                                                    str(_f.created_at), str(_f.modified_at)))
                tests_data.append(
                    AutoTestData(test.config.name, test.work_id, test.hostname, test.pid, test.final_state, test.result,
                                 test.exception_class, test.exception_message, test.exception_traceback,
                                 str(test.created_at) if test.created_at is not None else None,
                                 str(test.modified_at) if test.modified_at is not None else None,
                                 str(test.started_at) if test.started_at is not None else None,
                                 str(test.stopped_at) if test.stopped_at is not None else None,
                                 output_files=output_files_data))

            data.append(SubmissionData(sub.submitter.name,
                                       sub.is_cleared,
                                       str(sub.created_at),
                                       str(sub.modified_at),
                                       files_data,
                                       tests_data))

        return data

    @staticmethod
    def import_submissions(task: Task, data: List[SubmissionData]) -> List[Submission]:
        data_folder = app.config['DATA_FOLDER']
        requirement_map = {r.name: r for r in task.file_requirements}
        auto_test_config_map = {c.name: c for c in task.auto_test_configs}
        user_submit_timestamps_map = {}
        imported_submissions = []
        for s in data:
            submitter = AccountService.get_user_by_name(s.submitter_name)
            if submitter is None:
                raise SyncServiceError('submitter not found: %s' % s.submitter_name)

            user_submit_timestamps = user_submit_timestamps_map.get(submitter.id)
            if user_submit_timestamps is None:
                _submissions = db.session.query(Submission) \
                    .filter(Submission.submitter_id == submitter.id,
                            Submission.task_id == task.id) \
                    .all()
                user_submit_timestamps = {str(s.created_at) for s in _submissions}
                user_submit_timestamps_map[submitter.id] = user_submit_timestamps
            if s.created_at in user_submit_timestamps:
                continue

            new_sub = Submission(task_id=task.id, submitter_id=submitter.id, is_cleared=s.is_cleared,
                                 created_at=datetime.strptime(s.created_at, _DATETIME_FORMAT),
                                 modified_at=datetime.strptime(s.modified_at, _DATETIME_FORMAT))
            db.session.add(new_sub)
            imported_submissions.append(new_sub)

            for f in s.files:
                local_path = os.path.join('tasks', str(task.id), 'submissions', submitter.name, f.path)
                local_path_full = os.path.join(data_folder, local_path)
                local_path_folder_full = os.path.dirname(local_path_full)
                if not os.path.exists(local_path_folder_full):
                    os.makedirs(local_path_folder_full)
                with open(local_path_full, 'wb') as fo:
                    fo.write(b64decode(f.content.encode()))
                new_sub_file = SubmissionFile(submission=new_sub, requirement=requirement_map[f.requirement_name],
                                              path=local_path, size=f.size, md5=f.md5,
                                              created_at=datetime.strptime(f.created_at, _DATETIME_FORMAT),
                                              modified_at=datetime.strptime(f.modified_at, _DATETIME_FORMAT))
                db.session.add(new_sub_file)

            for test in s.auto_tests:
                config = auto_test_config_map[test.config_name]
                new_test = AutoTest(
                    submission=new_sub, config=config, work_id=test.work_id, hostname=test.hostname,
                    pid=test.pid, final_state=test.final_state, result=test.result,
                    exception_class=test.exception_class,
                    exception_message=test.exception_message,
                    exception_traceback=test.exception_traceback,
                    created_at=datetime.strptime(test.created_at, _DATETIME_FORMAT) if test.created_at else None,
                    modified_at=datetime.strptime(test.modified_at, _DATETIME_FORMAT) if test.modified_at else None,
                    started_at=datetime.strptime(test.started_at, _DATETIME_FORMAT) if test.started_at else None,
                    stopped_at=datetime.strptime(test.stopped_at, _DATETIME_FORMAT) if test.stopped_at else None)
                db.session.add(new_test)
                db.session.flush()  # flush to get id of new test object

                for output in test.output_files:
                    local_output_path = os.path.join('tasks', str(task.id), 'auto_tests', str(new_test.id), output.path)
                    local_output_path_full = os.path.join(data_folder, local_output_path)
                    local_output_path_folder_full = os.path.dirname(local_output_path_full)
                    if not os.path.exists(local_output_path_folder_full):
                        os.makedirs(local_output_path_folder_full)
                    with open(local_output_path_full, 'wb') as fo2:
                        fo2.write(b64decode(output.content.encode()))
                    new_output_file = AutoTestOutputFile(
                        auto_test=new_test, path=output.path,
                        save_path=local_output_path,
                        created_at=datetime.strptime(output.created_at, _DATETIME_FORMAT),
                        modified_at=datetime.strptime(output.modified_at, _DATETIME_FORMAT))
                    db.session.add(new_output_file)

        db.session.commit()
        return imported_submissions
