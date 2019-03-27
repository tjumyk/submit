import ast
import logging
import os
import sys
from typing import Optional, Tuple, Dict, List

import astunparse
import magic

from utils.upload import md5sum

logger = logging.getLogger(__name__)


class CodeSegment:
    def __init__(self, dump: str, node, height: int, total_nodes: int):
        self.dump = dump

        # for convenience only
        self.node = node
        self.height = height
        self.total_nodes = total_nodes

    def __repr__(self):
        return repr(self.dump)

    def __eq__(self, other):
        if not isinstance(other, CodeSegment):
            return False
        return self.dump == other.dump

    def __hash__(self):
        return self.dump.__hash__()

    def to_dict(self) -> dict:
        return dict(code=astunparse.unparse(self.node), height=self.height, total_nodes=self.total_nodes)


class CodeOccurrence:
    def __init__(self, user_id, file_id, file_md5: str, lineno: Optional[int], col_offset: Optional[int]):
        self.user_id = user_id
        self.file_id = file_id
        self.file_md5 = file_md5
        self.lineno = lineno
        self.col_offset = col_offset

    def __repr__(self):
        return '<CodeOccurrence user=%s, file=%s, md5=%s, line=%s, col=%s>' % \
               (self.user_id, self.file_id, self.file_md5, self.lineno, self.col_offset)

    def to_dict(self) -> dict:
        return dict(user_id=self.user_id, file_id=self.file_id, file_md5=self.file_md5, lineno=self.lineno,
                    col_offset=self.col_offset)


