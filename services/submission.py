import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple

from celery.result import AsyncResult
from sqlalchemy import desc, func
from werkzeug.datastructures import FileStorage

from testbot import bot
from error import BasicError
from models import Submission, Task, UserAlias, Team, SubmissionFile, db, UserTeamAssociation, AutoTest
from services.auto_test import AutoTestService
from services.task import TaskService


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
    def get_files(requirement_id: int) -> List[Tuple[int, int, SubmissionFile]]:
        return db.session.query(Submission.id, Submission.submitter_id, SubmissionFile)\
            .filter(SubmissionFile.requirement_id == requirement_id,
                    Submission.id == SubmissionFile.submission_id)\
            .all()

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
    def run_auto_test(submission: Submission) -> Tuple[AutoTest, AsyncResult]:
        if submission is None:
            raise SubmissionServiceError('submission is required')

        if submission.task.evaluation_method != 'auto_test':
            raise SubmissionServiceError('evaluation method is not auto testing')

        result = bot.run_test.apply_async((submission.id,), countdown=3)  # wait 3 seconds to allow db commit
        test = AutoTestService.add(submission, result.id)
        return test, result
