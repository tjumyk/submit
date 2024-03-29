import difflib
import os
from collections import OrderedDict
from functools import lru_cache

from error import BasicError
from models import SubmissionFile, FileRequirement
from utils.file import FileUtils


class SubmissionFileDiffServiceError(BasicError):
    pass


class SubmissionFileDiff:
    def __init__(self, from_file: SubmissionFile, to_file: SubmissionFile,
                 binary: bool, same: bool,
                 additions: int = None, deletions: int = None, diff: str = None):
        self.from_file = from_file
        self.to_file = to_file

        self.binary = binary
        self.same = same

        self.additions = additions
        self.deletions = deletions
        self.diff = diff

    def to_dict(self, with_file_details: bool = False) -> dict:
        d = dict(from_file_id=self.from_file.id, to_file_id=self.to_file.id,
                 from_submission_id=self.from_file.submission_id, to_submission_id=self.to_file.submission_id,
                 binary=self.binary, same=self.same,
                 additions=self.additions, deletions=self.deletions, diff=self.diff)
        if with_file_details:
            d['from_file'] = self.from_file.to_dict()
            d['to_file'] = self.to_file.to_dict()
        return d


@lru_cache(maxsize=128)
def cached_read_file(path: str):
    with open(path, 'rb') as f:
        content, _ = FileUtils.read_text(f.read())
        return content.splitlines(keepends=True)


class SubmissionFileDiffService:
    _max_file_size = 10 * 1024 * 1024  # 10 MB
    _text_file_extensions = {
        'txt',
        'py',
        'pl', 'ruby', 'php',
        'c', 'h', 'cpp', 'cxx', 'hpp',
        'java', 'cs',
        'js', 'css', 'html', 'coffee',
        'sh',
        'json', 'xml',
        'sql',
        'md', 'markdown',
        'source'
    }
    _result_cache = OrderedDict()  # (from_id, to_id) -> (additions, deletions) FIFO order
    _result_cache_max_size = 1024

    @classmethod
    def _is_text_file(cls, requirement: FileRequirement) -> bool:
        if requirement is None:
            raise SubmissionFileDiffServiceError('file requirement is required')

        _, ext = os.path.splitext(requirement.name)
        ext = ext.lower().lstrip('.')
        return ext in cls._text_file_extensions

    @classmethod
    def generate_diff(cls, from_file: SubmissionFile, to_file: SubmissionFile, data_root: str,
                      context_lines: int = 3, with_diff_content: bool = False) -> SubmissionFileDiff:
        if from_file is None:
            raise SubmissionFileDiffServiceError('from file is required')
        if to_file is None:
            raise SubmissionFileDiffServiceError('to file is required')

        from_req = from_file.requirement
        to_req = to_file.requirement
        if not cls._is_text_file(from_req) or not cls._is_text_file(to_req):  # binary file comparison
            return SubmissionFileDiff(from_file, to_file, binary=True, same=from_file.md5 == to_file.md5)
        if from_file.md5 == to_file.md5:  # skip actual diff if md5 match
            return SubmissionFileDiff(from_file, to_file, binary=False, same=True)

        # assume contents of a submission file never change given a specific ID
        cache_key = (from_file.id, to_file.id)
        if not with_diff_content:  # check if we already have the results in cache
            cache = cls._result_cache.get(cache_key)
            if cache:
                cls._result_cache.move_to_end(cache_key)  # move the key to the 'freshest' side
                additions, deletions = cache
                return SubmissionFileDiff(from_file, to_file, binary=False, same=False,
                                          additions=additions, deletions=deletions)

        # check file sizes before reading files
        if from_file.size > cls._max_file_size:
            raise SubmissionFileDiffServiceError('from file is too big')
        if to_file.size > cls._max_file_size:
            raise SubmissionFileDiffServiceError('to file is too big')

        # assume the 'physical file' at the path of a submission file is never changed
        from_content = cached_read_file(os.path.join(data_root, from_file.path))
        to_content = cached_read_file(os.path.join(data_root, to_file.path))

        diff = difflib.unified_diff(from_content, to_content, fromfile=from_req.name, tofile=to_req.name,
                                    fromfiledate='(Submission %d)' % from_file.submission_id,
                                    tofiledate='(Submission %d)' % to_file.submission_id,
                                    n=context_lines)
        additions = 0
        deletions = 0
        diff_lines = []
        for line in diff:
            if with_diff_content:
                diff_lines.append(line)
            if not line:
                continue
            ch = line[0]
            if ch == '+':
                if not line.startswith('+++'):
                    additions += 1
            elif ch == '-':
                if not line.startswith('---'):
                    deletions += 1
        diff_text = ''.join(diff_lines) if with_diff_content else None

        # save (partial) results into cache and take care of the size of the cache
        cls._result_cache[cache_key] = (additions, deletions)
        while len(cls._result_cache) > cls._result_cache_max_size:
            cls._result_cache.popitem(last=False)

        return SubmissionFileDiff(from_file, to_file, binary=False, same=False,
                                  additions=additions, deletions=deletions, diff=diff_text)