class CodeSegmentIndex:
    def __init__(self, min_index_height: int):
        self._min_index_height = min_index_height
        self._index = {}

    def _put(self, segment: CodeSegment, occurrence: CodeOccurrence):
        occ_users = self._index.get(segment)
        if occ_users is None:
            self._index[segment] = occ_users = {}
        occ_user_items = occ_users.get(occurrence.user_id)
        if occ_user_items is None:
            occ_users[occurrence.user_id] = occ_user_items = []
        occ_user_items.append(occurrence)

    def process_code(self, user_id, file_id, code: str, file_md5: str):
        def _iterate_node(node):
            height = 1
            total_nodes = 1
            if isinstance(node, ast.AST):
                fields = []
                for a, b in ast.iter_fields(node):
                    node_dump, node_height, node_total_nodes = _iterate_node(b)
                    fields.append((a, node_dump))
                    height = max(height, node_height + 1)
                    total_nodes += node_total_nodes
                dump = '%s(%s)' % (node.__class__.__name__, ', '.join(b for a, b in fields))

                lineno = None
                col_offset = None
                if node._attributes:
                    for a in node._attributes:
                        node_dump, node_height, node_total_nodes = _iterate_node(getattr(node, a))
                        if a == 'lineno':
                            lineno = node_dump
                        elif a == 'col_offset':
                            col_offset = node_dump
                if height >= self._min_index_height:
                    self._put(CodeSegment(dump, node, height, total_nodes),
                              CodeOccurrence(user_id, file_id, file_md5, lineno, col_offset))
            elif isinstance(node, list):
                items = []
                for x in node:
                    node_dump, node_height, node_total_nodes = _iterate_node(x)
                    items.append(node_dump)
                    height = max(height, node_height + 1)
                    total_nodes += node_total_nodes
                dump = '[%s]' % ', '.join(items)
                if height >= self._min_index_height:
                    self._put(CodeSegment(dump, node, height, total_nodes),
                              CodeOccurrence(user_id, file_id, file_md5, None, None))
            else:
                dump = repr(node)
                if height >= self._min_index_height:
                    self._put(CodeSegment(dump, node, height, total_nodes),
                              CodeOccurrence(user_id, file_id, file_md5, None, None))

            return dump, height, total_nodes

        root = ast.parse(code)
        _iterate_node(root)

    def process_file(self, user_id, file_id, file_path: str, file_md5: str = None):
        with open(file_path, 'rb') as f:
            buffer = f.read()
        encoding = magic.Magic(mime_encoding=True).from_buffer(buffer)
        if encoding == 'binary':
            raise IOError('binary file detected: uid=%s, fid/sid=%s, path=%s' % (user_id, file_id, file_path))
        try:
            code = buffer.decode(encoding)
        except (ValueError, LookupError):
            raise IOError('failed to decode file with %s encoding: uid=%s, fid/sid=%s, path=%s'
                          % (encoding, user_id, file_id, file_path))
        if not file_md5:  # if no md5 given, compute it now
            file_md5 = md5sum(file_path)
        self.process_code(user_id, file_id, code, file_md5)

    def get_duplicates(self, min_occ_users: int = 2, max_occ_users: int = None,
                       min_total_nodes: int = None, max_total_nodes: int = None,
                       min_height: int = None, max_height: int = None,
                       sort_by: str = 'total_nodes',
                       filter_user_id: int = None, filter_file_id: int = None):
        results = []
        for k, v in self._index.items():
            if min_height is not None and k.height < min_height:
                continue
            if max_height is not None and k.height > max_height:
                continue
            if min_total_nodes is not None and k.total_nodes < min_total_nodes:
                continue
            if max_total_nodes is not None and k.total_nodes > max_total_nodes:
                continue
            occ_users = len(v)
            if min_occ_users is not None and occ_users < min_occ_users:
                continue
            if max_occ_users is not None and occ_users > max_occ_users:
                continue

            if filter_user_id is not None:
                user_occurrences = v.get(filter_user_id)
                if user_occurrences is None:
                    continue
                if filter_file_id is None and not any(occ.file_id == filter_file_id for occ in user_occurrences):
                    continue
            else:
                if filter_file_id is not None:
                    logger.warning('parameter "filter_file_id" is ignored when "filter_user_id" is not provided')

            results.append((k, v))
        results.sort(key=lambda x: getattr(x[0], sort_by), reverse=True)
        return results

    @staticmethod
    def result_to_dict(result: Tuple[CodeSegment, Dict[int, List[CodeOccurrence]]]) -> Dict:
        segment, occ_users = result
        return dict(segment=segment.to_dict(),
                    occurrences={uid: [occ.to_dict() for occ in user_occurrences] for uid, user_occurrences in
                                 occ_users.items()})

    @staticmethod
    def pretty_print_result(result, file=sys.stdout):
        segment, occ_users = result
        print('%-18s%-22s%-8s%s' % ('User/Team ID', 'File/Submission ID', 'MD5', 'Location'), file=file)
        for uid, occ_user_items in occ_users.items():
            print(uid, file=file)
            for occ in occ_user_items:
                md5_short = occ.file_md5[:6] if occ.file_md5 else occ.file_md5
                print('%-18s%-22s%-8sLine %s, Col %s' % ('', occ.file_id, md5_short, occ.lineno, occ.col_offset),
                      file=file)
        print('AST Nodes: %d, Height: %d' % (segment.total_nodes, segment.height), file=file)
        print(astunparse.unparse(segment.node), file=file)

    @classmethod
    def pretty_print_results(cls, results, file=sys.stdout):
        print('Total Results: %d' % len(results), file=file)
        for i, r in enumerate(results):
            print('--------------------------- #%-2s ---------------------------' % (i + 1), file=file)
            cls.pretty_print_result(r, file=file)


def test_process_submissions(task_id: int, requirement_id: int, min_index_height: int):
    from models import SubmissionFile, db, Submission
    from server import app
    with app.test_request_context():
        index = CodeSegmentIndex(min_index_height=min_index_height)
        data_folder = app.config['DATA_FOLDER']
        user_set = set()
        valid_file_count = 0
        syntax_error_count = 0
        for sid, uid, path in db.session.query(Submission.id, Submission.submitter_id, SubmissionFile.path) \
                .filter(SubmissionFile.requirement_id == requirement_id,
                        SubmissionFile.submission_id == Submission.id,
                        Submission.task_id == task_id) \
                .all():
            user_set.add(uid)
            try:
                index.process_file(uid, sid, os.path.join(data_folder, path))
            except SyntaxError:
                logger.warning('Syntax Error in (uid: %s, sid: %s)' % (uid, sid))
                syntax_error_count += 1
                continue
            valid_file_count += 1
        logger.info('Processed users: %d, valid files: %d, syntax errors: %d' %
                    (len(user_set), valid_file_count, syntax_error_count))
        return index


def test():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    index = test_process_submissions(1, 1, 5)
    results = index.get_duplicates(max_occ_users=100)
    index.pretty_print_results(results)


if __name__ == '__main__':
    test()
