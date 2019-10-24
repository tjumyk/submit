import os
import re
import shutil
import tempfile

from flask import Blueprint, jsonify, request, current_app as app, send_from_directory
from sqlalchemy import func

from auth_connect.oauth import requires_admin
from models import db, Submission, UserTeamAssociation, Team
from services.account import AccountService, AccountServiceError
from services.auto_test import AutoTestService, AutoTestServiceError
from services.course import CourseService, CourseServiceError
from services.submission import SubmissionService, SubmissionServiceError
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
            params = request.json or request.form.to_dict() or {}
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
            return jsonify(task.to_dict(with_term=True, with_details=True, with_advanced_fields=True))
        elif request.method == 'PUT':
            params = request.json
            TaskService.update(task, **params)
            db.session.commit()
            return jsonify(task.to_dict(with_term=True, with_details=True, with_advanced_fields=True))
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

            mat = TaskService.add_material(task, material_type, file_name, params.get('description'), save_path,
                                           params.get('is_private') == 'true')
            file.save(full_path)
            mat.size = os.stat(full_path).st_size
            mat.md5 = md5sum(full_path)
            db.session.commit()
            return jsonify(mat.to_dict(with_advanced_fields=True)), 201
    except TaskServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/materials/<int:mid>', methods=['DELETE', 'PUT'])
@requires_admin
def admin_material(mid):
    try:
        material = TaskService.get_material(mid)
        if material is None:
            return jsonify(msg='material not found'), 404

        data_folder = app.config['DATA_FOLDER']

        if request.method == 'DELETE':
            save_path = os.path.join(data_folder, material.file_path)
            if os.path.isfile(save_path):
                os.remove(save_path)

            # remove parent folder if empty now
            parent_folder = os.path.dirname(save_path)
            if os.path.lexists(parent_folder) and not os.listdir(parent_folder):
                os.rmdir(parent_folder)

            db.session.delete(material)
            db.session.commit()
            return "", 204
        else:  # PUT
            params = request.json or request.form.to_dict() or {}
            allowed_fields = {'is_private', 'description'}
            for k, v in params.items():
                if k not in allowed_fields:
                    return jsonify(msg='invalid field', detail=k), 400
                if k == 'is_private':
                    if type(v) == str:
                        v = v == 'true'
                setattr(material, k, v)

            file = request.files.get('file')
            if file is not None:
                sub_folders = os.path.join('tasks', str(material.task_id), 'materials', material.type)
                folder = os.path.join(data_folder, sub_folders)
                if not os.path.isdir(folder):
                    os.makedirs(folder)

                save_path = os.path.join(sub_folders, material.name)
                full_path = os.path.join(folder, material.name)

                material.file_path = save_path
                file.save(full_path)
                material.size = os.stat(full_path).st_size
                material.md5 = md5sum(full_path)

            db.session.commit()
            return jsonify(material.to_dict(with_advanced_fields=True))
    except TaskServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/materials/<int:mid>/download')
@requires_admin
def admin_material_download(mid):
    try:
        material = TaskService.get_material(mid)
        if material is None:
            return jsonify(msg='material not found'), 404

        return send_from_directory(app.config['DATA_FOLDER'], material.file_path, as_attachment=True, cache_timeout=0)
    except TaskServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/materials/<int:mid>/validate-test-environment')
@requires_admin
def admin_material_validate_test_environment(mid):
    try:
        material = TaskService.get_material(mid)
        if material is None:
            return jsonify(msg='material not found'), 404

        full_path = os.path.join(app.config['DATA_FOLDER'], material.file_path)
        if md5sum(full_path) != material.md5:
            return jsonify(msg='md5 does not match'), 500

        tmp_dir = os.path.join(tempfile.mkdtemp(prefix='submit-material-validate'))

        info = {}
        archive_ok = False
        try:
            shutil.unpack_archive(full_path, tmp_dir)
            archive_ok = True
        except IOError as e:
            info['error'] = dict(msg='invalid archive', detail=str(e))

        if archive_ok:
            dockerfile = os.path.join(tmp_dir, 'Dockerfile')
            if os.path.exists(dockerfile):
                info['type'] = 'docker'

                conda_installer = re.compile(r'((Ana|Mini)conda[\d\w\-._]+)\.sh')
                conda_create = re.compile(r'conda\s+create\s+(.*\s+)?python=(.*)')
                with open(dockerfile) as f_dockerfile:
                    for line in f_dockerfile:
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith('ENTRYPOINT'):
                            info['docker_entry_point'] = line[len('ENTRYPOINT'):]
                        elif line.startswith('CMD'):
                            info['docker_cmd'] = line[len('CMD'):]
                        elif line.startswith('RUN'):
                            match = conda_installer.search(line)
                            if match:
                                info['conda_version'] = match.group(1)
                            else:
                                match = conda_create.search(line)
                                if match:
                                    info['conda_python_version'] = match.group(2)

                requirements_txt = os.path.join(tmp_dir, 'test', 'requirements.txt')
                if os.path.exists(requirements_txt):
                    requirements = []
                    with open(requirements_txt) as f_requirements_txt:
                        for line in f_requirements_txt:
                            line = line.strip()
                            if not line or line[0] == '#':  # empty line or comment
                                continue
                            requirements.append(line)
                        info['pip_requirements'] = requirements
            elif os.path.exists(os.path.join(tmp_dir, 'run.sh')):
                info['type'] = 'run-script'
            else:
                info['error'] = dict(msg='Dockerfile or run.sh not found')

        shutil.rmtree(tmp_dir)
        return jsonify(info)
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


