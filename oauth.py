import json
from functools import wraps
from typing import List
from urllib.parse import urlencode

import requests
from flask import Flask, request, current_app, session, redirect, g, jsonify

# ==== Constants ====

_config_key = 'OAUTH'
_request_user_key = 'oauth_user'
_session_uid_key = 'uid'
_session_access_token_key = 'access_token'
_admin_group_name = 'admin'


# ==== Exceptions ====

class OAuthError(Exception):
    def __init__(self, msg, detail=None):
        self.msg = msg
        self.detail = detail


class OAuthRequired(OAuthError):
    def __init__(self):
        super(OAuthRequired, self).__init__('authentication required')


class OAuthRequestError(OAuthError):
    pass


class OAuthAPIError(OAuthError):
    pass


class OAuthResultError(OAuthError):
    pass


# ==== Model classes ====

class User:
    def __init__(self, _id, name, email, nickname, avatar):
        self.id = _id
        self.name = name
        self.email = email
        self.nickname = nickname
        self.avatar = avatar

        self.groups = []

    def __repr__(self):
        return '<User %r>' % self.name

    def to_dict(self):
        return dict(id=self.id, name=self.name, email=self.email, nickname=self.nickname, avatar=self.avatar,
                    groups=[group.to_dict() for group in self.groups])


class Group:
    def __init__(self, _id, name, description):
        self.id = _id
        self.name = name
        self.description = description

    def __repr__(self):
        return '<Group %r>' % self.name

    def to_dict(self):
        return dict(id=self.id, name=self.name, description=self.description)


# ==== Internal Callbacks ====
_login_callback = None


# ==== Helper functions ====

def _error_html(msg, detail=None):
    if detail is None:
        detail = ''
    return "<html><body><h1>%s</h1><p>%s</p></body></html>" % (str(msg), str(detail))


def _preferred_mime():
    mimes = request.accept_mimetypes
    for mime in mimes:
        if mime[0] == 'text/html':
            return mime[0]
        if mime[0] == 'application/json':
            return mime[0]
    return 'text/html'


def _build_redirect_url(original_path, state):
    config = current_app.config.get(_config_key)
    config_server = config['server']
    config_client = config['client']
    params = {
        'client_id': config_client['id'],
        'redirect_url': config_client['url'] + config_client['callback_path']
    }
    if original_path:
        params['original_path'] = original_path
    if state:
        params['state'] = state
    redirect_url = config_server['url'] + config_server['connect_page']
    return redirect_url + '?' + urlencode(params)


def _build_error_response(error: OAuthError, original_path=None, previous_state=None):
    mime = _preferred_mime()
    if isinstance(error, (OAuthRequired, OAuthRequestError)) \
            and previous_state not in ['new_request', 'request_error']:  # avoid infinite redirect
        if isinstance(error, OAuthRequired):
            state = 'new_request'
        else:
            state = 'request_error'
        redirect_url = _build_redirect_url(original_path=original_path, state=state)
        if mime == 'text/html':
            return redirect(redirect_url)
        else:
            return jsonify(msg=error.msg, detail=error.detail, redirect_url=redirect_url), 401
    else:
        if mime == 'text/html':
            return _error_html(error.msg, error.detail), 500
        else:
            return jsonify(msg=error.msg, detail=error.detail), 500


def _is_oauth_skipped():
    config = current_app.config.get(_config_key)

    # if disabled
    if not config.get('enabled'):
        return True

    whitelist = config.get('whitelist')
    if whitelist:  # need to check if the client ip is in whitelist
        # if need real ip (when using a reverse-proxy like nginx)
        if config.get('resolve_real_ip'):
            ip = request.environ.get('HTTP_X_REAL_IP') or request.remote_addr
        else:
            ip = request.remote_addr
        # if whitelisted
        if ip in whitelist:
            return True

    return False


def _get_original_path():
    if _preferred_mime() == 'text/html':
        return request.full_path.rstrip('?')
    else:
        referrer = request.referrer  # use the referer page rather than the URL for the current request
        config = current_app.config.get(_config_key)
        config_client = config['client']
        client_url_prefix = config_client['url'].rstrip('/')
        if referrer and referrer.startswith(client_url_prefix):
            path = referrer[len(client_url_prefix):]
            if not path:
                return '/'
            if path[0] != '/':
                return None  # invalid path
            return path
        else:
            return None  # cannot find a reliable one


