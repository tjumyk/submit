import os
import shutil
import time
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app as app

from models import db
from oauth import requires_login
from services.account import AccountService
from services.submission import SubmissionService, SubmissionServiceError
from services.task import TaskService, TaskServiceError
from services.term import TermService, TermServiceError
from utils.upload import md5sum

task_api = Blueprint('task_api', __name__)


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

        if 'admin' not in roles and 'tutor' not in roles:
            if not task.open_time or task.open_time > datetime.utcnow():
                return jsonify(msg='task has not yet open'), 403

        return jsonify(task.to_dict(with_details=True))
    except (TaskServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/submissions')
@requires_login
def task_submissions(tid):
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

        # submitter here can be a user or a team
        return jsonify([(submitter.to_dict(), count, last_submit_time) for submitter, count, last_submit_time in
                        SubmissionService.get_summary_for_task(task)])
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
                raise SubmissionServiceError('task has not yet open')
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
            new_submission, submissions_to_clear = SubmissionService.add(task, files, save_paths, submitter=user)

            # clear outdated submissions according to history limit
            file_paths_to_remove = []
            for submission in submissions_to_clear:
                file_paths_to_remove.append(SubmissionService.clear_submission(submission))

            # prepare new folder
            folder_full = os.path.join(data_folder, folder)
            if os.path.lexists(folder_full):
                raise SubmissionServiceError('submission folder already exists')
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
                    if not os.listdir(folder_full):
                        os.rmdir(folder_full)

            db.session.commit()
            return jsonify(new_submission.to_dict()), 201

    except (TaskServiceError, TermServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
