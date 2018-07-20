from flask import Blueprint, jsonify, request

from models import db
from oauth import requires_login, get_user
from services.course import CourseService, CourseServiceError
from services.team import TeamService, TeamServiceError
from services.term import TermService, TermServiceError
from utils.upload import handle_upload, handle_post_upload, UploadError

admin_api = Blueprint('admin_api', __name__)


@admin_api.before_request
def check_admin():
    user = get_user()
    if user is None:
        return jsonify(msg='no user info'), 403
    if not any(g.name == 'admin' for g in user.groups):
        return jsonify(msg='admin required'), 403


@admin_api.route('/courses', methods=['GET', 'POST'])
@requires_login
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
@requires_login
def admin_course(cid):
    try:
        course = CourseService.get(cid)
        if course is None:
            return jsonify(msg='course not found'), 404
        if request.method == 'GET':
            return jsonify(course.to_dict(with_advanced_fields=True))
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
            return jsonify(course.to_dict())
        else:  # DELETE
            db.session.delete(course)
            db.session.commit()
            return "", 204
    except (CourseServiceError, UploadError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/courses/<int:cid>/terms', methods=['GET', 'POST'])
@requires_login
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
@requires_login
def admin_term(term_id):
    try:
        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404

        if request.method == 'GET':
            return jsonify(term.to_dict(with_advanced_fields=True))
        else:  # DELETE
            db.session.delete(term)
            db.session.commit()
            return "", 204
    except TermServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@admin_api.route('/terms/<int:term_id>/teams', methods=['GET', 'POST'])
@requires_login
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
@requires_login
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
