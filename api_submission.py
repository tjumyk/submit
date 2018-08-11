from flask import Blueprint, jsonify, current_app as app, send_from_directory

from oauth import requires_login
from services.account import AccountService
from services.submission import SubmissionService, SubmissionServiceError
from services.term import TermService, TermServiceError

submission_api = Blueprint('submission_api', __name__)


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
