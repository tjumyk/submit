import os
from models import SubmissionFile


class SubmissionFileViewerService:
    _code_highlight_file_extensions = {
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
    def select_viewer(cls, file: SubmissionFile, data_root: str):
        file_name = file.requirement.name
        _, ext = os.path.splitext(file_name)
        ext = ext.lower().lstrip('.')
        if ext in cls._code_highlight_file_extensions:
            with open(os.path.join(data_root, file.path)) as f_file:
                file_content = f_file.read()
            return 'highlight.html', dict(submission_id=file.submission_id, id=file.id, name=file_name,
                                          content=file_content, md5=file.md5[0:6], language_class=ext)

        return None
