import json
import logging
from io import StringIO
from threading import Lock
from typing import List, Tuple, Dict

from flask import Flask, request, jsonify

from anti_plagiarism.code_analysis import CodeFileInfo, CodeSegment, CodeOccurrence
from anti_plagiarism.store import Store
from models import Task
from server import app
from services.submission import SubmissionService, SubmissionServiceError
from services.task import TaskService, TaskServiceError
from services.team import TeamService, TeamServiceError

ap_server = Flask(__name__)

logger = logging.getLogger(__name__)

GRADE_NO_EVIDENCE = 0
GRADE_WEAK_EVIDENCE = 1
GRADE_MODERATE_EVIDENCE = 2
GRADE_STRONG_EVIDENCE = 3
GRADE_VERY_STRONG_EVIDENCE = 4
# FULL_COPY means the (normalised) code of the whole file is copied from another file but it is possible that only part
# of that file is copied.
GRADE_FULL_COPY = 5
# SAME_CODE means the two collided files have identical (normalised) code.
GRADE_SAME_CODE = 6
# SAME_FILE means the two collided files have identical content (same MD5).
GRADE_SAME_FILE = 7

GRADE_MESSAGES = {GRADE_NO_EVIDENCE: 'No Evidence',
                  GRADE_WEAK_EVIDENCE: 'Weak Evidence',
                  GRADE_MODERATE_EVIDENCE: 'Moderate Evidence',
                  GRADE_STRONG_EVIDENCE: 'Strong Evidence',
                  GRADE_VERY_STRONG_EVIDENCE: 'Very Strong Evidence',
                  GRADE_FULL_COPY: 'Full Copy',
                  GRADE_SAME_CODE: 'Same Code',
                  GRADE_SAME_FILE: 'Same File'}

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
        template_file_id = request.args.get('tid')
        if template_file_id is not None:
            template_file_id = int(template_file_id)

        with app.test_request_context():
            submission = SubmissionService.get(submission_id)
            if submission is None:
                return jsonify(msg='submission not found'), 404
            requirement = TaskService.get_file_requirement(requirement_id)
            if requirement is None:
                return jsonify(msg='requirement not found'), 404
            if template_file_id is not None:
                template_file = TaskService.get_material(template_file_id)
                if template_file is None:
                    return jsonify(msg='template file not found'), 404
            else:
                template_file = None
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
                return jsonify(conclusion='Skipped', reason='File not submitted')

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
                    # Currently, only allow one store in memory. TODO: use a queue to manage in-memory stores
                    _stores_map.clear()
                    _stores_map[requirement.id] = store = Store(requirement.id, task.is_team_task,
                                                                app.config['DATA_FOLDER'])

            store.add_file(submission_id, uid, file)
            file_info = store.get_file_info(submission_id)
            if file_info is None:  # failed to process file, e.g. syntax/io error
                return jsonify(conclusion='Skipped', reason='File syntax or IO error')

            if template_file:
                duplicates = store.get_duplicates(submission_id, uid, template_path=template_file.file_path,
                                                  template_md5=template_file.md5)
            else:
                duplicates = store.get_duplicates(submission_id, uid)

            summary = build_summary(store, task, uid=uid, info=file_info, duplicates=duplicates)
            with StringIO() as buffer:
                buffer.write(json.dumps(summary))  # dump a JSON summary in the first line
                buffer.write('\n')
                store.pretty_print_results(duplicates, file=buffer)  # then the full report follows
                return buffer.getvalue(), {'Content-Type': 'text/plain'}
    except (TaskServiceError, TeamServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


def build_summary(store: Store, task: Task, uid: int, info: CodeFileInfo,
                  duplicates: List[Tuple[CodeSegment, Dict[int, List[CodeOccurrence]]]]):
    duplicate_user_set = set()
    duplicate_users = []  # to keep a order
    duplicate_id_set = set()
    duplicate_entries = []  # to keep a order
    max_coverage = 0
    conclusion_grade = GRADE_NO_EVIDENCE

    for segment, dup in duplicates:
        coverage = segment.total_nodes / info.ast_total_nodes
        coverage_grade = get_grade_from_coverage(coverage)
        max_coverage = max(max_coverage, coverage)

        for _uid, user_occurrences in dup.items():
            if _uid == uid:
                continue
            if _uid not in duplicate_user_set:
                duplicate_users.append(_uid)
                duplicate_user_set.add(_uid)

            for occ in user_occurrences:
                ids = (_uid, occ.file_id)  # note occ.file_id is actually submission_id
                if ids in duplicate_id_set:
                    continue
                duplicate_id_set.add(ids)

                _info = store.get_file_info(occ.file_id)
                entry = dict(submission_id=occ.file_id)
                entry['coverage'] = round(coverage * 100) / 100
                if task.is_team_task:
                    entry['team_id'] = _uid
                else:
                    entry['user_id'] = _uid
                if _info:
                    entry['md5'] = _info.md5

                file_grade = coverage_grade
                if _info:
                    if info.md5 == _info.md5:
                        file_grade = max(file_grade, GRADE_SAME_FILE)
                    if info.ast_total_nodes == _info.ast_total_nodes == segment.total_nodes:
                        file_grade = max(file_grade, GRADE_SAME_CODE)
                else:
                    logger.warning('missing file info (uid=%s, sid=%s)' % (_uid, occ.file_id))

                entry['grade'] = GRADE_MESSAGES[file_grade]
                duplicate_entries.append(entry)
                conclusion_grade = max(conclusion_grade, file_grade)

    max_coverage = round(max_coverage * 100) / 100
    summary = dict(total_collisions=len(duplicates),
                   total_collided_files=len(duplicate_entries),
                   collided_files=duplicate_entries,
                   coverage=max_coverage,
                   conclusion=GRADE_MESSAGES[conclusion_grade])
    if task.is_team_task:
        summary['total_collided_teams'] = len(duplicate_users)
        summary['collided_teams'] = duplicate_users
    else:
        summary['total_collided_users'] = len(duplicate_users)
        summary['collided_users'] = duplicate_users
    return summary


def get_grade_from_coverage(coverage: float):
    if coverage == 1:
        return GRADE_FULL_COPY
    elif coverage > 0.9:
        return GRADE_VERY_STRONG_EVIDENCE
    elif coverage > 0.6:
        return GRADE_STRONG_EVIDENCE
    elif coverage > 0.3:
        return GRADE_MODERATE_EVIDENCE
    elif coverage > 0:
        return GRADE_WEAK_EVIDENCE
    return GRADE_NO_EVIDENCE


if __name__ == '__main__':
    ap_server.run(host='localhost', port=6322)
