import difflib
import os
from functools import lru_cache
from io import StringIO
from typing import Optional

from error import BasicError
from models import SubmissionFile, FileRequirement


class SubmissionFileDiffServiceError(BasicError):
    pass


class SubmissionFileDiff:
    def __init__(self, from_file: SubmissionFile, to_file: SubmissionFile, diff: str):
        self.from_file = from_file
        self.to_file = to_file
        self.diff = diff

    def to_dict(self) -> dict:
        d = dict(from_file=self.from_file.to_dict(), to_file=self.to_file.to_dict(), diff=self.diff)
        return d


@lru_cache(maxsize=256)
def cached_read_file(_id: int, md5: str, path: str):
    with open(path) as f:
        return f.readlines()


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
        'md', 'markdown'
    }

    @classmethod
    def is_file_supported(cls, requirement: FileRequirement) -> bool:
        if requirement is None:
            raise SubmissionFileDiffServiceError('file requirement is required')

        _, ext = os.path.splitext(requirement.name)
        ext = ext.lower().lstrip('.')
        return ext in cls._text_file_extensions

    @classmethod
    def generate_diff(cls, from_file: SubmissionFile, to_file: SubmissionFile, data_root: str,
                      context_lines: int = 3) -> Optional[SubmissionFileDiff]:
        if from_file is None:
            raise SubmissionFileDiffServiceError('from file is required')
        if to_file is None:
            raise SubmissionFileDiffServiceError('to file is required')
        from_req = from_file.requirement
        if not cls.is_file_supported(from_req):
            raise SubmissionFileDiffServiceError('from file is not supported')
        to_req = to_file.requirement
        if not cls.is_file_supported(to_req):
            raise SubmissionFileDiffServiceError('to file is not supported')
        if from_file.size > cls._max_file_size:
            raise SubmissionFileDiffServiceError('from file is too big')
        if to_file.size > cls._max_file_size:
            raise SubmissionFileDiffServiceError('to file is too big')

        # TODO md5 check (necessary?)
        from_content = cached_read_file(from_file.id, from_file.md5, os.path.join(data_root, from_file.path))
        to_content = cached_read_file(to_file.id, to_file.md5, os.path.join(data_root, to_file.path))

        diff = difflib.unified_diff(from_content, to_content, fromfile=from_req.name, tofile=to_req.name,
                                    fromfiledate='(Submission %d)' % from_file.submission_id,
                                    tofiledate='(Submission %d)' % to_file.submission_id,
                                    n=context_lines)
        with StringIO() as f_out:
            f_out.writelines(diff)
            diff = f_out.getvalue()
        if not diff:  # no diff
            return None

        return SubmissionFileDiff(from_file, to_file, diff)