# ==== Parsers ====

def _parse_response_error(response):
    try:
        data = json.loads(response.text)
        msg = data.get('msg')  # check if it has expected error message format
        if int(response.status_code / 100) == 4:  # 4xx
            return OAuthRequestError(msg=msg, detail=data.get('detail'))
        return OAuthAPIError(msg=msg, detail=data.get('detail'))
    except (ValueError, KeyError):
        return OAuthAPIError(msg='Status %d' % response.status_code, detail=response.text)


def _parse_user(_dict):
    if not _dict:
        raise OAuthResultError('empty user body')
    user = User(_dict.get('id'), _dict.get('name'), _dict.get('email'), _dict.get('nickname'), _dict.get('avatar'))
    if user.id is None:
        raise OAuthResultError('user id is missing')
    if type(user.id) != int:
        raise OAuthResultError('user id should be an integer')
    if not user.name:
        raise OAuthResultError('user name is missing or empty')
    if not user.email:
        raise OAuthResultError('user email is missing or empty')

    config = current_app.config.get(_config_key)
    config_server = config['server']
    server_url = config_server['url']

    # fix prefix for avatars
    if user.avatar and not user.avatar.startswith('http://') and not user.avatar.startswith('https://'):
        user.avatar = server_url + '/' + user.avatar.lstrip('/')

    group_dicts = _dict.get('groups')
    if group_dicts:
        for group_dict in group_dicts:
            user.groups.append(_parse_group(group_dict))
    return user


def _parse_group(_dict):
    if not _dict:
        raise OAuthResultError('empty group body')
    group = Group(_dict.get('id'), _dict.get('name'), _dict.get('description'))
    if group.id is None:
        raise OAuthResultError('group id is missing')
    if type(group.id) != int:
        raise OAuthResultError('group id should be an integer')
    if not group.name:
        raise OAuthResultError('group name is missing or empty')
    return group


# ==== API requests ====

def _request_access_token(authorization_token):
    if not authorization_token:
        raise OAuthRequestError('authorization token is required')

    config = current_app.config.get(_config_key)
    config_server = config['server']
    config_client = config['client']

    params = {
        'client_id': config_client['id'],
        'client_secret': config_client['secret'],
        'redirect_url': config_client['url'] + config_client['callback_path'],
        'token': authorization_token
    }

    try:
        response = requests.post(config_server['url'] + config_server['token_api'], params)
    except IOError:
        raise OAuthAPIError('failed to access OAuth API (access token)')

    if response.status_code != 200:
        raise _parse_response_error(response)
    try:
        data = response.json()
    except ValueError:
        raise OAuthResultError('invalid data format (token)')

    token = data.get('access_token')
    if not token:
        raise OAuthResultError('access_token is missing or empty')
    return token


def _request_resource(path, access_token, method='get', **kwargs):
    if not access_token:
        raise OAuthRequestError('access token is required')
    config = current_app.config.get(_config_key)
    config_server = config['server']
    if 'params' in kwargs:
        params = dict(kwargs['params'])
    else:
        params = {}
    params['oauth_token'] = access_token
    try:
        response = requests.request(method, config_server['url'] + path, params=params, **kwargs)
    except IOError:
        raise OAuthAPIError('failed to access OAuth API')
    if response.status_code // 100 != 2:
        raise _parse_response_error(response)
    return response


def _request_resource_json(path, access_token, method='get', **kwargs):
    response = _request_resource(path, access_token, method, **kwargs)
    try:
        return response.json()
    except ValueError:
        raise OAuthResultError('invalid data format')


def _request_oauth_user(access_token):
    config = current_app.config.get(_config_key)
    config_server = config['server']
    data = _request_resource_json(config_server['profile_api'], access_token)
    return _parse_user(data)


# ==== other private stuff ====

def _get_access_token():
    token = session.get(_session_access_token_key)
    if token is None:
        clear_user()
        raise OAuthRequired()
    return token


# ==== Register Endpoints ====

def _oauth_callback():
    config = current_app.config.get(_config_key)
    config_client = config['client']

    args = request.args
    token = args.get('token')
    state = args.get('state')
    original_path = args.get('original_path')

    try:
        access_token = _request_access_token(token)
        user = _request_oauth_user(access_token)

        session[_session_uid_key] = user.id
        session[_session_access_token_key] = access_token

        if original_path:
            if original_path[0] != '/':
                original_path = '/' + original_path  # ensure URL to self
        else:
            original_path = '/'
        return redirect(config_client['url'].rstrip('/') + original_path)
    except OAuthError as e:
        return _build_error_response(e, original_path, state)


