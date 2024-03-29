import html
import time
from datetime import datetime

from flask import Blueprint, jsonify, send_from_directory, current_app as app, request, render_template

from auth_connect.oauth import requires_login
from models import db
from services.account import AccountService
from services.auto_test import AutoTestService, AutoTestServiceError
from services.message_sender import MessageSenderService, MessageSenderServiceError
from services.messsage import MessageService, MessageServiceError
from services.submission import SubmissionService, SubmissionServiceError
from services.submission_file_diff import SubmissionFileDiffService, SubmissionFileDiffServiceError
from services.submission_file_viewer import SubmissionFileViewerService
from services.team import TeamService, TeamServiceError
from utils.message import build_message_with_template

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
        submitter_ass = None
        for _ass in team.user_associations:
            if _ass.user_id == submission.submitter_id:
                submitter_ass = _ass
                break
        if submitter_ass is None:
            return jsonify(msg="not your team's submission"), 403

        prev_submission, next_submission = \
            SubmissionService.get_neighbour_submissions_for_team(submission, submitter_ass)

        d = submission.to_dict(with_files=True, with_submitter=True)
        d['prev_id'] = prev_submission.id if prev_submission else None
        d['next_id'] = next_submission.id if next_submission else None
        return jsonify(d)
    except (SubmissionServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@my_team_submission_api.route('/<int:sid>/files/<int:fid>/raw')
@my_team_submission_api.route('/<int:sid>/files/<int:fid>/view')
@my_team_submission_api.route('/<int:sid>/files/<int:fid>/download')
@my_team_submission_api.route('/<int:sid>/files/<int:fid>/diff')
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
            prev_file = SubmissionService.get_previous_file_for_team(file)
            if not prev_file:  # no previous version
                return jsonify(msg='no previous version'), 400
            diff = SubmissionFileDiffService.generate_diff(prev_file, file, data_folder, with_diff_content=True)
            template_name, context = SubmissionFileViewerService.get_diff_viewer(diff)
            return render_template(template_name, **context)
        return jsonify(msg='invalid path'), 400
    except (SubmissionServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@my_team_submission_api.route('/<int:sid>/diff')
@requires_login
def submission_diff(sid):
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

        data_folder = app.config['DATA_FOLDER']
        results = {}
        for file in submission.files:
            prev_file = SubmissionService.get_previous_file_for_team(file)
            if not prev_file:  # no previous version
                continue
            results[file.id] = SubmissionFileDiffService.generate_diff(prev_file, file, data_folder)
        return jsonify({fid: diff.to_dict() for fid, diff in results.items()})
    except (SubmissionServiceError, SubmissionFileDiffServiceError, TeamServiceError) as e:
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

        update_after = request.args.get('update_after')
        if update_after is not None:
            try:
                update_after = float(update_after)
            except (TypeError, ValueError):
                return jsonify(msg='invalid update_after'), 400

        timestamp = int(time.time())
        tests = [AutoTestService.test_to_dict(test)
                 for test in SubmissionService.get_last_auto_tests(submission, include_private=False,
                                                                   update_after_timestamp=update_after)]
        return jsonify(tests=tests, timestamp=timestamp)
    except (SubmissionServiceError, TeamServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@my_team_submission_api.route('/<int:sid>/comments', methods=['GET', 'POST'])
@requires_login
def do_comments(sid):
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

        if request.method == 'GET':
            return jsonify([c.to_dict() for c in SubmissionService.get_comments(submission)])
        else:  # POST
            task = submission.task
            if task.close_time and task.close_time < datetime.utcnow():
                return jsonify(msg='task has closed'), 400

            last_comment = SubmissionService.get_last_comment(submission)
            comment = SubmissionService.add_comment(submission, user, request.json.get('content'))

            # check if need to send an email
            if last_comment is None or last_comment.author_id != user.id \
                    or datetime.utcnow() - last_comment.modified_at > SubmissionService.COMMENT_SESSION_EXPIRY:
                term = task.term
                course = term.course
                author_name = '%s (%s)' % (user.nickname, user.name) if user.nickname else user.name
                submission_path = 'team-submissions/%d/%d' % (team.id, submission.id)
                mail_args = dict(site=app.config['SITE'], term=term, task=task,
                                 submission=submission, submission_path=submission_path,
                                 comment=comment, comment_escaped_content=html.escape(comment.content),
                                 author_name=author_name)
                msg_content = build_message_with_template('submission_new_comment', mail_args)
                msg_channel = MessageService.get_channel_by_name('comment')
                msg, mails = MessageSenderService.send_to_group(msg_channel, term, msg_content, None,
                                                                course.tutor_group, hide_peers=False)
            else:
                mails = []

            db.session.commit()
            for mail in mails:
                mail.send()

            return jsonify(comment.to_dict()), 201
    except (SubmissionServiceError, TeamServiceError, AutoTestServiceError, MessageServiceError,
            MessageSenderServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
