import os

from flask import Blueprint, jsonify, request, current_app as app, send_from_directory

from models import db
from oauth import requires_admin
from services.account import AccountService, AccountServiceError
from services.course import CourseService, CourseServiceError
from services.task import TaskService, TaskServiceError
from services.team import TeamService, TeamServiceError
from services.term import TermService, TermServiceError
from utils.upload import handle_upload, handle_post_upload, UploadError, md5sum

admin_api = Blueprint('admin_api', __name__)


@admin_api.route('/users', methods=['GET'])
@requires_admin
def admin_user_list():
    try:
        args = request.args
        if 'name' in args:  # search by name
            limit = args.get('limit')
            if limit is not None:
                try:
                    limit = int(limit)
                except ValueError:
                    return jsonify(msg='limit must be an integer'), 400
                users = AccountService.search_user_by_name(args['name'], limit)
            else:
                users = AccountService.search_user_by_name(args['name'])  # use default limit
            return jsonify([user.to_dict(with_advanced_fields=True) for user in users])
        else:  # get all
            users = AccountService.get_all_users()
            user_dicts = []
            group_set = set()
            for u in users:
                user_dicts.append(u.to_dict(with_groups=False, with_group_ids=True, with_advanced_fields=True))
                # assume groups are lazy-loaded, otherwise need to dig into User.to_dict() to avoid redundant
                # SQL queries on Group table
                group_set.update(u.groups)
            group_dicts = [g.to_dict(with_advanced_fields=True) for g in group_set]
            return jsonify(users=user_dicts, groups=group_dicts)
    except AccountServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/users/<int:uid>', methods=['DELETE'])
@requires_admin
def admin_user(uid):
    try:
        user = AccountService.get_user(uid)
        if user is None:
            return jsonify(msg='user not found'), 404
        db.session.delete(user)
        db.session.commit()
        return "", 204
    except AccountServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/groups', methods=['GET'])
@requires_admin
def admin_group_list():
    try:
        args = request.args
        if 'name' in args:  # search by name
            limit = args.get('limit')
            if limit is not None:
                try:
                    limit = int(limit)
                except ValueError:
                    return jsonify(msg='limit must be an integer'), 400
                groups = AccountService.search_group_by_name(args['name'], limit)
            else:
                groups = AccountService.search_group_by_name(args['name'])  # use default limit
            return jsonify([group.to_dict(with_advanced_fields=True) for group in groups])
        else:  # get all
            groups = [g.to_dict(with_advanced_fields=True) for g in AccountService.get_all_groups()]
            return jsonify(groups)
    except AccountServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/groups/<int:gid>', methods=['DELETE'])
@requires_admin
def admin_group(gid):
    try:
        group = AccountService.get_group(gid)
        if group is None:
            return jsonify(msg='group not found'), 404
        db.session.delete(group)
        db.session.commit()
        return "", 204
    except AccountServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/sync-users')
@requires_admin
def admin_sync_users():
    try:
        AccountService.sync_users()
        db.session.commit()
        return "", 204
    except AccountServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


@admin_api.route('/sync-groups')
@requires_admin
def admin_sync_groups():
    try:
        AccountService.sync_groups()
        db.session.commit()
        return "", 204
    except AccountServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


