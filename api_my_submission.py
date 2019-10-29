from flask import Blueprint, jsonify, send_from_directory, current_app as app, request, render_template

from auth_connect.oauth import requires_login
from services.account import AccountService
from services.auto_test import AutoTestService, AutoTestServiceError
from services.submission import SubmissionService, SubmissionServiceError
from services.submission_file_diff import SubmissionFileDiffService, SubmissionFileDiffServiceError
from services.submission_file_viewer import SubmissionFileViewerService

my_submission_api = Blueprint('my_submission_api', __name__)


@my_submission_api.route('/<int:sid>')
@requires_login
def do_submission(sid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        submission = SubmissionService.get(sid)
        if submission is None:
            return jsonify(msg='submission not found'), 404

        if submission.submitter_id != user.id:
            return jsonify(msg='not your submission'), 403

        return jsonify(submission.to_dict(with_files=True))
    except SubmissionServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@my_submission_api.route('/<int:sid>/files/<int:fid>/raw')
@my_submission_api.route('/<int:sid>/files/<int:fid>/view')
@my_submission_api.route('/<int:sid>/files/<int:fid>/download')
@my_submission_api.route('/<int:sid>/files/<int:fid>/diff')
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
        if submission.submitter_id != user.id:
            return jsonify(msg='not your submission'), 403

        data_folder = app.config['DATA_FOLDER']
        if request.path.endswith('/raw'):
            return send_from_directory(data_folder, file.path)
        if request.path.endswith('/view'):
            result = SubmissionFileViewerService.select_viewer(file, data_folder)
            if result is not None:  # rendering is supported
                template_name, context = result
                return render_template(template_name, **context)
            # otherwise, fallback to 'raw' content
            return send_from_directory(data_folder, file.path)
        if request.path.endswith('/download'):
            return send_from_directory(data_folder, file.path, as_attachment=True)
        if request.path.endswith('/diff'):
            prev_file = SubmissionService.get_previous_file_for_submitter(file)
            if not prev_file:  # no previous version
                return jsonify(msg='no previous version'), 400
            diff = SubmissionFileDiffService.generate_diff(prev_file, file, data_folder, with_diff_content=True)
            template_name, context = SubmissionFileViewerService.get_diff_viewer(diff)
            return render_template(template_name, **context)
        return jsonify(msg='invalid path'), 400
    except SubmissionServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@my_submission_api.route('/<int:sid>/diff')
@requires_login
def submission_diff(sid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        submission = SubmissionService.get(sid)
        if submission is None:
            return jsonify(msg='submission not found'), 404

        if submission.submitter_id != user.id:
            return jsonify(msg='not your submission'), 403

        data_folder = app.config['DATA_FOLDER']
        results = {}
        for file in submission.files:
            prev_file = SubmissionService.get_previous_file_for_submitter(file)
            if not prev_file:  # no previous version
                continue
            results[file.id] = SubmissionFileDiffService.generate_diff(prev_file, file, data_folder)
        return jsonify({fid: diff.to_dict() for fid, diff in results.items()})
    except (SubmissionServiceError, SubmissionFileDiffServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@my_submission_api.route('/<int:sid>/auto-tests')
@requires_login
def auto_test_and_results(sid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        submission = SubmissionService.get(sid)
        if submission is None:
            return jsonify(msg='submission not found'), 404

        if submission.submitter_id != user.id:
            return jsonify(msg='not your submission'), 403

        update_after = request.args.get('update-after')
        if update_after is not None:
            try:
                update_after = float(update_after)
            except (TypeError, ValueError):
                return jsonify(msg='invalid update-after'), 400

        # return old list format for compatibility with outdated front-end code in students' browsers
        return jsonify([AutoTestService.test_to_dict(test)
                        for test in SubmissionService.get_last_auto_tests(submission, include_private=False,
                                                                          update_after_timestamp=update_after)])
    except (SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
