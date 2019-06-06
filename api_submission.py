import json
import os
from datetime import datetime
from functools import wraps

from flask import Blueprint, jsonify, current_app as app, send_from_directory, request, render_template

from auth_connect.oauth import requires_login
from models import db
from services.account import AccountService
from services.auto_test import AutoTestService, AutoTestServiceError
from services.submission import SubmissionService, SubmissionServiceError
from services.team import TeamService, TeamServiceError
from services.term import TermService, TermServiceError

submission_api = Blueprint('submission_api', __name__)

_highlight_file_extensions = {
    'py',
    'pl', 'ruby', 'php',
    'c', 'h', 'cpp', 'cxx', 'hpp',
    'java', 'cs',
    'js', 'css', 'html', 'coffee',
    'sh',
    'json', 'xml',
    'sql',
    'md', 'markdown'
}


def requires_worker(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return jsonify(msg='unauthorized access'), 401
        authorized = False
        for worker in app.config['AUTO_TEST']['workers']:
            if worker['name'] == auth.username and worker['password'] == auth.password:
                authorized = True
                break
        if not authorized:
            return jsonify(msg='access forbidden'), 403
        return f(*args, **kwargs)

    return wrapped


@submission_api.route('/<int:sid>')
@requires_login
def do_submission(sid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        submission = SubmissionService.get(sid)
        if submission is None:
            return jsonify(msg='submission not found'), 404
        roles = TermService.get_access_roles(submission.task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        return jsonify(submission.to_dict(with_submitter=True, with_files=True, with_advanced_fields=True))
    except (SubmissionServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@submission_api.route('/<int:sid>/files/<int:fid>/raw')
@submission_api.route('/<int:sid>/files/<int:fid>/download')
@requires_login
def submission_file_download(sid, fid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        file = SubmissionService.get_file(fid)
        if file is None:
            return jsonify(msg='file not found'), 404
        if file.submission_id != sid:
            return jsonify(msg='file does not belong to submission %s' % str(sid))

        submission = file.submission
        roles = TermService.get_access_roles(submission.task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        data_folder = app.config['DATA_FOLDER']
        as_attachment = request.path.endswith('/download')
        return send_from_directory(data_folder, file.path, as_attachment=as_attachment)
    except (SubmissionServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@submission_api.route('/<int:sid>/files/<int:fid>/view')
@requires_login
def submission_file_view(sid, fid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        file = SubmissionService.get_file(fid)
        if file is None:
            return jsonify(msg='file not found'), 404
        if file.submission_id != sid:
            return jsonify(msg='file does not belong to submission %s' % str(sid))

        submission = file.submission
        roles = TermService.get_access_roles(submission.task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        data_folder = app.config['DATA_FOLDER']
        file_name = file.requirement.name

        _, ext = os.path.splitext(file_name)
        ext = ext.lower().lstrip('.')
        if ext in _highlight_file_extensions:  # code highlight
            with open(os.path.join(data_folder, file.path)) as f_file:
                file_content = f_file.read()
            return render_template('highlight.html', sid=sid, fid=fid,
                                   name=file_name, content=file_content, md5=file.md5[0:6])

        # if rendering is not supported, send raw content like '/raw' endpoint
        return send_from_directory(data_folder, file.path)
    except (SubmissionServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@submission_api.route('/<int:sid>/auto-tests')
@requires_login
def test_and_results(sid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        submission = SubmissionService.get(sid)
        if submission is None:
            return jsonify(msg='submission not found'), 404
        roles = TermService.get_access_roles(submission.task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        return jsonify([AutoTestService.test_to_dict(t, with_advanced_fields=True)
                        for t in SubmissionService.get_auto_tests(submission, joined_load_output_files=True)])
    except (SubmissionServiceError, TermServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@submission_api.route('/<int:sid>/auto-tests/<int:tid>/output-files/<int:fid>/raw')
@submission_api.route('/<int:sid>/auto-tests/<int:tid>/output-files/<int:fid>/download')
@requires_login
def download_auto_test_output_file(sid, tid, fid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        submission = SubmissionService.get(sid)
        if submission is None:
            return jsonify(msg='submission not found'), 404
        roles = TermService.get_access_roles(submission.task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        test = AutoTestService.get(tid)
        if test is None:
            return jsonify(msg='test not found'), 404
        if test.submission_id != sid:
            return jsonify(msg='test does not belong to the submission'), 400

        file = AutoTestService.get_output_file(fid)
        if file is None:
            return jsonify(msg='file not found'), 404
        if file.auto_test_id != tid:
            return jsonify(msg='file does not belong to the test'), 400

        data_folder = app.config['DATA_FOLDER']
        as_attachment = request.path.endswith('/download')
        return send_from_directory(data_folder, file.save_path, as_attachment=as_attachment)
    except (SubmissionServiceError, TermServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@submission_api.route('/<int:sid>/worker-get-submission-and-config/<string:wid>')
@requires_worker
def worker_get_submission_and_config(sid, wid):
    try:
        test = AutoTestService.get_by_submission_work_id(sid, wid)
        if test is None:
            return jsonify(msg='test not found'), 404
        submission = test.submission

        submission_dict = submission.to_dict(with_files=True)
        config_dict = test.config.to_dict(with_environment=True, with_advanced_fields=True)

        task = submission.task
        if task.is_team_task:  # plug in team info
            ass = TeamService.get_team_association(task, submission.submitter)
            if ass is None:
                return jsonify(msg='team info not found'), 500
            submission_dict['submitter_team_id'] = ass.team_id

        return jsonify(dict(submission=submission_dict, config=config_dict))
    except (AutoTestServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@submission_api.route('/<int:sid>/worker-submission-files/<string:wid>/<int:fid>')
@requires_worker
def worker_download_file(sid, wid, fid):
    try:
        test = AutoTestService.get_by_submission_work_id(sid, wid)
        if test is None:
            return jsonify(msg='test not found'), 404

        file = SubmissionService.get_file(fid)
        if file is None:
            return jsonify(msg='file not found'), 404
        if file.submission_id != sid:
            return jsonify(msg='file does not belong to submission %s' % str(sid))

        data_folder = app.config['DATA_FOLDER']
        return send_from_directory(data_folder, file.path, as_attachment=True)
    except AutoTestServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@submission_api.route('/<int:sid>/worker-started/<string:wid>', methods=['PUT'])
@requires_worker
def worker_start(sid, wid):
    try:
        test = AutoTestService.get_by_submission_work_id(sid, wid)
        if test is None:
            return jsonify(msg='test not found'), 404

        params = request.json
        test.hostname = params.get('hostname')
        test.pid = params.get('pid')

        test.started_at = datetime.utcnow()
        db.session.commit()
        return "", 204
    except AutoTestServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@submission_api.route('/<int:sid>/worker-result/<string:wid>', methods=['PUT'])
@requires_worker
def worker_result(sid, wid):
    try:
        test = AutoTestService.get_by_submission_work_id(sid, wid)
        if test is None:
            return jsonify(msg='test not found'), 404

        params = request.json
        final_state = params.get('final_state')
        if not final_state:
            return jsonify(msg='final state is required'), 400

        test.final_state = final_state
        result = params.get('result')
        test.result = json.dumps(result) if result is not None else None
        test.exception_class = params.get('exception_class')
        test.exception_message = params.get('exception_message')
        test.exception_traceback = params.get('exception_traceback')

        test.stopped_at = datetime.utcnow()
        db.session.commit()
        return "", 204
    except AutoTestServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@submission_api.route('/<int:sid>/worker-output-files/<string:wid>', methods=['POST'])
@requires_worker
def worker_output_files(sid, wid):
    try:
        test = AutoTestService.get_by_submission_work_id(sid, wid)
        if test is None:
            return jsonify(msg='test not found'), 404

        data_folder = app.config['DATA_FOLDER']
        save_folder = os.path.join('tasks', str(test.submission.task_id), 'auto_tests', str(test.id))
        save_folder_full = os.path.join(data_folder, save_folder)

        for name in request.files:
            AutoTestService.add_output_file(test, name, os.path.join(save_folder, name))

        if not os.path.lexists(save_folder_full):
            os.makedirs(save_folder_full)
        for name, file in request.files.items():
            file.save(os.path.join(data_folder, save_folder, name))

        db.session.commit()
        return "", 204
    except AutoTestServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@submission_api.route('/<int:sid>/worker-output-files/<string:wid>/<int:fid>')
@requires_worker
def worker_output_file(sid, wid, fid):
    try:
        test = AutoTestService.get_by_submission_work_id(sid, wid)
        if test is None:
            return jsonify(msg='test not found'), 404

        file = AutoTestService.get_output_file(fid)
        if file.auto_test_id != test.id:
            return jsonify(msg='file does not belongs to the test'), 400

        data_folder = app.config['DATA_FOLDER']
        return send_from_directory(data_folder, file.save_path, as_attachment=True)
    except AutoTestServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
