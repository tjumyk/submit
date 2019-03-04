from flask import Blueprint, jsonify

from auth_connect.oauth import requires_login
from services.course import CourseService, CourseServiceError
from services.term import TermService, TermServiceError

course_api = Blueprint('course_api', __name__)


@course_api.route('', methods=['GET'])
@requires_login
def do_courses():
    try:
        return jsonify([t.to_dict(with_terms=True) for t in CourseService.get_all()])
    except CourseServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@course_api.route('/<int:cid>/terms', methods=['GET'])
@requires_login
def course_terms(cid):
    course = CourseService.get(cid)
    if course is None:
        return jsonify('course not found'), 404

    try:
        return jsonify([t.to_dict() for t in TermService.get_for_course(course)])
    except TermServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 500
