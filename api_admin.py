from flask import Blueprint, jsonify, request

from models import db
from oauth import requires_admin
from services.account import AccountService, AccountServiceError
from services.course import CourseService, CourseServiceError
from services.team import TeamService, TeamServiceError
from services.term import TermService, TermServiceError
from utils.upload import handle_upload, handle_post_upload, UploadError

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
            course = CourseService.add(params.get('code'), params.get('name'))
            db.session.commit()
            return jsonify(course.to_dict(with_advanced_fields=True)), 201
    except CourseServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/courses/<int:cid>', methods=['GET', 'PUT', 'DELETE'])
@requires_admin
def admin_course(cid):
    try:
        course = CourseService.get(cid)
        if course is None:
            return jsonify(msg='course not found'), 404
        if request.method == 'GET':
            return jsonify(course.to_dict(with_terms=True, with_associations=True, with_advanced_fields=True))
        elif request.method == 'PUT':
            params = request.json or request.form or {}
            files = request.files
            upload_type = 'icon'
            if 'icon' in files:
                params['icon'] = handle_upload(files['icon'], upload_type,
                                               image_check=True, image_check_squared=True)
            old = CourseService.update(course, **params)
            if 'icon' in old:
                handle_post_upload(old['icon'], upload_type)
            db.session.commit()
            return jsonify(course.to_dict(with_terms=True, with_associations=True, with_advanced_fields=True))
        else:  # DELETE
            db.session.delete(course)
            db.session.commit()
            return "", 204
    except (CourseServiceError, UploadError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/courses/<int:course_id>/users/<int:uid>/<role>', methods=['PUT', 'DELETE'])
@requires_admin
def admin_course_user(course_id, uid, role):
    try:
        course = CourseService.get(course_id)
        if course is None:
            return jsonify(msg='course not found'), 404
        user = AccountService.get_user(uid)
        if user is None:
            return jsonify(msg='user not found'), 404

        if request.method == 'PUT':
            CourseService.add_user_association(course, user, role)
        else:  # DELETE
            CourseService.remove_user_association(course, user, role)
        db.session.commit()
        return "", 204
    except CourseServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/courses/<int:course_id>/groups/<int:gid>/<role>', methods=['PUT', 'DELETE'])
@requires_admin
def admin_course_group(course_id, gid, role):
    try:
        course = CourseService.get(course_id)
        if course is None:
            return jsonify(msg='course not found'), 404
        group = AccountService.get_group(gid)
        if group is None:
            return jsonify(msg='group not found'), 404

        if request.method == 'PUT':
            CourseService.add_group_association(course, group, role)
        else:  # DELETE
            CourseService.remove_group_association(course, group, role)
        db.session.commit()
        return "", 204
    except CourseServiceError as e:
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
            term = TermService.add(course, params.get('year'), params.get('semester'))
            db.session.commit()
            return jsonify(term.to_dict(with_advanced_fields=True)), 201
    except (CourseServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/terms/<int:term_id>', methods=['GET', 'DELETE'])
@requires_admin
def admin_term(term_id):
    try:
        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404

        if request.method == 'GET':
            return jsonify(term.to_dict(with_course=True, with_associations=True, with_advanced_fields=True))
        else:  # DELETE
            db.session.delete(term)
            db.session.commit()
            return "", 204
    except TermServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/terms/<int:term_id>/users/<int:uid>/<role>', methods=['PUT', 'DELETE'])
@requires_admin
def admin_term_user(term_id, uid, role):
    try:
        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404
        user = AccountService.get_user(uid)
        if user is None:
            return jsonify(msg='user not found'), 404

        if request.method == 'PUT':
            TermService.add_user_association(term, user, role)
        else:  # DELETE
            TermService.remove_user_association(term, user, role)
        db.session.commit()
        return "", 204
    except TermServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/terms/<int:term_id>/groups/<int:gid>/<role>', methods=['PUT', 'DELETE'])
@requires_admin
def admin_term_group(term_id, gid, role):
    try:
        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404
        group = AccountService.get_group(gid)
        if group is None:
            return jsonify(msg='group not found'), 404

        if request.method == 'PUT':
            TermService.add_group_association(term, group, role)
        else:  # DELETE
            TermService.remove_group_association(term, group, role)
        db.session.commit()
        return "", 204
    except TermServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/terms/<int:term_id>/teams', methods=['GET', 'POST'])
@requires_admin
def admin_teams(term_id):
    try:
        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404

        if request.method == 'GET':
            return [t.to_dict(with_advanced_fields=True) for t in TeamService.get_for_term(term)]
        else:  # POST
            params = request.json
            name = params.get('name')
            team = TeamService.add(term, None, name)
            db.session.commit()
            return jsonify(team.to_dict(with_advanced_fields=True)), 201
    except TeamServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/teams/<int:team_id>', methods=['GET', 'PUT', 'DELETE'])
@requires_admin
def admin_team(team_id):
    try:
        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        if request.method == 'GET':
            return team.to_dict(with_advanced_fields=True)
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
            return jsonify(team.to_dict())
        else:  # DELETE
            db.session.delete(team)
            db.session.commit()
    except (TeamServiceError, UploadError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