@admin_api.route('/courses', methods=['GET', 'POST'])
@requires_admin
def admin_courses():
    try:
        if request.method == 'GET':
            return jsonify([c.to_dict(with_advanced_fields=True) for c in CourseService.get_all()])
        else:  # POST
            params = request.json
            course = CourseService.add(params.get('code'), params.get('name'),
                                       params.get('tutor_group_name'), params.get('is_new_tutor_group'))
            db.session.commit()
            return jsonify(course.to_dict(with_advanced_fields=True)), 201
    except (CourseServiceError, AccountServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/courses/<int:cid>', methods=['GET', 'PUT', 'DELETE'])
@requires_admin
def admin_course(cid):
    try:
        course = CourseService.get(cid)
        if course is None:
            return jsonify(msg='course not found'), 404
        if request.method == 'GET':
            return jsonify(course.to_dict(with_terms=True, with_groups=True, with_advanced_fields=True))
        elif request.method == 'PUT':
            params = request.json or request.form or {}
            files = request.files
            upload_type = 'icon'
            if 'icon' in files:
                params['icon'] = handle_upload(files['icon'], upload_type)
            old = CourseService.update(course, **params)
            if 'icon' in old:
                handle_post_upload(old['icon'], upload_type)
            db.session.commit()
            return jsonify(course.to_dict(with_terms=True, with_groups=True, with_advanced_fields=True))
        else:  # DELETE
            db.session.delete(course)
            db.session.commit()
            return "", 204
    except (CourseServiceError, UploadError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/courses/<int:cid>/terms', methods=['GET', 'POST'])
@requires_admin
def admin_terms(cid):
    try:
        course = CourseService.get(cid)
        if course is None:
            return jsonify('course not found'), 404

        if request.method == 'GET':
            return jsonify([t.to_dict(with_advanced_fields=True) for t in TermService.get_for_course(course)])
        else:  # POST
            params = request.json
            term = TermService.add(course, params.get('year'), params.get('semester'),
                                   params.get('student_group_name'), params.get('is_new_student_group'))
            db.session.commit()
            return jsonify(term.to_dict(with_advanced_fields=True)), 201
    except (CourseServiceError, TermServiceError, AccountServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/terms/<int:term_id>', methods=['GET', 'DELETE'])
@requires_admin
def admin_term(term_id):
    try:
        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404

        if request.method == 'GET':
            return jsonify(term.to_dict(with_course=True, with_tasks=True, with_groups=True, with_advanced_fields=True))
        else:  # DELETE
            db.session.delete(term)
            db.session.commit()
            return "", 204
    except TermServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/terms/<int:term_id>/tasks', methods=['GET', 'POST'])
@requires_admin
def admin_term_tasks(term_id):
    try:
        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404

        if request.method == 'GET':
            return jsonify([t.to_dict(with_advanced_fields=True) for t in term.tasks])
        else:  # POST
            params = request.json
            task = TaskService.add(term, params.get('type'), params.get('title'), params.get('description'))
            db.session.commit()
            return jsonify(task.to_dict(with_details=True)), 201
    except (TermServiceError, TaskServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/tasks/<int:tid>', methods=['GET', 'PUT', 'DELETE'])
@requires_admin
def admin_task(tid):
    try:
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404

        if request.method == 'GET':
            return jsonify(task.to_dict(with_term=True, with_details=True))
        elif request.method == 'PUT':
            params = request.json
            TaskService.update(task, **params)
            db.session.commit()
            return jsonify(task.to_dict(with_term=True, with_details=True))
        else:  # DELETE
            db.session.delete(task)
            db.session.commit()
            return "", 204
    except TaskServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/tasks/<int:tid>/materials', methods=['GET', 'POST'])
@requires_admin
def admin_task_materials(tid):
    try:
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404

        if request.method == 'GET':
            return jsonify(m.to_dict(with_advanced_fields=True) for m in task.materials)
        else:  # POST
            params = request.form
            file = request.files.get('file')
            if file is None:
                return jsonify(msg='file is required'), 400

            file_name = params.get('name')
            material_type = params.get('type')

            sub_folders = os.path.join('tasks', str(tid), 'materials', material_type)
            folder = os.path.join(app.config['DATA_FOLDER'], sub_folders)
            if not os.path.isdir(folder):
                os.makedirs(folder)

            save_path = os.path.join(sub_folders, file_name)
            full_path = os.path.join(folder, file_name)

            mat = TaskService.add_material(task, material_type, file_name, params.get('description'), save_path)
            file.save(full_path)
            mat.size = os.stat(full_path).st_size
            mat.md5 = md5sum(full_path)
            db.session.commit()
            return jsonify(mat.to_dict(with_advanced_fields=True)), 201
    except TaskServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/materials/<int:mid>', methods=['DELETE'])
@requires_admin
def admin_material(mid):
    try:
        material = TaskService.get_material(mid)
        if material is None:
            return jsonify(msg='material not found'), 404

        save_path = os.path.join(app.config['DATA_FOLDER'], material.file_path)
        if os.path.isfile(save_path):
            os.remove(save_path)

        db.session.delete(material)
        db.session.commit()
        return "", 204
    except TaskServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/materials/<int:mid>/download')
@requires_admin
def admin_material_download(mid):
    try:
        material = TaskService.get_material(mid)
        if material is None:
            return jsonify(msg='material not found'), 404

        return send_from_directory(app.config['DATA_FOLDER'], material.file_path, as_attachment=True)
    except TaskServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/tasks/<int:tid>/file-requirements', methods=['GET', 'POST'])
@requires_admin
def admin_task_file_requirements(tid):
    try:
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404

        if request.method == 'GET':
            return jsonify(r.to_dict() for r in task.file_requirements)
        else:  # POST
            params = request.json
            req = TaskService.add_file_requirement(task, params.get('name'), params.get('description'),
                                                   params.get('is_optional'), params.get('size_limit'))
            db.session.commit()
            return jsonify(req.to_dict()), 201
    except TaskServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/file-requirements/<int:rid>', methods=['DELETE'])
@requires_admin
def admin_file_requirement(rid):
    try:
        req = TaskService.get_file_requirement(rid)
        if req is None:
            return jsonify(msg='file requirement not found'), 404

        db.session.delete(req)
        db.session.commit()
        return "", 204
    except TaskServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/tasks/<int:task_id>/teams', methods=['GET'])
@requires_admin
def admin_teams(task_id):
    try:
        task = TaskService.get(task_id)
        if task is None:
            return jsonify(msg='task not found'), 404

        return [t.to_dict() for t in TeamService.get_for_task(task)]
    except (TaskServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/teams/<int:team_id>', methods=['GET', 'PUT', 'DELETE'])
@requires_admin
def admin_team(team_id):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        if request.method == 'GET':
            return team.to_dict(with_associations=True)
        elif request.method == 'PUT':
            params = request.json or request.form or {}
            files = request.files
            upload_type = 'avatar'
            if 'avatar' in files:
                params['avatar'] = handle_upload(files['avatar'], upload_type,
                                                 image_check=True, image_check_squared=True)
            old = TeamService.update(team, **params)
            if 'avatar' in old:
                handle_post_upload(old['avatar'], upload_type)
            db.session.commit()
            return jsonify(team.to_dict(with_associations=True))
        else:  # DELETE
            db.session.delete(team)
            db.session.commit()
    except (TeamServiceError, UploadError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
