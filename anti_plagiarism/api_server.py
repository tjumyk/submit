import logging
import os
from io import StringIO
from threading import Lock

from flask import Flask, request, jsonify

from anti_plagiarism.code_analysis import CodeSegmentIndex
from models import SubmissionFile
from server import app
from services.submission import SubmissionService, SubmissionServiceError
from services.task import TaskService, TaskServiceError
from services.team import TeamService, TeamServiceError

ap_server = Flask(__name__)

logger = logging.getLogger(__name__)
data_folder = app.config['DATA_FOLDER']


class Store:
    """
    Thread-safe in-memory index store for a requirement.
    """

    def __init__(self, requirement_id: int, is_team_task: bool, template_path: str = None):
        self.requirement_id = requirement_id
        self.is_team_task = is_team_task
        self.template_path = template_path

        self._template_sid = -1
        self._template_uid = -1
        self._lock = Lock()
        self._indexed_file_ids = set()
        self._index = None

    def add_file(self, sid: int, uid: int, file: SubmissionFile):
        with self._lock:
            if self._index is None:  # cold start
                self._index = self._build_full_index()
                if self.template_path:  # also index the template file
                    try:
                        self._index.process_file(self._template_uid, self._template_sid,
                                                 os.path.join(data_folder, self.template_path))
                    except SyntaxError:
                        logger.warning('Syntax Error in template file')
                    except IOError:
                        logger.warning('IO Error in template file', exc_info=True)
            else:  # assume this submission is the only submission that has not been indexed
                if file.id in self._indexed_file_ids:
                    return
                try:
                    self._index.process_file(uid, sid, os.path.join(data_folder, file.path), file.md5)
                except SyntaxError:
                    logger.debug('Syntax Error in (uid: %s, sid: %s)' % (uid, sid))
                except IOError:
                    logger.warning('IO Error in (uid: %s, sid: %s)' % (uid, sid), exc_info=True)
                self._indexed_file_ids.add(file.id)  # mark it as indexed even error occurred

    def get_duplicates(self, sid: int, uid: int, limit: int = 100):
        # TODO accept configurable options
        options = {}
        if self.template_path:
            options['exclude_user_id'] = self._template_uid
        return self._index.get_duplicates(include_user_id=uid, include_user_file_id=sid, **options)[:limit]

    def _build_full_index(self) -> CodeSegmentIndex:
        index = CodeSegmentIndex(min_index_height=5)

        if self.is_team_task:
            # treat a team as a single 'user' in this module
            file_tuples = SubmissionService.get_team_files(self.requirement_id)
        else:
            file_tuples = SubmissionService.get_files(self.requirement_id)

        user_set = set()
        valid_file_count = 0
        syntax_error_count = 0
        io_error_count = 0
        for sid, uid, file in file_tuples:
            user_set.add(uid)
            self._indexed_file_ids.add(file.id)
            try:
                index.process_file(uid, sid, os.path.join(data_folder, file.path), file.md5)
            except SyntaxError:
                logger.debug('Syntax Error in (uid: %s, sid: %s)' % (uid, sid))
                syntax_error_count += 1
                continue
            except IOError:
                logger.warning('IO Error in (uid: %s, sid: %s)' % (uid, sid), exc_info=True)
                io_error_count += 1
                continue
            valid_file_count += 1
        logger.info('Built full index for requirement %d. '
                    'users/teams: %d, valid files: %d, syntax errors: %d, io errors: %d' %
                    (self.requirement_id, len(user_set), valid_file_count, syntax_error_count, io_error_count))
        return index


_stores_map = {}

_global_lock = Lock()


@ap_server.route('/')
def index_page():
    return '<h1>anti-plagiarism api server</h1>'


@ap_server.route('/api/check')
def check():
    try:
        submission_id = request.args.get('sid')
        if submission_id is None:
            return jsonify(msg='submission id is required'), 400
        submission_id = int(submission_id)
        requirement_id = request.args.get('rid')
        if requirement_id is None:
            return jsonify(msg='requirement id is required'), 400
        requirement_id = int(requirement_id)

        with app.test_request_context():
            submission = SubmissionService.get(submission_id)
            if submission is None:
                return jsonify(msg='submission not found'), 404
            requirement = TaskService.get_file_requirement(requirement_id)
            if requirement is None:
                return jsonify(msg='requirement not found'), 404
            if not requirement.name.endswith('.py'):
                return jsonify(msg='file type not supported'), 400
            if requirement.task_id != submission.task_id:
                return jsonify(msg='submission and requirement are not in the same task'), 400

            task = submission.task
            file = None
            for f in submission.files:
                if f.requirement_id == requirement_id:
                    file = f
                    break
            if file is None:
                return '', 204  # TODO is it a good idea to return nothing?

            if task.is_team_task:
                ass = TeamService.get_team_association(task, submission.submitter)
                if ass is None:
                    return jsonify(msg='user does not have a team (what?)'), 500
                uid = ass.team_id  # treat a team as a single 'user' in this module
            else:
                uid = submission.submitter_id

            with _global_lock:
                store = _stores_map.get(requirement.id)
                if store is None:
                    _stores_map[requirement.id] = store = Store(requirement.id, task.is_team_task)

            store.add_file(submission_id, uid, file)
            results = store.get_duplicates(uid, file.id)
            with StringIO() as buffer:
                CodeSegmentIndex.pretty_print_results(results, file=buffer)
                return buffer.getvalue(), {'Content-Type': 'text/plain'}
    except (TaskServiceError, TeamServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


if __name__ == '__main__':
    ap_server.run(host='localhost', port=6322)
