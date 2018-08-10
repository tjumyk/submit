from flask import Flask, request, jsonify

import oauth
from api_account import account_api
from api_admin import admin_api
from api_course import course_api
from api_material import material_api
from api_task import task_api
from api_team import team_api
from api_term import term_api
from models import db
from services.account import AccountService, AccountServiceError
from utils import upload

app = Flask(__name__)
app.config.from_json('config.json')

db.init_app(app)
upload.init_app(app)


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
app.register_blueprint(admin_api, url_prefix='/api/admin')


@app.route('/')
@app.route('/terms/<path:path>')
@app.route('/admin/<path:path>')
@oauth.requires_login
def get_index_page(path=''):
    return app.send_static_file('index.html')


@app.errorhandler(404)
def page_not_found(error):
    for mime in request.accept_mimetypes:
        if mime[0] == 'text/html':
            break
        if mime[0] == 'application/json':
            return jsonify(msg='wrong url', detail='You have accessed an unknown location'), 404
    return app.send_static_file('index.html'), 404


@app.cli.command()
def create_db():
    db.create_all()


@app.cli.command()
def drop_db():
    db.drop_all()


if __name__ == '__main__':
    app.run(host='localhost', port=8888)
