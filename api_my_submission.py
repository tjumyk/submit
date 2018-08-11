from flask import Blueprint, jsonify, send_from_directory, current_app as app

from oauth import requires_login
from services.account import AccountService
from services.submission import SubmissionService, SubmissionServiceError
from services.team import TeamService, TeamServiceError
from services.term import TermServiceError

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

        if submission.submitter_id is not None and submission.submitter_id != user.id:
            return jsonify(msg='not your submission'), 403
        if submission.submitter_team_id is not None and not TeamService.is_member(submission.submitter_team, user):
            return jsonify(msg="not your team's submission"), 403

        return jsonify(submission.to_dict(with_files=True))
    except (SubmissionServiceError, TermServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@my_submission_api.route('/<int:sid>/files/<int:fid>/download')
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
        if submission.submitter_id is not None and submission.submitter_id != user.id:
            return jsonify(msg='not your submission'), 403
        if submission.submitter_team_id is not None and not TeamService.is_member(submission.submitter_team, user):
            return jsonify(msg="not your team's submission"), 403

        data_folder = app.config['DATA_FOLDER']
        return send_from_directory(data_folder, file.path, as_attachment=True)
    except (SubmissionServiceError, TermServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
