from flask import Blueprint, jsonify, send_from_directory, current_app as app

from auth_connect.oauth import requires_login
from services.account import AccountService
from services.auto_test import AutoTestService, AutoTestServiceError
from services.submission import SubmissionService, SubmissionServiceError
from services.team import TeamService, TeamServiceError

my_team_submission_api = Blueprint('my_team_submission_api', __name__)


@my_team_submission_api.route('/<int:sid>')
@requires_login
def do_submission(sid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        submission = SubmissionService.get(sid)
        if submission is None:
            return jsonify(msg='submission not found'), 404

        # team check
        task = submission.task
        ass = TeamService.get_team_association(task, user)
        if not ass:
            return jsonify(msg='user not in a team'), 403
        team = ass.team
        if not team.is_finalised:
            return jsonify(msg='team is not finalised'), 403

        # same team check
        is_same_team = False
        for _ass in team.user_associations:
            if _ass.user_id == submission.submitter_id:
                is_same_team = True
                break
        if not is_same_team:
            return jsonify(msg="not your team's submission"), 403

        return jsonify(submission.to_dict(with_files=True, with_submitter=True))
    except (SubmissionServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@my_team_submission_api.route('/<int:sid>/files/<int:fid>/download')
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

        # team check
        task = submission.task
        ass = TeamService.get_team_association(task, user)
        if not ass:
            return jsonify(msg='user not in a team'), 403
        team = ass.team
        if not team.is_finalised:
            return jsonify(msg='team is not finalised'), 403

        # same team check
        is_same_team = False
        for _ass in team.user_associations:
            if _ass.user_id == submission.submitter_id:
                is_same_team = True
                break
        if not is_same_team:
            return jsonify(msg="not your team's submission"), 403

        data_folder = app.config['DATA_FOLDER']
        return send_from_directory(data_folder, file.path, as_attachment=True)
    except (SubmissionServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@my_team_submission_api.route('/<int:sid>/auto-tests')
@requires_login
def auto_test_and_results(sid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        submission = SubmissionService.get(sid)
        if submission is None:
            return jsonify(msg='submission not found'), 404

        # team check
        task = submission.task
        ass = TeamService.get_team_association(task, user)
        if not ass:
            return jsonify(msg='user not in a team'), 403
        team = ass.team
        if not team.is_finalised:
            return jsonify(msg='team is not finalised'), 403

        # same team check
        is_same_team = False
        for _ass in team.user_associations:
            if _ass.user_id == submission.submitter_id:
                is_same_team = True
                break
        if not is_same_team:
            return jsonify(msg="not your team's submission"), 403

        tests = []
        for test in submission.auto_tests:
            if test.config.is_private:  # skip private tests
                continue
            test_obj = test.to_dict()
            if not test.final_state:  # running tests
                result_obj = AutoTestService.result_to_dict(AutoTestService.get_result(test))
                test_obj.update(result_obj)  # merge temporary result
            tests.append(test_obj)

        return jsonify(tests)
    except (SubmissionServiceError, TeamServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