# ==== public decorators ====

def requires_login(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            user = get_user()  # will return None if OAuth is skipped
            if user and _login_callback:
                ret = _login_callback(user)
                if ret is not None:
                    return ret
            return f(*args, **kwargs)
        except OAuthError as e:
            return _build_error_response(e, _get_original_path())

    return wrapped


def requires_admin(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            user = get_user()  # will return None if OAuth is skipped
            if user and _login_callback:
                ret = _login_callback(user)
                if ret is not None:
                    return ret
            if user is None:
                return jsonify(msg='user info required'), 401
            is_admin = False
            for group in user.groups:
                if group.name == _admin_group_name:
                    is_admin = True
                    break
            if not is_admin:
                return jsonify(msg='admin required'), 403
            return f(*args, **kwargs)
        except OAuthError as e:
            return _build_error_response(e, _get_original_path())

    return wrapped


# ==== public functions ====

def get_uid() -> [int, None]:
    """
    Get UID stored in session.
    """
    return session.get(_session_uid_key)


def get_user() -> [User, None]:
    """
    Get User with access token stored in session.

    Call this inside a function protected by @requires_login. Otherwise, you need to handle possible exceptions.
    It returns None only if OAuth is skipped (disabled or whitelisted).
    """
    if _is_oauth_skipped():
        return None
    user = g.get(_request_user_key)
    if user is not None:
        return user
    uid = get_uid()
    if uid is None:
        clear_user()
        raise OAuthRequired()
    access_token = _get_access_token()
    user = _request_oauth_user(access_token)
    setattr(g, _request_user_key, user)
    return user


def clear_user() -> None:
    """
    Remove all the OAuth data in session.
    """
    if _request_user_key in g:
        g.pop(_request_user_key)
    if _session_uid_key in session:
        del session[_session_uid_key]
    if _session_access_token_key in session:
        del session[_session_access_token_key]


def get_users() -> List[User]:
    config = current_app.config.get(_config_key)
    data = _request_resource_json(config['server']['admin_users_api'], _get_access_token())
    user_dicts = data['users']
    group_dicts = data['groups']
    groups = {_g['id']: _parse_group(_g) for _g in group_dicts}
    users = []
    for u in user_dicts:
        user = _parse_user(u)
        for gid in u['group_ids']:
            user.groups.append(groups[gid])
        users.append(user)
    return users


def get_groups() -> List[Group]:
    config = current_app.config.get(_config_key)
    data = _request_resource_json(config['server']['admin_groups_api'], _get_access_token())
    return [_parse_group(_g) for _g in data]


def add_group(name, description=None) -> Group:
    config = current_app.config.get(_config_key)
    group_data = {
        'name': name,
        'description': description
    }
    data = _request_resource_json(config['server']['admin_groups_api'], _get_access_token(), method='post',
                                  json=group_data)
    return _parse_group(data)


def init_app(app: Flask, config_file: str = 'oauth.config.json', login_callback=None) -> None:
    """
    Initialize OAuth configurations and callbacks in the provided Flask app
    :param app: Your Flask app
    :param config_file: The path to a configuration file for OAuth
    :param login_callback: (optional) a callback function to call after successful login
    """
    global _login_callback
    with open(config_file) as f:
        config = json.load(f)
        app.config[_config_key] = config
    server_config = config['server']
    client_config = config['client']
    server_url = server_config['url']
    app.add_url_rule(client_config['callback_path'], None, _oauth_callback)
    app.add_url_rule(client_config['profile_path'], 'account_profile',
                     lambda: redirect(server_url + server_config['profile_page']))
    app.add_url_rule(client_config['admin_user_path'], 'admin_user',
                     lambda uid: redirect(server_url + server_config['admin_user_page'].format(uid=uid)))
    app.add_url_rule(client_config['admin_group_path'], 'admin_group',
                     lambda gid: redirect(server_url + server_config['admin_group_page'].format(gid=gid)))
    _login_callback = login_callback

# TODO connect via API? --> avoid infinite loop && CORS issues
# TODO automatically update access token?
