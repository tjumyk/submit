import os
import re
import shutil
import tempfile
import zipfile

from flask import Blueprint, jsonify, request, current_app as app, send_from_directory, json
from sqlalchemy import func

from auth_connect.oauth import requires_admin
from models import db, Submission, UserTeamAssociation, Team, SubmissionFile, AutoTest
from services.account import AccountService, AccountServiceError
from services.auto_test import AutoTestService, AutoTestServiceError
from services.course import CourseService, CourseServiceError
from services.final_marks import FinalMarksService, FinalMarksServiceError
from services.message_sender import MessageSenderService, MessageSenderServiceError
from services.messsage import MessageService, MessageServiceError
from services.submission import SubmissionService, SubmissionServiceError
from services.task import TaskService, TaskServiceError
from services.team import TeamService, TeamServiceError
from services.term import TermService, TermServiceError
from utils.give import GiveImporter, GiveImporterError
from utils.message import build_message_with_template
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


@admin_api.route('/users/<int:uid>/sync')
@requires_admin
def admin_user_sync(uid):
    try:
        user = AccountService.get_user(uid)
        if user is None:
            return jsonify(msg='user not found'), 404

        user_alias = AccountService.sync_user_by_id(user.id)
        db.session.commit()
        return jsonify(user_alias.to_dict())
    except AccountServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/groups/<int:gid>/sync')
