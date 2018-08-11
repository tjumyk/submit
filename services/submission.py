import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple

from sqlalchemy import desc
from werkzeug.datastructures import FileStorage

from error import BasicError
from models import Submission, Task, UserAlias, Team, SubmissionFile, db


class SubmissionServiceError(BasicError):
    pass


class SubmissionService:
    @staticmethod
    def get(_id: int) -> Optional[Submission]:
        if _id is None:
            raise SubmissionServiceError('id is required')
        if type(_id) is not int:
            raise SubmissionServiceError('id must be an integer')
        return Submission.query.get(_id)

    @staticmethod
    def get_for_task(task: Task) -> List[Submission]:
        if task is None:
            raise SubmissionServiceError('task is required')
        return Submission.query.with_parent(task).all()

    @staticmethod
    def get_for_task_and_user(task: Task, user: UserAlias) -> List[Submission]:
        if task is None:
            raise SubmissionServiceError('task is required')
        if user is None:
            raise SubmissionServiceError('user is required')
        return Submission.query.with_parent(task).with_parent(user).all()

    @staticmethod
    def get_for_task_and_team(task: Task, team: Team) -> List[Submission]:
        if task is None:
            raise SubmissionServiceError('task is required')
        if team is None:
            raise SubmissionServiceError('team is required')
        return Submission.query.with_parent(task).with_parent(team).all()

    @staticmethod
    def add(task: Task, files: Dict[int, FileStorage], save_paths: Dict[int, str],
            submitter: UserAlias = None, submitter_team: Team = None) -> Tuple[Submission, List[Submission]]:
        # assume role has been checked (to minimize dependency)
        # TODO team submission
        # TODO special consideration
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

        # submission attempt limit check
        if task.submission_attempt_limit is not None:
            all_submissions = Submission.query.with_parent(task).with_parent(submitter).count()
            if all_submissions >= task.submission_attempt_limit:
                raise SubmissionServiceError('submission attempt limit exceeded')

        # submission history limit check
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
            file = SubmissionFile(submission=submission, requirement=req, file_path=save_path)
            submission.files.append(file)

        # check remaining requirements
        for req in requirements.values():
            if not req.is_optional:
                raise SubmissionServiceError('unmet requirement', req.name)

        db.session.add(submission)
        return submission, submissions_to_clear

    @staticmethod
    def clear_submission(submission: Submission) ->List[str]:
        if submission is None:
            raise SubmissionServiceError('submission is requried')
        if submission.is_cleared:
            raise SubmissionServiceError('submission is already cleared')
        file_paths = [f.file_path for f in submission.files]
        for file in submission.files:
            db.session.delete(file)
        submission.is_cleared = True
        return file_paths
