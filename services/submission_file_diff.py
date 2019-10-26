import difflib
import os
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


class SubmissionFileDiffService:
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

        # TODO md5 check (necessary?)

        with open(os.path.join(data_root, from_file.path)) as f_from:
            from_content = f_from.readlines()
        with open(os.path.join(data_root, to_file.path)) as f_to:
            to_content = f_to.readlines()

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
