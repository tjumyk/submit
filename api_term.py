from flask import Blueprint, jsonify, request

from models import db
from oauth import requires_login
from services.account import AccountService
from services.team import TeamServiceError, TeamService
from services.term import TermService, TermServiceError

term_api = Blueprint('term_api', __name__)


@term_api.route('/', methods=['GET'])
@requires_login
def do_terms():
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403
        return jsonify([t for t in TermService.get_for_user(user)])
    except TermServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@term_api.route('/<int:term_id>/teams', methods=['GET', 'POST'])
@requires_login
def do_teams(term_id):
    term = TermService.get(term_id)
    if term is None:
        return jsonify('term not found'), 404

    if request.method == 'GET':
        try:
            return jsonify([t.to_dict() for t in TeamService.get_for_term(term)])
        except TeamServiceError as e:
            return jsonify(msg=e.msg, detail=e.detail), 500
    else:  # POST
        try:
            params = request.json
            name = params.get('name')
            user = AccountService.get_current_user()
            if user is None:
                return jsonify(msg='no user info'), 403
            team = TeamService.add(term, name, user)
            db.session.commit()
            return jsonify(team.to_dict()), 201
        except TeamServiceError as e:
            return jsonify(msg=e.msg, detail=e.detail), 400
