import os
import shutil
import tempfile
from typing import List

from nbconvert.nbconvertapp import NbConvertApp


class NotebookToolkit:
    NOTEBOOK_FILE_EXTENSION = '.ipynb'
    WORK_FOLDER_NAME = 'submit_nbtoolkit'

    @classmethod
    def _scan_notebooks_in_dir(cls, path: str) -> List[str]:
        for root, subdir, files in os.walk(path):
            for file in files:
                if file.lower().endswith(cls.NOTEBOOK_FILE_EXTENSION):
                    path_segments = root.split(os.sep)
                    # exclude MACOSX shadow files
                    if '__MACOSX' in path_segments:
                        continue
                    # exclude files in hidden folders
                    if any(segment.startswith('.') for segment in path_segments):
                        continue
                    yield os.path.join(root, file)

    @classmethod
    def _make_work_dir(cls):
        work_root = os.path.join(tempfile.gettempdir(), cls.WORK_FOLDER_NAME)
        if not os.path.exists(work_root):
            os.makedirs(work_root, mode=0o700, exist_ok=True)  # set 'exist_ok' to accept race conditions
        return tempfile.mkdtemp(dir=work_root)

    @classmethod
    def extract_notebooks(cls, path: str) -> List[str]:
        """
        Extract notebooks from a file.
        """
        if not os.path.isfile(path):  # folder is not supported as it might be problematic to copy the whole folder
            return []
        if path.lower().endswith(cls.NOTEBOOK_FILE_EXTENSION):  # it is a notebook file
            dest_dir = cls._make_work_dir()
            dest_path = os.path.join(dest_dir, os.path.basename(path))
            shutil.copy(path, dest_path)
            return [dest_path]
        if any(path.lower().endswith(ext) for fmt in shutil.get_unpack_formats() for ext in fmt[1]):  # it is a archive
            dest_dir = cls._make_work_dir()
            shutil.unpack_archive(path, dest_dir)
            return cls._scan_notebooks_in_dir(dest_dir)
        return []

    @classmethod
    def convert_to_html(cls, nb_path: str) -> str:
        app = NbConvertApp()
        app.initialize(['--to', 'html', '--template', 'full', nb_path])
        app.start()

        path_segments = os.path.splitext(nb_path)
        html_path = path_segments[0] + '.html'
        assert os.path.exists(html_path)
        return html_path
