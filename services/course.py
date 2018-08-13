from typing import Optional, List

import oauth
from sqlalchemy import or_, func

from error import BasicError
from models import Course, db
from services.account import AccountService


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
    def get(_id) -> Optional[Course]:
        if _id is None:
            raise CourseServiceError('id is required')
        if type(_id) is not int:
            raise CourseServiceError('id must be an integer')

        return Course.query.get(_id)

    @staticmethod
    def get_all() -> List[Course]:
        return Course.query.all()

    @staticmethod
    def add(code, name, tutor_group_name, is_new_tutor_group=True) -> Course:
        if code is None:
            raise CourseServiceError('code is required')
        if name is None:
            raise CourseServiceError('name is required')
        if not tutor_group_name:
            raise CourseServiceError('tutor group name is required')

        if len(code) > CourseService.code_max_length:
            raise CourseServiceError('code too long')
        if len(name) > CourseService.name_max_length:
            raise CourseServiceError('name too long')

        if db.session.query(func.count()).filter(or_(Course.code == code, Course.name == name)).scalar():
            raise CourseServiceError('duplicate code or name')

        if is_new_tutor_group:
            tutor_group = AccountService.add_group(tutor_group_name, 'Tutor of %s' % code)
        else:
            tutor_group = AccountService.get_group_by_name(tutor_group_name)
            if tutor_group is None:
                raise CourseServiceError('tutor group not found')

        course = Course(code=code, name=name, tutor_group=tutor_group)
        db.session.add(course)
        return course

    @staticmethod
    def update(course, **kwargs) -> dict:
        if course is None:
            raise CourseServiceError('course is required')
        for k in kwargs:
            if k not in CourseService.profile_fields:
                raise CourseServiceError('invalid field', k)
        old = {k: getattr(course, k) for k in kwargs}
        for k, v in kwargs.items():
            setattr(course, k, v)
        return old

