from flask import Blueprint, jsonify

from auth_connect.oauth import requires_login
from services.account import AccountService
from services.term import TermService, TermServiceError

term_api = Blueprint('term_api', __name__)


@term_api.route('/<int:term_id>')
@requires_login
def do_term(term_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404
        if not TermService.get_access_roles(term, user):
            return jsonify(msg='access forbidden'), 403
        return jsonify(term.to_dict())
    except TermServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@term_api.route('/<int:term_id>/tasks')
@requires_login
def term_tasks(term_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404
        if not TermService.get_access_roles(term, user):
            return jsonify(msg='access forbidden'), 403

        # Notice: must not expose task details in this api because there's no time check here
        return jsonify([t.to_dict(with_details=False, with_advanced_fields=False)
                        for t in sorted(term.tasks, key=lambda t: t.id)])
    except TermServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
