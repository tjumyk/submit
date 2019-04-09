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
    def __init__(self, user_id, file_id, lineno: Optional[int], col_offset: Optional[int]):
        self.user_id = user_id
        self.file_id = file_id
        self.lineno = lineno
        self.col_offset = col_offset

    def __repr__(self):
        return '<CodeOccurrence user=%s, file=%s, line=%s, col=%s>' % \
               (self.user_id, self.file_id, self.lineno, self.col_offset)

    def to_dict(self) -> dict:
        return dict(user_id=self.user_id, file_id=self.file_id, lineno=self.lineno, col_offset=self.col_offset)


class CodeFileInfo:
    def __init__(self, md5: str, ast_height: int, ast_total_nodes: int):
        self.md5 = md5
        self.ast_height = ast_height
        self.ast_total_nodes = ast_total_nodes


class CodeSegmentIndex:
    def __init__(self, min_index_height: int):
        self._min_index_height = min_index_height
        self._index = {}
        self._file_info_map = {}

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
            lineno = None
            col_offset = None
            if isinstance(node, ast.AST):
                fields = []
                for field_name, field_value in ast.iter_fields(node):
                    node_dump, node_height, node_total_nodes, node_lineno, node_col_offset = _iterate_node(field_value)
                    fields.append((field_name, node_dump))
                    height = max(height, node_height + 1)
                    total_nodes += node_total_nodes
                dump = '%s(%s)' % (node.__class__.__name__, ', '.join(dump for _, dump in fields))

                lineno, col_offset = _extract_node_position(node)

                if height >= self._min_index_height:
                    self._put(CodeSegment(dump, node, height, total_nodes),
                              CodeOccurrence(user_id, file_id, lineno, col_offset))
            elif isinstance(node, list):
                item_dumps = []
                item_heights = []
                item_total_nodes = []
                item_positions = []
                for x in node:
                    node_dump, node_height, node_total_nodes, node_lineno, node_col_offset = _iterate_node(x)
                    item_dumps.append(node_dump)
                    item_positions.append((node_lineno, node_col_offset))
                    height = max(height, node_height + 1)
                    item_heights.append(node_height)
                    item_total_nodes.append(node_total_nodes)
                    total_nodes += node_total_nodes
                dump = '[%s]' % ', '.join(item_dumps)

                if len(node):  # use the position info of the first item
                    lineno, col_offset = item_positions[0]

                if height >= self._min_index_height:
                    self._put(CodeSegment(dump, node, height, total_nodes),
                              CodeOccurrence(user_id, file_id, lineno, col_offset))

                # also index partial lists
                for start_idx in range(len(node)):
                    for end_idx in range(start_idx + 2, len(node) + 1):  # at least two items
                        partial_list_height = max(item_heights[start_idx:end_idx])
                        if partial_list_height >= self._min_index_height:
                            partial_list = node[start_idx:end_idx]
                            partial_list_dump = ', '.join(item_dumps[start_idx: end_idx])
                            partial_list_total_nodes = sum(item_total_nodes[start_idx:end_idx])
                            partial_list_lineno, partial_list_col_offset = item_positions[start_idx]
                            self._put(CodeSegment(partial_list_dump, partial_list, partial_list_height,
                                                  partial_list_total_nodes),
                                      CodeOccurrence(user_id, file_id, partial_list_lineno, partial_list_col_offset))
            else:
                dump = repr(node)
                # no position info available, use default None for lineno and col_offset
                if height >= self._min_index_height:
                    self._put(CodeSegment(dump, node, height, total_nodes),
                              CodeOccurrence(user_id, file_id, lineno, col_offset))

            return dump, height, total_nodes, lineno, col_offset

        def _extract_node_position(node):
            lineno = None
            col_offset = None
            if node._attributes:
                for attr_name in node._attributes:
                    if attr_name == 'lineno':
                        lineno = getattr(node, attr_name)
                    elif attr_name == 'col_offset':
                        col_offset = getattr(node, attr_name)
            return lineno, col_offset

        root = ast.parse(code)
        return _iterate_node(root)

    def remove_code(self, user_id, file_id):
        segments_to_delete = []
        for k, v in self._index.items():
            user_occurrences = v.get(user_id)
            if user_occurrences:
                i = 0
                while i < len(user_occurrences):
                    occ = user_occurrences[i]
                    if occ.file_id == file_id:
                        user_occurrences.pop(i)
                    else:
                        i += 1
                if len(user_occurrences) == 0:  # empty occ list
                    del v[user_id]
            if len(v) == 0:  # empty occ users
                segments_to_delete.append(k)
        for k in segments_to_delete:
            del self._index[k]

    def process_file(self, user_id, file_id, file_path: str, file_md5: str = None) -> CodeFileInfo:
        file_info = self._file_info_map.get(file_id)
        if file_info is not None:
            if file_info.md5 == file_md5:
                logger.info('Skipped processing file as already processed: uid=%s, fid/sid=%s, md5=%s'
                            % (user_id, file_id, file_md5))
                return file_info
            else:
                logger.info('Removing index for old file: uid=%s, fid/sid=%s, old_md5=%s, new_md5=%s'
                            % (user_id, file_id, file_info.md5, file_md5))
                self.remove_code(user_id, file_id)

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
        _, ast_height, ast_total_nodes, _, _ = self.process_code(user_id, file_id, code)
        file_info = CodeFileInfo(md5=file_md5, ast_height=ast_height, ast_total_nodes=ast_total_nodes)
        self._file_info_map[file_id] = file_info
        return file_info

    def get_file_info(self, file_id) -> CodeFileInfo:
        return self._file_info_map.get(file_id)

    def get_duplicates(self, min_occ_users: int = 2, max_occ_users: int = None,
                       min_total_nodes: int = None, max_total_nodes: int = None,
                       min_height: int = None, max_height: int = None,
                       sort_by: str = 'total_nodes',
                       include_user_id: int = None, include_user_file_id: int = None,
                       exclude_user_id: int = None, exclude_user_file_id: int = None,
                       min_code_length: int = None, max_code_length: int = None,
                       min_code_lines: int = 2, max_code_lines: int = None) \
            -> List[Tuple[CodeSegment, Dict[int, List[CodeOccurrence]]]]:
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

            if include_user_id is not None:
                user_occurrences = v.get(include_user_id)
                if user_occurrences is None:
                    continue
                if include_user_file_id is not None and not any(occ.file_id == include_user_file_id
                                                                for occ in user_occurrences):
                    continue
            else:
                if include_user_file_id is not None:
                    logger.warning('parameter "include_user_file_id" is ignored when "include_user_id" is not provided')

            if exclude_user_id is not None:
                user_occurrences = v.get(exclude_user_id)
                if user_occurrences is not None:
                    if exclude_user_file_id is None:
                        continue
                    if any(occ.file_id == exclude_user_file_id for occ in user_occurrences):
                        continue
            else:
                if exclude_user_file_id is not None:
                    logger.warning('parameter "exclude_file_id" is ignored when "exclude_user_id" is not provided')

            if min_code_length is not None or max_code_length is not None \
                    or min_code_lines is not None or max_code_lines is not None:  # need to un-parse the AST
                # The un-parsed code should have the same execution sequence as the original code but the textual format
                # may be quite different.
                try:
                    code = astunparse.unparse(k.node)
                except AttributeError as e:
                    logger.warning('Un-parse AST failed: %s' % str(e))
                    continue
                # the un-parse function produce may produce an empty starting line and an empty ending line
                code = code.strip()
                code_length = len(code)
                if min_code_length is not None and code_length < min_code_length:
                    continue
                if max_code_length is not None and code_length > max_code_length:
                    continue
                if min_code_lines is not None or max_code_lines is not None:  # need to count the number of lines
                    # We are using the number of lines of the un-parsed code, which does not necessarily has the same
                    # number of lines as the original code.
                    num_lines = len(code.split('\n'))
                    if min_code_lines is not None and num_lines < min_code_lines:
                        continue
                    if max_code_lines is not None and num_lines > max_code_lines:
                        continue

            results.append((k, v))
        results.sort(key=lambda x: getattr(x[0], sort_by), reverse=True)
        return results

    @staticmethod
    def result_to_dict(result: Tuple[CodeSegment, Dict[int, List[CodeOccurrence]]]) -> Dict:
        segment, occ_users = result
        return dict(segment=segment.to_dict(),
                    occurrences={uid: [occ.to_dict() for occ in user_occurrences] for uid, user_occurrences in
                                 occ_users.items()})

    def pretty_print_result(self, result, file=sys.stdout):
        segment, occ_users = result
        print('%-18s%-22s%-16s%-8s%s' % ('User/Team ID', 'File/Submission ID', 'AST Coverage', 'MD5', 'Location'),
              file=file)
        for uid, occ_user_items in occ_users.items():
            print(uid, file=file)
            for occ in occ_user_items:
                md5 = None
                coverage = None
                file_info = self._file_info_map.get(occ.file_id)
                if file_info:
                    md5 = file_info.md5
                    coverage = '%.f%%' % (segment.total_nodes / file_info.ast_total_nodes * 100)
                md5_short = md5[:6] if md5 else None
                print('%-18s%-22s%-16s%-8sLine %s, Col %s' % ('', occ.file_id, coverage, md5_short, occ.lineno,
                                                              occ.col_offset),
                      file=file)
        print('AST Nodes: %d, Height: %d' % (segment.total_nodes, segment.height), file=file)
        print(astunparse.unparse(segment.node), file=file)

    def pretty_print_results(self, results, file=sys.stdout):
        print('Total Results: %d' % len(results), file=file)
        for i, r in enumerate(results):
            print('--------------------------------------- #%-2s ---------------------------------------'
                  % (i + 1), file=file)
            self.pretty_print_result(r, file=file)


def test_process_submissions(task_id: int, requirement_id: int, min_index_height: int):
    from models import SubmissionFile, db, Submission
    from server import app
    with app.test_request_context():
        index = CodeSegmentIndex(min_index_height=min_index_height)
        data_folder = app.config['DATA_FOLDER']
        user_set = set()
        valid_file_count = 0
        syntax_error_count = 0
        for sid, uid, path, md5 in db.session.query(Submission.id, Submission.submitter_id, SubmissionFile.path,
                                                    SubmissionFile.md5) \
                .filter(SubmissionFile.requirement_id == requirement_id,
                        SubmissionFile.submission_id == Submission.id,
                        Submission.task_id == task_id) \
                .all():
            user_set.add(uid)
            try:
                index.process_file(uid, sid, os.path.join(data_folder, path), md5)
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
