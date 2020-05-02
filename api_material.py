import os
from datetime import datetime

from flask import Blueprint, jsonify, send_from_directory, current_app as app, redirect, request

from api_submission import requires_worker
from auth_connect.oauth import requires_login
from services.account import AccountService
from services.material_preview import MaterialPreviewService
from services.task import TaskService, TaskServiceError
from services.term import TermService, TermServiceError

material_api = Blueprint('material_api', __name__)


@material_api.route('/<int:mid>/download')
@requires_login
def material_download(mid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        material = TaskService.get_material(mid)
        if material is None:
            return jsonify(msg='material not found'), 404

        task = material.task
        roles = TermService.get_access_roles(task.term, user)
        if not roles:
            return jsonify(msg='access forbidden'), 403

        if 'admin' not in roles and 'tutor' not in roles:
            if material.is_private:
                return jsonify(msg='access forbidden'), 403
            if not task.open_time or task.open_time > datetime.utcnow():
                return jsonify(msg='task has not yet open'), 403

        return send_from_directory(app.config['DATA_FOLDER'], material.file_path, as_attachment=True, cache_timeout=0)
    except (TaskServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@material_api.route('/<int:mid>/worker-download')
@requires_worker
def material_worker_download(mid):
    try:
        material = TaskService.get_material(mid)
        if material is None:
            return jsonify(msg='material not found'), 404
        return send_from_directory(app.config['DATA_FOLDER'], material.file_path, as_attachment=True, cache_timeout=0)
    except (TaskServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@material_api.route('/<int:mid>/notebooks')
@requires_login
def material_get_notebooks(mid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        material = TaskService.get_material(mid)
        if material is None:
            return jsonify(msg='material not found'), 404

        task = material.task
        roles = TermService.get_access_roles(task.term, user)
        if not roles:
            return jsonify(msg='access forbidden'), 403

        if 'admin' not in roles and 'tutor' not in roles:
            if material.is_private:
                return jsonify(msg='access forbidden'), 403
            if not task.open_time or task.open_time > datetime.utcnow():
                return jsonify(msg='task has not yet open'), 403

        notebooks = MaterialPreviewService.get_notebooks(material, app.config['DATA_FOLDER'])
        return jsonify([nb.to_dict() for nb in notebooks])
    except (TaskServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@material_api.route('/<int:mid>/notebooks/<path:path>')
@requires_login
def material_get_notebook_content(mid, path: str):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        material = TaskService.get_material(mid)
        if material is None:
            return jsonify(msg='material not found'), 404

        task = material.task
        roles = TermService.get_access_roles(task.term, user)
        if not roles:
            return jsonify(msg='access forbidden'), 403

        if 'admin' not in roles and 'tutor' not in roles:
            if material.is_private:
                return jsonify(msg='access forbidden'), 403
            if not task.open_time or task.open_time > datetime.utcnow():
                return jsonify(msg='task has not yet open'), 403

        path = path.lstrip('/')
        if path.find('/') < 0:
            # require a trailing slash after notebook name to avoid errors when loading resources from relative paths
            return jsonify(msg='notebook name must end with a slash'), 400

        notebook_name, sub_path = path.split('/', 1)
        notebook = MaterialPreviewService.get_notebook(material, notebook_name, app.config['DATA_FOLDER'])
        if notebook is None:
            return jsonify(msg='notebook not found'), 404

        if not sub_path:  # requesting notebook html
            return send_from_directory(notebook.base_dir, notebook.html_name, cache_timeout=0)
        else:  # requesting associated resource files
            # when 'custom.css' is requested and the notebook itself does not have one, the default 'notebook.css' in
            # the root folder will be used
            if sub_path == 'custom.css' and not os.path.exists(os.path.join(notebook.base_dir, sub_path)):
                return send_from_directory(app.root_path, 'notebook-page.css')

            return send_from_directory(notebook.base_dir, sub_path, cache_timeout=0)
    except (TaskServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
