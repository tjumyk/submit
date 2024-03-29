from typing import Optional, List

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from error import BasicError
from models import Term, UserAlias, db
from services.account import AccountService


class TermServiceError(BasicError):
    pass


class TermService:
    @staticmethod
    def get(_id) -> Optional[Term]:
        if _id is None:
            raise TermServiceError('id is required')
        if type(_id) is not int:
            raise TermServiceError('id must be an integer')

        return Term.query.get(_id)

    @staticmethod
    def get_for_user(user: UserAlias) -> List[Term]:
        if user is None:
            raise TermServiceError('user is required')
        return Term.query.options(joinedload('group_associations')) \
            .filter(UserAlias.id == user.id).all()

    @staticmethod
    def get_for_course(course) -> List[Term]:
        return Term.query.with_parent(course).all()

    @staticmethod
    def get_all() -> List[Term]:
        return Term.query.all()

    @staticmethod
    def add(course, year, semester, student_group_name, is_new_student_group=True) -> Term:
        if course is None:
            raise TermServiceError('course is required')
        if year is None:
            raise TermServiceError('year is required')
        if semester is None:
            raise TermServiceError('semester is required')
        if type(year) is not int:
            raise TermServiceError('year is not an integer')
        if not student_group_name:
            raise TermServiceError('student group name is required')

        if db.session.query(func.count()).filter(Term.course_id == course.id,
                                                 Term.year == year,
                                                 Term.semester == semester).scalar():
            raise TermServiceError('duplicate term')

        if is_new_student_group:
            student_group = AccountService.add_group(student_group_name,
                                                     'Students of %s %dS%s' % (course.code, year, semester))
        else:
            student_group = AccountService.get_group_by_name(student_group_name)
            if student_group is None:
                raise TermServiceError('student group not found')

        term = Term(course=course, year=year, semester=semester, student_group=student_group)
        db.session.add(term)
        return term

    @staticmethod
    def get_access_roles(term, user) -> set:
        if term is None:
            raise TermServiceError('term is required')
        if user is None:
            raise TermServiceError('user is required')

        roles = set()
        for g in user.groups:
            if g.name == 'admin':
                roles.add('admin')
            if g.id == term.student_group_id:
                roles.add('student')
            if g.id == term.course.tutor_group_id:
                roles.add('tutor')
        return roles
