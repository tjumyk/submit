import ast
import logging
import os
import sys
from typing import Optional

import astunparse
import magic

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


class CodeOccurrence:
    def __init__(self, user_id, file_id, lineno: Optional[int], col_offset: Optional[int]):
        self.user_id = user_id
        self.file_id = file_id
        self.lineno = lineno
        self.col_offset = col_offset

    def __repr__(self):
        return '<CodeOccurrence user=%s, file=%s, line=%s, col=%s>' % \
               (self.user_id, self.file_id, self.lineno, self.col_offset)


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

    def process_code(self, user_id, file_id, code: str):
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
                              CodeOccurrence(user_id, file_id, lineno, col_offset))
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
                              CodeOccurrence(user_id, file_id, None, None))
            else:
                dump = repr(node)
                if height >= self._min_index_height:
                    self._put(CodeSegment(dump, node, height, total_nodes),
                              CodeOccurrence(user_id, file_id, None, None))

            return dump, height, total_nodes

        root = ast.parse(code)
        _iterate_node(root)

    def process_file(self, user_id, file_id, file_path: str):
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
        self.process_code(user_id, file_id, code)

    def get_duplicates(self, min_occ_users: int = 2, max_occ_users: int = None,
                       min_total_nodes: int = None, max_total_nodes: int = None,
                       min_height: int = None, max_height: int = None,
                       sort_by: str = 'total_nodes'):
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
            results.append((k, v))
        results.sort(key=lambda x: getattr(x[0], sort_by), reverse=True)
        return results

    @staticmethod
    def pretty_print_result(result, file=sys.stdout):
        segment, occ_users = result
        print('%-18s%-22s%s' % ('User ID', 'File/Submission ID', 'Location'), file=file)
        for uid, occ_user_items in occ_users.items():
            print(uid, file=file)
            for occ in occ_user_items:
                print('%-18s%-22sLine %s, Col %s' % ('', occ.file_id, occ.lineno, occ.col_offset), file=file)
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
