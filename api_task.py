import os
import shutil
import time
from datetime import datetime
from typing import Optional

from flask import Blueprint, jsonify, request, current_app as app

from models import db, SpecialConsideration, UserTeamAssociation
from oauth import requires_login
from services.account import AccountService, AccountServiceError
from services.submission import SubmissionService, SubmissionServiceError
from services.task import TaskService, TaskServiceError
from services.team import TeamService, TeamServiceError
from services.term import TermService, TermServiceError
from utils.upload import md5sum

task_api = Blueprint('task_api', __name__)


class SubmissionStatus:
    def __init__(self, attempts: Optional[int],
                 team_association: Optional[UserTeamAssociation],
                 special_consideration: Optional[SpecialConsideration]):
        self.attempts = attempts
        self.team_association = team_association
        self.special_consideration = special_consideration

    def to_dict(self):
        d = dict(attempts=self.attempts)
        d['team_association'] = self.team_association.to_dict(with_team=True) if self.team_association else None
        d['special_consideration'] = self.special_consideration.to_dict() if self.special_consideration else None
        return d


@task_api.route('/<int:tid>')
@requires_login
def do_task(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)
        if not roles:
            return jsonify(msg='access forbidden'), 403

        preview_mode = request.args.get('preview')
        if preview_mode:
            return jsonify(task.to_dict())
        else:  # getting task details requires either admin/tutor role or after the opening time
            if 'admin' not in roles and 'tutor' not in roles:
                if not task.open_time or task.open_time > datetime.utcnow():
                    return jsonify(msg='task has not yet open'), 403
            return jsonify(task.to_dict(with_details=True))
    except (TaskServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/user-submission-summaries')
@requires_login
def task_user_submission_summaries(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        # allow access even before the opening time

        return jsonify([s.to_dict() for s in SubmissionService.get_user_summaries(task)])
    except (TaskServiceError, TermServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/team-submission-summaries')
@requires_login
def task_team_submission_summaries(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        # allow access even before the opening time

        return jsonify([s.to_dict() for s in SubmissionService.get_team_summaries(task)])
    except (TaskServiceError, TermServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/user-submissions/<int:uid>')
@requires_login
def task_user_submissions(tid, uid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        target_user = AccountService.get_user(uid)
        if target_user is None:
            return jsonify(msg='target user not found'), 404

        # allow access even before the opening time

        return jsonify([s.to_dict() for s in SubmissionService.get_for_task_and_user(task, target_user,
                                                                                     include_cleared=True)])
    except (TaskServiceError, TermServiceError, AccountServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/users/<int:uid>')
@requires_login
def get_user(task_id, uid):
    """
    Convenience api for tutors to get student info
    """
    try:
        task = TaskService.get(task_id)
        if task is None:
            return jsonify('task not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 500
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        target_user = AccountService.get_user(uid)
        if 'student' not in TermService.get_access_roles(task.term, target_user):
            return jsonify(msg='only student info allowed')

        return jsonify(target_user.to_dict())
    except AccountServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/my-submission-status')
@requires_login
def task_my_submission_status(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'student' not in roles:
            return jsonify(msg='only for students'), 403

        attempts = SubmissionService.count_for_task_and_user(task, user, include_cleared=True)
        special = TaskService.get_special_consideration_for_task_user(task, user)
        status = SubmissionStatus(attempts, None, special)
        return jsonify(status.to_dict())
    except (TaskServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/my-team-submission-status')
@requires_login
def task_my_team_submission_status(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'student' not in roles:
            return jsonify(msg='only for students'), 403

        # team check
        ass = TeamService.get_team_association(task, user)
        if ass and ass.team.is_finalised:
            attempts = SubmissionService.count_for_team(ass.team, include_cleared=True)
            special = TaskService.get_special_consideration_for_team(ass.team)
            status = SubmissionStatus(attempts, ass, special)
        else:
            status = SubmissionStatus(None, ass, None)
        return jsonify(status.to_dict())
    except (TaskServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/team-submissions/<int:team_id>')
@requires_login
def task_team_submissions(tid, team_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='target team not found'), 404
        if team.task_id != tid:
            return jsonify(msg='target team does not belong to this task'), 400

        # allow access even before the opening time

        return jsonify([s.to_dict(with_submitter=True) for s in SubmissionService.get_for_team(team,
                                                                                               include_cleared=True)])
    except (TaskServiceError, TermServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/my-submissions', methods=['GET', 'POST'])
@requires_login
def task_my_submissions(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'student' not in roles:
            return jsonify(msg='only for students'), 403

        if request.method == 'GET':
            if not task.open_time or datetime.utcnow() < task.open_time:
                return jsonify(msg='task has not yet open'), 403
            return jsonify([s.to_dict() for s in SubmissionService.get_for_task_and_user(task, user)])
        else:  # POST
            # time check will be done in SubmissionService.add method

            # prepare files and paths
            data_folder = app.config['DATA_FOLDER']
            folder = os.path.join('tasks', str(task.id), 'submissions', user.name, str(time.time()))
            files = {}
            save_paths = {}
            requirements = {r.id: r for r in task.file_requirements}
            for name, file in request.files.items():
                try:
                    req_id = int(name)
                    req = requirements[req_id]
                except (ValueError, KeyError):
                    return jsonify(msg='invalid field', detail='invalid requirement id: %r' % name), 400
                files[req_id] = file
                save_paths[req_id] = os.path.join(folder, req.name)

            # create new submission
            new_submission, submissions_to_clear = SubmissionService.add(task, user, files, save_paths)

            # clear outdated submissions according to history limit
            file_paths_to_remove = []
            for submission in submissions_to_clear:
                file_paths_to_remove.append(SubmissionService.clear_submission(submission))

            # prepare new folder
            folder_full = os.path.join(data_folder, folder)
            if os.path.lexists(folder_full):
                return jsonify(msg='submission folder already exists'), 500
            os.makedirs(folder_full)

            # save new files
            file_objects = {f.requirement.id: f for f in new_submission.files}
            for req_id in files:
                req = requirements[req_id]
                file = files[req_id]
                file_obj = file_objects[req_id]
                path = save_paths[req_id]
                full_path = os.path.join(data_folder, path)
                file.save(full_path)

                # size check
                size = os.stat(full_path).st_size
                if req.size_limit is not None and size > req.size_limit:
                    shutil.rmtree(folder_full)  # remove the whole folder
                    return jsonify(msg='file too big', detail=req.name), 400
                file_obj.size = size

                # md5 hash
                file_obj.md5 = md5sum(full_path)

            # remove outdated files
            for batch in file_paths_to_remove:
                for file_path in batch:
                    full_path = os.path.join(data_folder, file_path)
                    if os.path.isfile(full_path):
                        os.remove(full_path)
                # try to delete parent folder if empty now (try to be conservative and make it extensible)
                if batch:
                    folder = os.path.dirname(batch[0])
                    folder_full = os.path.join(data_folder, folder)
                    if os.path.isdir(folder_full) and not os.listdir(folder_full):
                        os.rmdir(folder_full)

            db.session.commit()
            return jsonify(new_submission.to_dict()), 201

    except (TaskServiceError, TermServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/my-team-submissions', methods=['GET'])
@requires_login
def task_my_team_submissions(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'student' not in roles:
            return jsonify(msg='only for students'), 403

        # team check
        ass = TeamService.get_team_association(task, user)
        if not ass:
            return jsonify(msg='user not in a team'), 403
        team = ass.team
        if not team.is_finalised:
            return jsonify(msg='team is not finalised'), 403

        # time check
        if not task.open_time or datetime.utcnow() < task.open_time:
            return jsonify(msg='task has not yet open'), 403

        return jsonify([s.to_dict(with_submitter=True) for s in SubmissionService.get_for_team(team)])
    except (TaskServiceError, TermServiceError, TeamServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/teams', methods=['GET', 'POST'])
@requires_login
def do_teams(task_id):
    try:
        task = TaskService.get(task_id)
        if task is None:
            return jsonify(msg='task not found'), 404

        if request.method == 'GET':
            return jsonify([(t.to_dict(with_creator=True), total_user_associations)
                            for t, total_user_associations in TeamService.get_for_task(task)])
        else:  # POST
            user = AccountService.get_current_user()
            if user is None:
                return jsonify(msg='no user info'), 403

            params = request.json
            team = TeamService.add(task, user, params.get('name'), params.get('slogan'))
            db.session.commit()
            return jsonify(team.to_dict(with_associations=True)), 201
    except (TaskServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/my-team-association', methods=['GET'])
@requires_login
def my_team(task_id):
    try:
        task = TaskService.get(task_id)
        if task is None:
            return jsonify(msg='task not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403

        ass = TeamService.get_team_association(task, user)
        if not ass:
            return "", 204
        return jsonify(ass.to_dict(with_team=True))
    except (TaskServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
