import json
import logging
import os
import sys
from io import StringIO
from threading import Lock
from typing import List, Tuple, Dict

from flask import Flask, request, jsonify

from anti_plagiarism.code_analysis import CodeSegmentIndex, CodeFileInfo, CodeSegment, CodeOccurrence
from models import SubmissionFile, Task
from server import app
from services.submission import SubmissionService, SubmissionServiceError
from services.task import TaskService, TaskServiceError
from services.team import TeamService, TeamServiceError

ap_server = Flask(__name__)

logger = logging.getLogger(__name__)
data_folder = app.config['DATA_FOLDER']

GRADE_NO_EVIDENCE = 0
GRADE_WEAK_EVIDENCE = 1
GRADE_MODERATE_EVIDENCE = 2
GRADE_STRONG_EVIDENCE = 3
GRADE_VERY_STRONG_EVIDENCE = 3
GRADE_EXACTLY_SAME = 4

GRADE_MESSAGES = {GRADE_NO_EVIDENCE: 'No Evidence',
                  GRADE_WEAK_EVIDENCE: 'Weak Evidence',
                  GRADE_MODERATE_EVIDENCE: 'Moderate Evidence',
                  GRADE_STRONG_EVIDENCE: 'Strong Evidence',
                  GRADE_VERY_STRONG_EVIDENCE: 'Very Strong Evidence',
                  GRADE_EXACTLY_SAME: 'Exactly the Same'}


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

    def get_duplicates(self, sid: int, uid: int, limit: int = 100) \
            -> List[Tuple[CodeSegment, Dict[int, List[CodeOccurrence]]]]:
        # TODO accept configurable options
        options = {}
        if self.template_path:
            options['exclude_user_id'] = self._template_uid
        return self._index.get_duplicates(sort_by='total_nodes', include_user_id=uid, include_user_file_id=sid,
                                          **options)[:limit]

    def get_file_info(self, sid: int) -> CodeFileInfo:
        return self._index.get_file_info(sid)

    def pretty_print_results(self, results, file=sys.stdout):
        return self._index.pretty_print_results(results, file)

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
            duplicates = store.get_duplicates(submission_id, uid)

            summary = build_summary(store, task, uid, submission_id, duplicates)
            with StringIO() as buffer:
                buffer.write(json.dumps(summary))  # dump a JSON summary in the first line
                buffer.write('\n')
                store.pretty_print_results(duplicates, file=buffer)  # then the full report follows
                return buffer.getvalue(), {'Content-Type': 'text/plain'}
    except (TaskServiceError, TeamServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


def build_summary(store: Store, task: Task, uid: int, submission_id: int,
                  duplicates: List[Tuple[CodeSegment, Dict[int, List[CodeOccurrence]]]]):
    info = store.get_file_info(submission_id)
    duplicate_id_set = set()
    duplicate_entries = []
    result_grade = GRADE_NO_EVIDENCE

    max_dup_height = 0
    max_dup_total_nodes = 0

    for segment, dup in duplicates:
        for _uid, user_occurrences in dup.items():
            for occ in user_occurrences:
                ids = (_uid, occ.file_id)
                if ids == (uid, submission_id) or ids in duplicate_id_set:
                    continue
                duplicate_id_set.add(ids)

                _info = store.get_file_info(occ.file_id)
                entry = dict(submission_id=occ.file_id)
                if task.is_team_task:
                    entry['team_id'] = _uid
                else:
                    entry['user_id'] = _uid
                if _info:
                    entry['md5'] = _info.md5
                duplicate_entries.append(entry)

                if info and _info and info.md5 == _info.md5:
                    result_grade = max(result_grade, GRADE_EXACTLY_SAME)
                max_dup_height = max(max_dup_height, segment.height)
                max_dup_total_nodes = max(max_dup_total_nodes, segment.total_nodes)

    if info:
        max_coverage = max(max_dup_height / info.ast_height, max_dup_total_nodes / info.ast_total_nodes)
        if max_coverage == 1:
            result_grade = max(result_grade, GRADE_EXACTLY_SAME)
        elif max_coverage > 0.8:
            result_grade = max(result_grade, GRADE_VERY_STRONG_EVIDENCE)
        elif max_coverage > 0.6:
            result_grade = max(result_grade, GRADE_STRONG_EVIDENCE)
        elif max_coverage > 0.4:
            result_grade = max(result_grade, GRADE_MODERATE_EVIDENCE)
        elif max_coverage > 0.2:
            result_grade = max(result_grade, GRADE_WEAK_EVIDENCE)
    else:
        logger.warning('coverage test skipped due to missing file info (uid=%s, sid=%s)' % (uid, submission_id))

    return dict(total_collide_files=len(duplicate_entries),
                total_collisions=len(duplicates),
                collide_files=duplicate_entries,
                result=GRADE_MESSAGES[result_grade])


if __name__ == '__main__':
    ap_server.run(host='localhost', port=6322)