@requires_admin
def admin_group_sync(gid):
    try:
        group = AccountService.get_group(gid)
        if group is None:
            return jsonify(msg='group not found'), 404

        group_alias = AccountService.sync_group_by_id(group.id, sync_group_users=True)
        db.session.commit()
        return jsonify(group_alias.to_dict(with_user_ids=True))
    except AccountServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


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

        return send_from_directory(app.config['DATA_FOLDER'], material.file_path, as_attachment=True, max_age=0)
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
        skip_successful = request.args.get('skip_successful') == 'true'

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
                    last_sids = db.session.query(UserTeamAssociation.team_id, func.max(Submission.id).label('sid')) \
                        .filter(*filters) \
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

        if skip_successful:
            last_tids = db.session.query(AutoTest.submission_id, func.max(AutoTest.id).label('tid')) \
                .filter(AutoTest.submission_id.in_([s.id for s in submissions]),
                        AutoTest.config_id == config.id) \
                .group_by(AutoTest.submission_id).subquery()
            successful_sids = set(r[0] for r in db.session.query(AutoTest.submission_id) \
                                  .filter(AutoTest.id == last_tids.c.tid, AutoTest.final_state == 'SUCCESS').all())
            submissions = [s for s in submissions if s.id not in successful_sids]

        result_tuples = []
        for submission in submissions:
            result_tuples.append(SubmissionService.run_auto_test(submission, config))
        db.session.commit()

        ret = []
        for test, result in result_tuples:
            test_obj = test.to_dict(with_advanced_fields=True)
            test_obj.update(AutoTestService.result_to_dict(result, with_advanced_fields=True))  # merge temporary result
            ret.append(test_obj)
        return jsonify(ret), 200
    except (SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/tasks/<int:tid>/final-marks', methods=['POST'])
@requires_admin
def do_final_marks(tid):
    try:
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404

        params = request.json
        user = AccountService.get_user(params.get('user_id'))
        if user is None:
            return jsonify(msg='user not found'), 404
        record = FinalMarksService.set(task, user, params.get('marks'), params.get('comment'))

        db.session.commit()
        return jsonify(record.to_dict(with_comment=True, with_advanced_fields=True))
    except (AccountServiceError, TaskServiceError, FinalMarksServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/tasks/<int:tid>/batch-final-marks', methods=['POST'])
@requires_admin
def do_batch_final_marks(tid):
    try:
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404

        data = request.json
        user_names = [row[0] for row in data]
        if len(set(user_names)) != len(user_names):
            return jsonify(msg='duplicate user names in list'), 400
        users = AccountService.get_user_by_name_list(user_names)
        if len(users) != len(user_names):
            return jsonify(msg='some users not found'), 400
        processed_data = []
        for user_name, marks, comment in data:
            processed_data.append((users[user_name], marks, comment))
        new_records, updated_records = FinalMarksService.batch_set(task, processed_data)

        db.session.commit()
        return jsonify(new=len(new_records), updated=len(updated_records))
    except (AccountServiceError, TaskServiceError, FinalMarksServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/tasks/<int:tid>/release-final-marks')
@requires_admin
def release_final_marks(tid):
    try:
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404

        FinalMarksService.release(task)

        term = task.term
        mail_args = dict(site=app.config['SITE'], term=term, task=task)
        msg_content = build_message_with_template('task_final_marks_released', mail_args)
        msg_channel = MessageService.get_channel_by_name('task')
        msg, mails = MessageSenderService.send_to_group(msg_channel, term, msg_content, None, term.student_group)

        db.session.commit()
        for mail in mails:
            mail.send()
        return "", 204
    except (TaskServiceError, FinalMarksServiceError, MessageServiceError, MessageSenderServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/auto-test-summaries')
@requires_admin
def auto_test_summaries():
    try:
        return jsonify(AutoTestService.get_summaries(with_advanced_fields=True))
    except AutoTestServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/tasks/<int:tid>/import-give', methods=['POST'])
@requires_admin
def import_give(tid: int):
    try:
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404

        archive = request.files.get('archive')
        if not archive:
            return jsonify(msg='archive file is required'), 400

        requirement_map = {r.name: r for r in task.file_requirements}
        data_folder = app.config['DATA_FOLDER']

        num_submitters = 0
        num_imported_submissions = 0
        num_skipped_submissions = 0
        with tempfile.TemporaryDirectory() as work_dir:
            archive_path = os.path.join(work_dir, archive.filename)
            archive.save(archive_path)
            extract_dir = os.path.join(work_dir, '_extract')
            os.mkdir(extract_dir)

            copy_info = []
            importer = GiveImporter(requirement_map.keys())
            for student_id, submissions_info in importer.import_archive(archive_path, extract_dir):
                student = AccountService.sync_user_by_name(student_id)

                existing_created_at = {
                    row[0] for row in db.session.query(Submission.created_at)
                    .filter(Submission.task_id == task.id,
                            Submission.submitter_id == student.id)
                    .all()
                }
                for idx, (_time, files) in enumerate(submissions_info):
                    if _time in existing_created_at:
                        num_skipped_submissions += 1
                        continue  # avoid re-importing same submission

                    # add suffix to each timestamp to avoid path conflict
                    _timestamp = str(_time.timestamp()) + str(idx)
                    save_folder = os.path.join('tasks', str(task.id), 'submissions', student.name, _timestamp)
                    new_submission = Submission(task_id=task.id, submitter_id=student.id,
                                                created_at=_time, modified_at=_time)
                    db.session.add(new_submission)

                    for file_name, tmp_path in files.items():
                        requirement = requirement_map[file_name]
                        save_path = os.path.join(save_folder, file_name)
                        size = os.stat(tmp_path).st_size
                        md5 = md5sum(tmp_path)
                        new_file = SubmissionFile(submission=new_submission, requirement_id=requirement.id,
                                                  path=save_path, size=size, md5=md5,
                                                  created_at=_time, modified_at=_time)
                        db.session.add(new_file)
                        copy_info.append((tmp_path, save_path))
                    num_imported_submissions += 1
                num_submitters += 1

            # do actual file copies at last
            for tmp_path, save_path in copy_info:
                to_path = os.path.join(data_folder, save_path)
                to_dir_path = os.path.dirname(to_path)
                if not os.path.exists(to_dir_path):
                    os.makedirs(to_dir_path)
                shutil.copy(tmp_path, to_path)

        db.session.commit()
        return jsonify(num_submitters=num_submitters, num_imported_submissions=num_imported_submissions,
                       num_skipped_submissions=num_skipped_submissions)
    except (TaskServiceError, GiveImporterError, AccountServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/tasks/<int:tid>/export-submissions')
@requires_admin
def export_submissions(tid: int):
    try:
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404

        data_folder = app.config['DATA_FOLDER']
        with tempfile.TemporaryDirectory() as tmp_dir:
            term = task.term
            zip_name = '%s-%dS%s-%s.zip' % (term.course.code, term.year, term.semester, task.title)
            zip_path = os.path.join(tmp_dir, zip_name)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as f_zip:
                for sub in task.submissions:
                    if sub.is_cleared:
                        continue
                    submitter_name = sub.submitter.name
                    submission_folder = os.path.join('submissions', submitter_name, str(sub.created_at))
                    for sub_file in sub.files:
                        f_zip.write(os.path.join(data_folder, sub_file.path),
                                    os.path.join(submission_folder, sub_file.requirement.name))
                if task.is_team_task:
                    teams_info = []
                    for team in TeamService.get_for_task(task, joined_load_user_associations=True):
                        member_names = [ass.user.name for ass in team.user_associations]
                        teams_info.append(dict(name=team.name, members=member_names))
                    f_zip.writestr('teams.json', json.dumps(teams_info))
            return send_from_directory(tmp_dir, zip_name, as_attachment=True, download_name=zip_name,
                                       max_age=0)
    except (TaskServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400

