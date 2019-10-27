import os

from models import SubmissionFile


class SubmissionFileViewerService:
    _template_name = 'highlight.html'
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
            title = '%s (#%s)' % (file_name, file.md5[0:6])
            return cls._template_name, dict(title=title, content=file_content, language_class=ext)

        return None

    @classmethod
    def get_diff_viewer(cls, diff):
        from_file = diff.from_file
        to_file = diff.to_file
        title = '%s (Submission %d) --> %s (Submission %d)' % \
                (from_file.requirement.name, from_file.submission_id,
                 to_file.requirement.name, to_file.submission_id)
        if diff.same:
            return cls._template_name, dict(title=title, content='Same File', language_class='md')
        if diff.binary:
            return cls._template_name, dict(title=title, content='Binary Diff', language_class='md')
        if not diff.diff:
            return cls._template_name, dict(title=title, content='No Diff', language_class='md')
        return cls._template_name, dict(title=title, content=diff.diff, language_class='diff')
