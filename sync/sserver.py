import json
import logging
import os
from threading import Lock

from flask import Flask, request, jsonify

from models import db, Task
from services.task import TaskServiceError
from sync.smodel import TeamData
from sync.sservice import SyncService, SubmissionData, SyncServiceError

app = Flask(__name__)
app.config.from_json('../config.json')
db.init_app(app)

logger = logging.getLogger(__name__)

_sync_state = {
}

_sync_state_file_name = 'sync_state.json'
if os.path.exists(_sync_state_file_name):
    with open(_sync_state_file_name) as _f_sync:
        _sync_state = json.load(_f_sync)

_lock = Lock()


def _save_state():
    with open(_sync_state_file_name, 'w') as f_sync:
        json.dump(_sync_state, f_sync, indent=2)


@app.route('/')
def index_page():
    return '<h1>submit sync server</h1>'


@app.route('/api/terms/<int:term_id>/tasks/<string:task_title>/submissions/diff', methods=['POST'])
def diff_submissions(term_id, task_title):
    try:
        task = db.session.query(Task).filter(Task.term_id == term_id, Task.title == task_title).first()
        if task is None:
            return jsonify(msg='task %s not found' % task_title), 404

        result = SyncService.diff_submissions(task, request.json)
        return jsonify(result)
    except TaskServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


@app.route('/api/terms/<int:term_id>/tasks/<string:task_title>/submissions', methods=['POST'])
def import_submissions(term_id, task_title):
    try:
        task = db.session.query(Task).filter(Task.term_id == term_id, Task.title == task_title).first()
        if task is None:
            return jsonify(msg='task %s not found' % task_title), 404

        submissions = SyncService.import_submissions(task, [SubmissionData.from_dict(d) for d in request.json])
        return jsonify(imported=len(submissions))
    except (TaskServiceError, SyncServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


@app.route('/api/terms/<int:term_id>/tasks/<string:task_title>/teams', methods=['POST'])
def import_teams(term_id, task_title):
    try:
        task = db.session.query(Task).filter(Task.term_id == term_id, Task.title == task_title).first()
        if task is None:
            return jsonify(msg='task %s not found' % task_title), 404

        teams = SyncService.import_teams(task, [TeamData.from_dict(d) for d in request.json])
        return jsonify(imported=len(teams))
    except (TaskServiceError, SyncServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


if __name__ == '__main__':
    app.run(host='localhost', port=6202)
