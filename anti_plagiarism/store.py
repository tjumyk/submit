import logging
import os
import sys
from threading import Lock
from typing import List, Tuple, Dict

from anti_plagiarism.code_analysis import CodeSegmentIndex, CodeFileInfo, CodeSegment, CodeOccurrence
from models import SubmissionFile
from services.submission import SubmissionService

logger = logging.getLogger(__name__)


class Store:
    """
    Thread-safe in-memory index store for a requirement.
    """

    def __init__(self, requirement_id: int, is_team_task: bool, data_folder: str):
        self.requirement_id = requirement_id
        self.is_team_task = is_team_task
        self.data_folder = data_folder

        self._template_path = None
        self._template_md5 = None
        self._template_uid = -1
        self._template_sid = -1

        self._lock = Lock()
        self._indexed_file_ids = set()
        self._index = None

    def add_file(self, sid: int, uid: int, file: SubmissionFile):
        with self._lock:
            if self._index is None:  # cold start
                self._index = self._build_full_index()  # should include the current submission
            else:  # assume this submission is the only submission that has not been indexed
                if file.id in self._indexed_file_ids:
                    return
                try:
                    self._index.process_file(uid, sid, os.path.join(self.data_folder, file.path), file.md5)
                except SyntaxError:
                    logger.debug('Syntax Error in (uid: %s, sid: %s)' % (uid, sid))
                except IOError:
                    logger.warning('IO Error in (uid: %s, sid: %s)' % (uid, sid), exc_info=True)
                self._indexed_file_ids.add(file.id)  # mark it as indexed even error occurred

    def get_duplicates(self, sid: int, uid: int, limit: int = 100, template_path: str = None,
                       template_md5: str = None) -> List[Tuple[CodeSegment, Dict[int, List[CodeOccurrence]]]]:
        with self._lock:
            if template_path:  # enable template
                if not self._template_path or (self._template_path != template_path
                                               or self._template_md5 != template_md5):  # need to index the template
                    if self._template_path:  # need to remove old template from index
                        self._index.remove_code(self._template_uid, self._template_sid)
                    try:
                        self._index.process_file(self._template_uid, self._template_sid,
                                                 os.path.join(self.data_folder, template_path), template_md5)
                    except SyntaxError:
                        logger.warning('Syntax Error in template file: %s' % template_path)
                    except IOError:
                        logger.warning('IO Error in template file: %s' % template_path, exc_info=True)
                    self._template_path = template_path
                    self._template_md5 = template_md5
            else:  # disable template
                if self._template_path is not None:  # need to remove old template from index
                    self._index.remove_code(self._template_uid, self._template_sid)
                    self._template_path = None
                    self._template_md5 = None

        exclude_user_id = self._template_uid if template_path else None
        return self._index.get_duplicates(sort_by='total_nodes', include_user_id=uid, include_user_file_id=sid,
                                          exclude_user_id=exclude_user_id)[:limit]

    def get_file_info(self, sid: int) -> CodeFileInfo:
        return self._index.get_file_info(sid)

    def pretty_print_results(self, results, file=sys.stdout):
        return self._index.pretty_print_results(results, file)

    def _build_full_index(self) -> CodeSegmentIndex:
        index = CodeSegmentIndex()

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
            try:
                index.process_file(uid, sid, os.path.join(self.data_folder, file.path), file.md5)
                valid_file_count += 1
            except SyntaxError:
                logger.debug('Syntax Error in (uid: %s, sid: %s)' % (uid, sid))
                syntax_error_count += 1
            except IOError:
                logger.warning('IO Error in (uid: %s, sid: %s)' % (uid, sid), exc_info=True)
                io_error_count += 1
            self._indexed_file_ids.add(file.id)  # mark it as indexed even error occurred
        logger.info('Built full index for requirement %d. '
                    'users/teams: %d, valid files: %d, syntax errors: %d, io errors: %d' %
                    (self.requirement_id, len(user_set), valid_file_count, syntax_error_count, io_error_count))
        return index
