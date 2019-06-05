import os
from typing import List, Optional

from error import BasicError
from models import Material
from utils.notebook import NotebookToolkit


class MaterialPreviewServiceError(BasicError):
    pass


class MaterialNotebookPreview:
    def __init__(self, material_id: int, md5: str, name: str, html_name: str, base_dir: str):
        self.material_id = material_id
        self.md5 = md5

        self.name = name
        self.html_name = html_name
        self.base_dir = base_dir

    def to_dict(self):
        return dict(material_id=self.material_id, md5=self.md5, name=self.name)  # hide internal values


_previews_cache = {}


class MaterialPreviewService:
    @staticmethod
    def _extract_notebooks(material: Material, data_root: str):
        notebooks = NotebookToolkit.extract_notebooks(os.path.join(data_root, material.file_path))
        previews = {}
        for notebook in notebooks:
            name = os.path.basename(notebook)
            html_path = NotebookToolkit.convert_to_html(notebook)
            base_dir, html_name = os.path.split(html_path)
            previews[name] = MaterialNotebookPreview(material_id=material.id, md5=material.md5,
                                                     name=name, html_name=html_name, base_dir=base_dir)
        return previews

    @classmethod
    def get_notebooks(cls, material: Material, data_root: str) -> List[MaterialNotebookPreview]:
        cache_key = (material.id, material.md5)
        previews = _previews_cache.get(cache_key)
        if previews is None:
            previews = cls._extract_notebooks(material, data_root)
            _previews_cache[cache_key] = previews
        return list(previews.values())

    @classmethod
    def get_notebook(cls, material: Material, notebook_name: str, data_root: str) \
            -> Optional[MaterialNotebookPreview]:
        cache_key = (material.id, material.md5)
        previews = _previews_cache.get(cache_key)
        if previews is None:
            previews = cls._extract_notebooks(material, data_root)
            _previews_cache[cache_key] = previews
        return previews.get(notebook_name)
