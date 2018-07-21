from sqlalchemy import or_

from error import BasicError
from models import Course, db, GroupCourseAssociation, UserCourseAssociation


class CourseServiceError(BasicError):
    pass


class CourseService:
    code_max_length = 16
    name_max_length = 128
    description_max_length = 512
    profile_fields = {
        'icon'
    }
    user_roles = {'lecturer'}
    group_roles = {}  # will use group roles if necessary in the future

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
        return GroupCourseAssociation.query.with_parent(course).all()

    @classmethod
    def add_user_association(cls, course, user, role):
        if course is None:
            raise CourseServiceError('course is required')
        if user is None:
            raise CourseServiceError('user is required')
        if role is None:
            raise CourseServiceError('role is required')

        if role not in cls.user_roles:
            raise CourseServiceError('invalid role')
        if UserCourseAssociation.query.filter_by(user_id=user.id, course_id=course.id, role=role).count():
            raise CourseServiceError('already has role')
        db.session.add(UserCourseAssociation(user=user, course=course, role=role))

    @classmethod
    def add_group_association(cls, course, group, role):
        if course is None:
            raise CourseServiceError('course is required')
        if group is None:
            raise CourseServiceError('group is required')
        if role is None:
            raise CourseServiceError('role is required')

        if role not in cls.group_roles:
            raise CourseServiceError('invalid role')
        if GroupCourseAssociation.query.filter_by(group_id=group.id, course_id=course.id, role=role).count():
            raise CourseServiceError('already has role')
        db.session.add(GroupCourseAssociation(group=group, course=course, role=role))

    @classmethod
    def remove_user_association(cls, course, user, role):
        if course is None:
            raise CourseServiceError('course is required')
        if user is None:
            raise CourseServiceError('user is required')
        if role is None:
            raise CourseServiceError('role is required')

        if role not in cls.user_roles:
            raise CourseServiceError('invalid role')
        asso = UserCourseAssociation.query.filter_by(user_id=user.id, course_id=course.id, role=role).first()
        if asso is None:
            raise CourseServiceError('no such role')
        db.session.delete(asso)

    @classmethod
    def remove_group_association(cls, course, group, role):
        if course is None:
            raise CourseServiceError('course is required')
        if group is None:
            raise CourseServiceError('group is required')
        if role is None:
            raise CourseServiceError('role is required')

        if role not in cls.group_roles:
            raise CourseServiceError('invalid role')
        asso = GroupCourseAssociation.query.filter_by(group_id=group.id, course_id=course.id, role=role).first()
        if asso is None:
            raise CourseServiceError('no such role')
        db.session.delete(asso)
