from datetime import datetime
from flask import Blueprint, jsonify, send_from_directory, current_app as app

from api_submission import requires_worker
from oauth import requires_login
from services.account import AccountService
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

