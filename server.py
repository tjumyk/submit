import os
import re
import json

import click
from flask import Flask, request, jsonify, send_from_directory

from api_account import account_api
from api_admin import admin_api
from api_course import course_api
from api_material import material_api
from api_meta import meta_api
from api_my_submission import my_submission_api
from api_my_team_submission import my_team_submission_api
from api_submission import submission_api
from api_task import task_api
from api_team import team_api
from api_term import term_api
from api_message import message_api
from auth_connect import oauth
from models import db
from services.account import AccountService, AccountServiceError
from services.messsage import MessageService
from utils import upload
from utils.ip import IPTool


class MyFlask(Flask):
    _hashed_static_file_pattern = re.compile(r'^.+\.[a-z0-9]{20}\.\w+$')
    _hashed_static_file_cache_timeout = 365 * 24 * 60 * 60  # 1 year
    _index_page_cache_timeout = 5 * 60  # 5 minutes

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_url_rule(
            self.static_url_path + '_<string:region>/<path:filename>',
            endpoint='region_static',
            view_func=self.send_region_static_file
        )

    def send_static_file(self, filename):
        return self.send_region_static_file(filename, None)

    def send_region_static_file(self, filename, region):
        """Identify hashed static files and send them with a longer cache timeout.
        For 'index.html', send it with a short cache timeout.
        For other static files, the default cache timeout is used.
        """
        if not self.has_static_folder:
            raise RuntimeError('No static folder for this object')
        if filename == 'index.html':
            cache_timeout = self._index_page_cache_timeout
        elif self._hashed_static_file_pattern.fullmatch(filename):
            cache_timeout = self._hashed_static_file_cache_timeout
        else:
            cache_timeout = self.get_send_file_max_age(filename)

        static_folder = self.get_region_static_folder(region)
        return send_from_directory(static_folder, filename, max_age=cache_timeout)

    def get_region_static_folder(self, region):
        if region:  # use the static folder for this region
            static_folder = '%s_%s' % (self.static_folder, region)
        else:  # use default static folder
            static_folder = self.static_folder
        return static_folder

    def get_request_region(self):
        detect_regions = self.config.get('DETECT_REQUEST_REGIONS')
        if detect_regions:
            ip = IPTool.get_client_ip(request)
            country_code = IPTool.get_ip_country(ip)
            if country_code:
                country_code = country_code.lower()
                if country_code in detect_regions:
                    return country_code
        return None


app = MyFlask(__name__)
with open('config.json') as _f_cfg:
    app.config.from_mapping(json.load(_f_cfg))


db.init_app(app)
upload.init_app(app)
IPTool.init_app(app)

# import logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


def _login_callback(user):
    try:
        AccountService.sync_user(user)
        db.session.commit()
    except AccountServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


oauth.init_app(app, login_callback=_login_callback)

app.register_blueprint(account_api, url_prefix='/api/account')
app.register_blueprint(course_api, url_prefix='/api/courses')
app.register_blueprint(term_api, url_prefix='/api/terms')
app.register_blueprint(team_api, url_prefix='/api/teams')
app.register_blueprint(task_api, url_prefix='/api/tasks')
app.register_blueprint(material_api, url_prefix='/api/materials')
app.register_blueprint(submission_api, url_prefix='/api/submissions')
app.register_blueprint(my_submission_api, url_prefix='/api/my-submissions')
app.register_blueprint(my_team_submission_api, url_prefix='/api/my-team-submissions')
app.register_blueprint(message_api, url_prefix='/api/messages')
app.register_blueprint(meta_api, url_prefix='/api/meta')
app.register_blueprint(admin_api, url_prefix='/api/admin')


@app.route('/')
@app.route('/terms/<path:path>')
@app.route('/admin/<path:path>')
@oauth.requires_login
def get_index_page(path=''):
    region = app.get_request_region()
    return app.send_region_static_file('index.html', region)


@app.errorhandler(404)
def page_not_found(error):
    for mime in request.accept_mimetypes:
        if mime[0] == 'text/html':
            break
        if mime[0] == 'application/json':
            return jsonify(msg='wrong url', detail='You have accessed an unknown location'), 404
    region = app.get_request_region()
    # in case we are building the front-end
    if not os.path.exists(os.path.join(app.get_region_static_folder(region), 'index.html')):
        return send_from_directory(app.root_path, 'building.html', max_age=0), 503
    return app.send_region_static_file('index.html', region), 404


@app.cli.command()
def create_db():
    db.create_all()


@app.cli.command()
def init_db():
    MessageService.init_default_channels()
    db.session.commit()


@app.cli.command()
@click.option('-c', '--channel_name')
def init_email_subscriptions(channel_name: str):
    channel = None
    if channel_name is not None:
        channel = MessageService.get_channel_by_name(channel_name)

    for user in AccountService.get_all_users():
        MessageService.init_new_user_subscriptions(user, channel)
    db.session.commit()


@app.cli.command()
def drop_db():
    db.drop_all()


if __name__ == '__main__':
    app.run(host='localhost', port=8888)
