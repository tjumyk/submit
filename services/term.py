from sqlalchemy.orm import joinedload

from error import BasicError
from models import Term, UserAlias, db


class TermServiceError(BasicError):
    pass


class TermService:
    @staticmethod
    def get(_id):
        if _id is None:
            raise TermServiceError('id is required')
        if type(_id) is not int:
            raise TermServiceError('id must be an integer')

        return Term.query.get(_id)

    @staticmethod
    def get_for_user(user: UserAlias):
        if user is None:
            raise TermServiceError('user is required')
        return Term.query.options(joinedload('group_associations')) \
            .filter(UserAlias.id == user.id).all()

    @staticmethod
    def get_for_course(course):
        return Term.query.with_parent(course).all()

    @staticmethod
    def get_all():
        return Term.query.all()

    @staticmethod
    def add(course, year, semester):
        if course is None:
            raise TermServiceError('course is required')
        if year is None:
            raise TermServiceError('year is required')
        if semester is None:
            raise TermServiceError('semester is required')
        if type(year) is not int:
            raise TermServiceError('year is not an integer')

        term = Term(course=course, year=year, semester=semester)
        db.session.add(term)
        return term

    @staticmethod
    def is_user_eligible(term, user, role=None):
        # FIXME inefficient
        # GroupTermAssociations.query.options(joinedload('group.users'))\
        #     .filter(UserAlias.id==user.id)
        if not any(term == asso.term and (role is None or role == asso.role)
                   for g in user.groups
                   for asso in g.term_associations):
            return False
        return True
