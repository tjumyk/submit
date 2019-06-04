from flask import Blueprint, request, jsonify, current_app as app

from auth_connect.oauth import requires_login
from models import db
from services.account import AccountService
from services.message_sender import MessageSenderService, MessageSenderServiceError
from services.messsage import MessageService, MessageServiceError
from services.team import TeamService, TeamServiceError
from utils.message import build_message_with_template
from utils.upload import handle_upload, handle_post_upload, UploadError

team_api = Blueprint('team_api', __name__)


@team_api.route('/<int:team_id>', methods=['GET', 'PUT', 'DELETE'])
@requires_login
def do_team(team_id):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404

        if request.method == 'GET':
            return jsonify(team.to_dict(with_associations=True))
        elif request.method == 'PUT':
            user = AccountService.get_current_user()
            if user is None:
                return jsonify(msg='no user info'), 403
            if not TeamService.is_creator(team, user):
                return jsonify(msg='team creator required'), 403

            params = request.json or request.form.to_dict() or {}
            files = request.files
            upload_type = 'avatar'
            if 'avatar' in files:
                params['avatar'] = handle_upload(files.avatar, upload_type,
                                                 image_check=True, image_check_squared=True)
            old = TeamService.update(team, **params)
            if 'avatar' in old:
                handle_post_upload(old['avatar'], upload_type)

            db.session.commit()
            return jsonify(team.to_dict(with_associations=True))
        else:  # DELETE
            user = AccountService.get_current_user()
            if user is None:
                return jsonify(msg='no user info'), 403
            if not TeamService.is_creator(team, user):
                return jsonify(msg='team creator required'), 403

            task = team.task
            msg_args = dict(site=app.config['SITE'],
                            operator_name='%s (%s)' % (user.nickname, user.name) if user.nickname else user.name,
                            team=team,
                            task=task,
                            term=task.term)
            msg_content = build_message_with_template('team_dismissed', msg_args)
            msg_channel = MessageService.get_channel_by_name('team')
            msgs, mails = MessageSenderService.send_to_users(msg_channel, task.term, msg_content, None,
                                                             [ass.user for ass in team.user_associations])

            TeamService.dismiss(team)
            db.session.commit()
            for mail in mails:
                mail.send()
            return "", 204
    except (TeamServiceError, UploadError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
    except (MessageSenderServiceError, MessageServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


@team_api.route('/<int:team_id>/users', methods=['GET'])
@requires_login
def team_users(team_id):
    """
    Notice: team "users" are not necessarily "members", only those agreed by both the user and the team creator are
    "members".
    """
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        return jsonify([ass.to_dict(with_user=True) for ass in team.user_associations])
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@team_api.route('/<int:team_id>/invite/<int:uid>', methods=['PUT', 'DELETE'])
@requires_login
def team_invite(team_id, uid):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403
        if not TeamService.is_creator(team, user):
            return jsonify(msg='team creator required'), 403
        target_user = AccountService.get_user(uid)
        if target_user is None:
            return jsonify(msg='invited user not found'), 404

        if request.method == 'PUT':
            TeamService.invite(team, target_user)
            db.session.commit()
            # TODO send email
        else:  # DELETE
            TeamService.handle_invitation(team, target_user, False)
            db.session.commit()
            # TODO send email
        return "", 204
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@team_api.route('/<int:team_id>/handle-invite', methods=['PUT', 'DELETE'])
@requires_login
def team_invite_accept(team_id):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403

        TeamService.handle_invitation(team, user, request.method == 'PUT')
        db.session.commit()
        # TODO send email
        return "", 204
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@team_api.route('/<int:team_id>/join', methods=['PUT', 'DELETE'])
@requires_login
def team_apply(team_id):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        if team is None:
            return jsonify(msg='team not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403

        task = team.task
        creator = team.creator
        msg_args = dict(site=app.config['SITE'],
                        requester_name='%s (%s)' % (user.nickname, user.name) if user.nickname else user.name,
                        recipient_name=creator.nickname if creator.nickname else creator.name,
                        team=team,
                        task=task,
                        term=task.term)
        msg_channel = MessageService.get_channel_by_name('team')

        if request.method == 'PUT':
            msg_content = build_message_with_template('team_join_requested', msg_args)
            msg, mail = MessageSenderService.send_to_user(msg_channel, task.term, msg_content, None, creator)

            TeamService.apply_join(team, user)
        else:  # DELETE
            msg_content = build_message_with_template('team_join_request_cancelled', msg_args)
            msg, mail = MessageSenderService.send_to_user(msg_channel, task.term, msg_content, None, creator)

            TeamService.handle_join_application(team, user, False)

        db.session.commit()
        if mail:
            mail.send()
        return "", 204
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
    except (MessageSenderServiceError, MessageServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


@team_api.route('/<int:team_id>/handle-join/<int:applicant_id>', methods=['PUT', 'DELETE'])
@requires_login
def team_apply_accept(team_id, applicant_id):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403
        if not TeamService.is_creator(team, user):
            return jsonify(msg='team creator required'), 403
        applicant = AccountService.get_user(applicant_id)
        if applicant is None:
            return jsonify(msg='applicant not found'), 404

        task = team.task
        msg_args = dict(site=app.config['SITE'],
                        operator_name='%s (%s)' % (user.nickname, user.name) if user.nickname else user.name,
                        recipient_name=applicant.nickname if applicant.nickname else applicant.name,
                        team=team,
                        task=task,
                        term=task.term)
        msg_channel = MessageService.get_channel_by_name('team')

        is_accepted = request.method == 'PUT'
        if is_accepted:
            msg_content = build_message_with_template('team_join_request_accepted', msg_args)
            msg, mail = MessageSenderService.send_to_user(msg_channel, task.term, msg_content, None, applicant)
        else:
            msg_content = build_message_with_template('team_join_request_rejected', msg_args)
            msg, mail = MessageSenderService.send_to_user(msg_channel, task.term, msg_content, None, applicant)

        TeamService.handle_join_application(team, applicant, is_accepted)
        db.session.commit()
        if mail:
            mail.send()
        return "", 204
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
    except (MessageSenderServiceError, MessageServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


@team_api.route('/<int:team_id>/leave', methods=['PUT'])
@requires_login
def team_leave(team_id):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403

        task = team.task
        creator = team.creator
        msg_args = dict(site=app.config['SITE'],
                        member_name='%s (%s)' % (user.nickname, user.name) if user.nickname else user.name,
                        recipient_name=creator.nickname if creator.nickname else creator.name,
                        team=team,
                        task=task,
                        term=task.term)
        msg_content = build_message_with_template('team_member_leave', msg_args)
        msg_channel = MessageService.get_channel_by_name('team')
        msg, mail = MessageSenderService.send_to_user(msg_channel, task.term, msg_content, None, creator)

        TeamService.leave(team, user)
        db.session.commit()
        if mail:
            mail.send()
        return "", 204
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
    except (MessageSenderServiceError, MessageServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


@team_api.route('/<int:team_id>/kick-out/<int:uid>', methods=['PUT'])
@requires_login
def team_kick_out(team_id, uid):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403
        if not TeamService.is_creator(team, user):
            return jsonify(msg='team creator required'), 403
        target_user = AccountService.get_user(uid)
        if target_user is None:
            return jsonify(msg='target user not found'), 404

        task = team.task
        msg_args = dict(site=app.config['SITE'],
                        operator_name='%s (%s)' % (user.nickname, user.name) if user.nickname else user.name,
                        recipient_name=target_user.nickname if target_user.nickname else target_user.name,
                        team=team,
                        task=task,
                        term=task.term)
        msg_channel = MessageService.get_channel_by_name('team')
        msg_content = build_message_with_template('team_kicked_out', msg_args)
        msg, mail = MessageSenderService.send_to_user(msg_channel, task.term, msg_content, None, target_user)

        TeamService.leave(team, target_user)
        db.session.commit()
        if mail:
            mail.send()
        return "", 204
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
    except (MessageSenderServiceError, MessageServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


@team_api.route('/<int:team_id>/finalise', methods=['PUT'])
@requires_login
def team_finalise(team_id):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403
        if not TeamService.is_creator(team, user):
            return jsonify(msg='team creator required'), 403

        task = team.task
        msg_args = dict(site=app.config['SITE'],
                        operator_name='%s (%s)' % (user.nickname, user.name) if user.nickname else user.name,
                        team=team,
                        task=task,
                        term=task.term)
        msg_channel = MessageService.get_channel_by_name('team')
        msg_content = build_message_with_template('team_finalised', msg_args)

        msgs, mails = MessageSenderService.send_to_users(msg_channel, task.term, msg_content, None,
                                                         [ass.user for ass in team.user_associations])

        TeamService.finalise(team)
        db.session.commit()
        for mail in mails:
            mail.send()
        return "", 204
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
    except (MessageSenderServiceError, MessageServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 500
