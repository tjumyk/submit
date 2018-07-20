from flask import Blueprint, request, jsonify

from models import db
from oauth import requires_login
from services.account import AccountService
from services.team import TeamService, TeamServiceError
from utils.upload import handle_upload, handle_post_upload, UploadError

team_api = Blueprint('team_api', __name__)


@team_api.route('/<int:team_id>', methods=['GET', 'PUT', 'DELETE'])
@requires_login
def do_team(team_id):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403

        if request.method == 'GET':
            return jsonify(team.to_dict())
        elif request.method == 'PUT':
            if TeamService.get_creator(team) != user:
                return jsonify(msg='team creator required'), 403
            params = request.json or request.form or {}
            files = request.files
            upload_type = 'avatar'
            if 'avatar' in files:
                params['avatar'] = handle_upload(files.avatar, upload_type,
                                                 image_check=True, image_check_squared=True)
            old = TeamService.update(team, **params)
            if 'avatar' in old:
                handle_post_upload(old['avatar'], upload_type)
            db.session.commit()
            return jsonify(team.to_dict())
        else:  # DELETE
            if TeamService.get_creator(team) != user:
                return jsonify(msg='team creator required'), 403
            TeamService.dismiss(team)
            db.session.commit()
            return "", 204
    except (TeamServiceError, UploadError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@team_api.route('/<int:team_id>/users', methods=['GET'])
@requires_login
def team_invitations(team_id):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        return jsonify([a.to_dict(with_user=True) for a in TeamService.get_user_associations(team)])
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
        if TeamService.get_creator(team) != user:
            return jsonify(msg='team creator required'), 403
        invite_user = AccountService.get_user(uid)
        if invite_user is None:
            return jsonify(msg='invited user not found'), 404

        if request.method == 'PUT':
            TeamService.invite(team, invite_user)
            db.session.commit()
        else:  # DELETE
            TeamService.cancel_invitation(team, user)
            db.session.commit()
        return "", 204
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@team_api.route('/<int:team_id>/invite-accept', methods=['PUT'])
@requires_login
def team_invite_accept(team_id):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403

        TeamService.agree_invitation(team, user)
        db.session.commit()
        return "", 204
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@team_api.route('/<int:team_id>/apply', methods=['PUT', 'DELETE'])
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

        if request.method == 'PUT':
            TeamService.apply_join(team, user)
            db.session.commit()
        else:  # DELETE
            TeamService.cancel_join_application(team, user)
            db.session.commit()
        return "", 204
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@team_api.route('/<int:team_id>/apply-accept/<applicant_id>', methods=['PUT'])
@requires_login
def team_apply_accept(team_id, applicant_id):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403
        if TeamService.get_creator(team) != user:
            return jsonify(msg='team creator required'), 403
        applicant = AccountService.get_user(applicant_id)
        if applicant is None:
            return jsonify(msg='applicant not found'), 404

        TeamService.agree_join_application(team, applicant)
        db.session.commit()
        return "", 204
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


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
        if TeamService.get_creator(team) != user:
            return jsonify(msg='team creator required'), 403

        TeamService.finalise(team)
        db.session.commit()
        return "", 204
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
