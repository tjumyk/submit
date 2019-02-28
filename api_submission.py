import json
import os
from datetime import datetime
from functools import wraps

from flask import Blueprint, jsonify, current_app as app, send_from_directory, request

from models import db
from oauth import requires_login
from services.account import AccountService
from services.auto_test import AutoTestService, AutoTestServiceError
from services.submission import SubmissionService, SubmissionServiceError
from services.term import TermService, TermServiceError

submission_api = Blueprint('submission_api', __name__)


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
        return send_from_directory(data_folder, file.path, as_attachment=True)
    except (SubmissionServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@submission_api.route('/<int:sid>/run-auto-test')
@requires_login
def run_test(sid):
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

        test, result = SubmissionService.run_auto_test(submission)
        db.session.commit()

        test_obj = test.to_dict(with_advanced_fields=True)
        test_obj.update(AutoTestService.result_to_dict(result, with_advanced_fields=True))  # merge temporary result
        return jsonify(test_obj), 201
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

        tests = []
        for test in submission.auto_tests:
            test_obj = test.to_dict(with_advanced_fields=True)
            if not test.final_state:  # running tests
                result = AutoTestService.get_result(test)
                result_obj = AutoTestService.result_to_dict(result, with_advanced_fields=True)
                test_obj.update(result_obj)  # merge temporary result
            tests.append(test_obj)

        return jsonify(tests)
    except (SubmissionServiceError, TermServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@submission_api.route('/<int:sid>/auto-tests/<int:tid>', methods=['DELETE'])
@requires_login
def do_test(sid, tid):
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

        data_folder = app.config['DATA_FOLDER']
        for file in test.output_files:
            save_path_full = os.path.join(data_folder, file.save_path)
            if os.path.lexists(save_path_full):
                os.remove(save_path_full)
        if test.output_files:  # try to remove parent folder if empty now
            folder_path = os.path.dirname(test.output_files[0].save_path)
            folder_path_full = os.path.join(data_folder, folder_path)
            if os.path.lexists(folder_path_full) and not os.listdir(folder_path_full):
                os.rmdir(folder_path_full)

        result = AutoTestService.get_result(test)
        result.forget()  # remove temporary result from storage (if any)

        for file in test.output_files:
            db.session.delete(file)
        db.session.delete(test)
        db.session.commit()
        return "", 204
    except (SubmissionServiceError, TermServiceError) as e:
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


@submission_api.route('/<int:sid>/worker-get-submission/<string:wid>')
@requires_worker
def worker_get_auto_test(sid, wid):
    try:
        test = AutoTestService.get_by_submission_work_id(sid, wid)
        if test is None:
            return jsonify(msg='test not found'), 404
        return jsonify(test.submission.to_dict(with_files=True, with_auto_test_environment=True))
    except AutoTestServiceError as e:
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
