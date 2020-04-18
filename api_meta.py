import json
import subprocess
import time

from flask import Blueprint, jsonify

from auth_connect.oauth import requires_login

meta_api = Blueprint('meta_api', __name__)


@meta_api.route('/version')
@requires_login
def get_version():
    git_commit = subprocess.check_output(["git", "describe", "--tags"]).decode().strip()

    return jsonify(commit=git_commit)


@meta_api.route('/faq')
@requires_login
def get_faq():
    with open('faq.json') as f_faq:
        faq = json.load(f_faq)
    return jsonify(faq)


@meta_api.route('/clock')
@requires_login
def get_clock():
    return jsonify(time=time.time())