@admin_api.route('/tasks/<int:tid>/auto-test-configs', methods=['GET', 'POST'])
@requires_admin
def admin_task_auto_test_configs(tid):
    try:
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404

        if request.method == 'GET':
            return jsonify(c.to_dict(with_advanced_fields=True) for c in task.auto_test_configs)
        else:  # POST
            params = request.json

            env_id = params.pop('environment_id', None)
            if env_id:
                env = TaskService.get_material(env_id)
                if env is None:
                    return jsonify(msg='environment material not found')
                params['environment'] = env

            file_req_id = params.pop('file_requirement_id', None)
            if file_req_id:
                file_req = TaskService.get_file_requirement(file_req_id)
                if file_req is None:
                    return jsonify(msg='target file requirement not found')
                params['file_requirement'] = file_req

            template_file_id = params.pop('template_file_id', None)
            if template_file_id:
                template_file = TaskService.get_material(template_file_id)
                if template_file is None:
                    return jsonify(msg='template file material not found')
                params['template_file'] = template_file

            config = TaskService.add_auto_test_config(task, **params)

            db.session.commit()
            return jsonify(config.to_dict(with_advanced_fields=True)), 201
    except TaskServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/auto-test-configs/<int:cid>', methods=['PUT', 'DELETE'])
@requires_admin
def admin_task_auto_test_config(cid):
    try:
        config = TaskService.get_auto_test_config(cid)
        if config is None:
            return jsonify(msg='auto test config not found'), 404

        if request.method == 'PUT':
            params = request.json

            if 'environment_id' in params:
                env_id = params.pop('environment_id')
                if env_id:
                    env = TaskService.get_material(env_id)
                    if env is None:
                        return jsonify(msg='environment material not found')
                    params['environment'] = env
                else:
                    params['environment'] = None

            if 'file_requirement_id' in params:
                file_req_id = params.pop('file_requirement_id')
                if file_req_id:
                    file_req = TaskService.get_file_requirement(file_req_id)
                    if file_req is None:
                        return jsonify(msg='target file requirement not found')
                    params['file_requirement'] = file_req
                else:
                    params['file_requirement'] = None

            if 'template_file_id' in params:
                template_file_id = params.pop('template_file_id')
                if template_file_id:
                    template_file = TaskService.get_material(template_file_id)
                    if template_file is None:
                        return jsonify(msg='template file material not found')
                    params['template_file'] = template_file
                else:
                    params['template_file'] = None

            config = TaskService.update_auto_test_config(config, **params)

            db.session.commit()
            return jsonify(config.to_dict(with_advanced_fields=True))
        else:  # DELETE
            db.session.delete(config)
            db.session.commit()
            return "", 204
    except TaskServiceError as e:
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
            params = request.json or request.form.to_dict() or {}
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
            return "", 204
    except (TeamServiceError, UploadError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/tasks/<int:task_id>/special-considerations', methods=['GET', 'POST'])
@requires_admin
def admin_task_special_considerations(task_id):
    try:
        task = TaskService.get(task_id)
        if task is None:
            return jsonify(msg='task not found'), 404

        if request.method == 'GET':
            return jsonify([s.to_dict(with_user_or_team=True) for s in
                            TaskService.get_special_considerations_for_task(task)])
        else:  # POST
            params = request.json

            user_name = params.get('user_name')
            if user_name:
                user = AccountService.get_user_by_name(user_name)
                if user is None:
                    return jsonify(msg='user not found'), 400
            else:
                user = None

            team_name = params.get('team_name')
            if team_name:
                team = TeamService.get_by_task_and_name(task, team_name)
                if team is None:
                    return jsonify(msg='team not found'), 400
            else:
                team = None

            spec = TaskService.add_special_consideration(task, user, team,
                                                         params.get('due_time_extension'),
                                                         params.get('submission_attempt_limit_extension'))
            db.session.commit()
            return jsonify(spec.to_dict(with_user_or_team=True)), 201
    except (TaskServiceError, AccountServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/special-considerations/<int:spec_id>', methods=['DELETE'])
@requires_admin
def admin_special_consideration(spec_id):
    try:
        spec = TaskService.get_special_consideration(spec_id)
        if spec is None:
            return jsonify(msg='special consideration not found'), 404

        db.session.delete(spec)
        db.session.commit()
        return "", 204
    except TaskServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/submissions/<int:sid>/run-auto-test/<int:cid>')
@requires_admin
def admin_submission_run_auto_test(sid, cid):
    try:
        submission = SubmissionService.get(sid)
        if submission is None:
            return jsonify(msg='submission not found'), 404
        config = TaskService.get_auto_test_config(cid)
        if config is None:
            return jsonify(msg='auto test config not found'), 404

        test, result = SubmissionService.run_auto_test(submission, config)
        db.session.commit()

        test_obj = test.to_dict(with_advanced_fields=True)
        test_obj.update(AutoTestService.result_to_dict(result, with_advanced_fields=True))  # merge temporary result
        return jsonify(test_obj), 201
    except (SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/submissions/<int:sid>/auto-tests/<int:tid>', methods=['DELETE'])
@requires_admin
def admin_delete_test(sid, tid):
    try:
        submission = SubmissionService.get(sid)
        if submission is None:
            return jsonify(msg='submission not found'), 404

        test = AutoTestService.get(tid)

        data_folder = app.config['DATA_FOLDER']
        for file in test.output_files:
            save_path_full = os.path.join(data_folder, file.save_path)
            if os.path.lexists(save_path_full):
                os.remove(save_path_full)
        if test.output_files:  # try to remove parent folder if empty now
            folder_path = os.path.dirname(test.output_files[0].save_path)
            folder_path_full = os.path.join(data_folder, folder_path)
            if os.path.lexists(folder_path_full) and not os.listdir(folder_path_full):
                os.rmdir(folder_path_full)

        result = AutoTestService.get_result(test)
        result.forget()  # remove temporary result from storage (if any)

        for file in test.output_files:
            db.session.delete(file)
        db.session.delete(test)
        db.session.commit()
        return "", 204
    except (SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/auto-test-configs/<int:cid>/run', methods=['GET'])
@requires_admin
def admin_run_auto_test(cid):
    try:
        config = TaskService.get_auto_test_config(cid)
        if config is None:
            return jsonify(msg='auto test config not found'), 404

        task = config.task

        filters = [
            Submission.task_id == task.id,
            Submission.is_cleared == False
        ]

        last_submissions_only = request.args.get('last_submissions_only') == 'true'

        if task.is_team_task:
            team_id = request.args.get('team_id')
            if team_id is not None:
                try:
                    team_id = int(team_id)
                except (ValueError, TypeError):
                    return jsonify(msg='team id must be an integer'), 400
                team = TeamService.get(team_id)
                if team is None:
                    return jsonify(msg='team not found'), 404
                if team.task_id != task.id:
                    return jsonify(msg='team does not belong to this task'), 400
                filters.extend([UserTeamAssociation.team_id == team_id,
                                UserTeamAssociation.user_id == Submission.submitter_id])

            if last_submissions_only:
                if team_id is not None:
                    last_sid = db.session.query(func.max(Submission.id).label('sid')).filter(*filters).subquery()
                    submissions = db.session.query(Submission).filter(Submission.id == last_sid.c.sid)
                else:
                    filters.extend([UserTeamAssociation.user_id == Submission.submitter_id,
                                    UserTeamAssociation.team_id == Team.id,
                                    Team.task_id == task.id])
                    last_sids = db.session.query(UserTeamAssociation.team_id, func.max(Submission.id).label('sid'))\
                        .filter(*filters)\
                        .group_by(UserTeamAssociation.team_id).subquery()
                    submissions = db.session.query(Submission).filter(Submission.id == last_sids.c.sid)
            else:
                submissions = db.session.query(Submission).filter(*filters).order_by(Submission.id)
        else:
            user_id = request.args.get('user_id')
            if user_id is not None:
                try:
                    user_id = int(user_id)
                except (ValueError, TypeError):
                    return jsonify(msg='user id must be an integer'), 400
                filters.append(Submission.submitter_id == user_id)

            if last_submissions_only:
                if user_id is not None:
                    last_sid = db.session.query(func.max(Submission.id).label('sid')).filter(*filters).subquery()
                    submissions = db.session.query(Submission).filter(Submission.id == last_sid.c.sid)
                else:
                    last_sids = db.session.query(Submission.submitter_id, func.max(Submission.id).label('sid')) \
                        .filter(*filters) \
                        .group_by(Submission.submitter_id).subquery()
                    submissions = db.session.query(Submission).filter(Submission.id == last_sids.c.sid)
            else:
                submissions = db.session.query(Submission).filter(*filters).order_by(Submission.id)

        result_tuples = []
        for submission in submissions:
            result_tuples.append(SubmissionService.run_auto_test(submission, config))
        db.session.commit()

        ret = []
        for test, result in result_tuples:
            test_obj = test.to_dict(with_advanced_fields=True)
            test_obj.update(AutoTestService.result_to_dict(result, with_advanced_fields=True))  # merge temporary result
            ret.append(test_obj)
        return jsonify(ret), 201
    except (SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
