from sqlalchemy import or_

from error import BasicError
from models import Course, db, GroupCourseAssociations


class CourseServiceError(BasicError):
    pass


class CourseService:
    code_max_length = 16
    name_max_length = 128
    description_max_length = 512
    profile_fields = {
        'icon'
    }

    @staticmethod
    def get(_id):
        if _id is None:
            raise CourseServiceError('id is required')
        if type(_id) is not int:
            raise CourseServiceError('id must be an integer')

        return Course.query.get(_id)

    @staticmethod
    def get_all():
        return Course.query.all()

    @staticmethod
    def add(code, name):
        if code is None:
            raise CourseServiceError('code is required')
        if name is None:
            raise CourseServiceError('name is required')
        if Course.query.filter(or_(Course.code == code, Course.name == name)).count():
            raise CourseServiceError('duplicate code or name')

        if len(code) > CourseService.code_max_length:
            raise CourseServiceError('code too long')
        if len(name) > CourseService.name_max_length:
            raise CourseServiceError('name too long')

        course = Course(code=code, name=name)
        db.session.add(course)
        return course

    @staticmethod
    def update(course, **kwargs):
        if course is None:
            raise CourseServiceError('course is required')
        for k in kwargs:
            if k not in CourseService.profile_fields:
                raise CourseServiceError('invalid field', k)
        old = {k: getattr(course, k) for k in kwargs}
        for k, v in kwargs.items():
            setattr(course, k, v)
        return old

    @staticmethod
    def get_group_associations(course):
        return GroupCourseAssociations.query.with_parent(course).all()
