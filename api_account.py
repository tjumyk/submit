from flask import Blueprint, jsonify

from auth_connect.oauth import requires_login
from services.account import AccountService

account_api = Blueprint('account_api', __name__)


@account_api.route('/me')
@requires_login
def get_me():
    user = AccountService.get_current_user()
    if user is None:
        return jsonify(msg='no user info'), 403
    return jsonify(user.to_dict())
