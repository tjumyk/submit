from flask import Blueprint, jsonify

import oauth
from oauth import requires_login

account_api = Blueprint('account_api', __name__)


@account_api.route('/me')
@requires_login
def get_me():
    user = oauth.get_user()
    if user is None:
        return jsonify(msg='no user info'), 403
    return jsonify(user.to_dict())

