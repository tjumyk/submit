import os
from urllib.parse import quote
from typing import List, Optional

from error import BasicError
from models import Material
from utils.notebook import NotebookToolkit
from bs4 import BeautifulSoup


class MaterialPreviewServiceError(BasicError):
    pass


class MaterialNotebookPreview:
    def __init__(self, material_id: int, md5: str, name: str, html_name: str, base_dir: str, inline_html: str):
        self.material_id = material_id
        self.md5 = md5

        self.name = name
        self.html_name = html_name
        self.base_dir = base_dir

        self.inline_html = inline_html

    def to_dict(self):
        return dict(material_id=self.material_id, md5=self.md5, name=self.name,
                    inline_html=self.inline_html)  # hide internal values


_previews_cache = {}


class MaterialPreviewService:
    @classmethod
    def _extract_notebooks(cls, material: Material, data_root: str):
        notebooks = NotebookToolkit.extract_notebooks(os.path.join(data_root, material.file_path))
        previews = {}
        for notebook in notebooks:
            name = os.path.basename(notebook)
            html_path = NotebookToolkit.convert_to_html(notebook)
            base_dir, html_name = os.path.split(html_path)
            inline_html = cls._extract_inline_html(material, name, html_path)
            previews[name] = MaterialNotebookPreview(material_id=material.id, md5=material.md5, name=name,
                                                     html_name=html_name, base_dir=base_dir, inline_html=inline_html)
        return previews

    @staticmethod
    def _extract_inline_html(material: Material, notebook_name: str, html_path: str):
        with open(html_path) as f_html:
            html = f_html.read()
            doc = BeautifulSoup(html, 'html.parser')
            body = doc.body
            # fix images
            for img in body.select('img'):
                img_src = img.get('src')
                if not img_src or img_src.startswith('/') \
                        or img_src.startswith('http://') or img_src.startswith('https://'):
                    continue
                img['src'] = 'api/materials/%d/notebooks/%s/' % (material.id, quote(notebook_name)) + img_src
            # fix anchors
            for anchor in body.select('a'):
                href = anchor.get('href')
                if not href:
                    continue
                if href.startswith('http://') or href.startswith('https://'):
                    anchor['target'] = '_blank'
                elif href.startswith('#'):
                    anchor.extract()
            # remove ids
            for x in body.select('[id]'):
                del x['id']
            # remove style tags
            for style in body.select('style'):
                style.extract()
            inline_html = ''.join(str(c) for c in body.children)
        return inline_html

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
