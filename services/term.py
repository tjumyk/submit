from typing import Optional, List

from sqlalchemy.orm import joinedload

from error import BasicError
from models import Term, UserAlias, db, GroupTermAssociation, UserTermAssociation


class TermServiceError(BasicError):
    pass


class TermService:
    user_roles = {'tutor', 'marker', 'student'}
    group_roles = {'tutor', 'marker', 'student'}

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
    def add(course, year, semester) -> Term:
        if course is None:
            raise TermServiceError('course is required')
        if year is None:
            raise TermServiceError('year is required')
        if semester is None:
            raise TermServiceError('semester is required')
        if type(year) is not int:
            raise TermServiceError('year is not an integer')

        if Term.query.filter(Term.course_id == course.id, Term.year == year, Term.semester == semester).count():
            raise TermServiceError('duplicate term')

        term = Term(course=course, year=year, semester=semester)
        db.session.add(term)
        return term

    @classmethod
    def add_user_association(cls, term, user, role):
        if term is None:
            raise TermServiceError('term is required')
        if user is None:
            raise TermServiceError('user is required')
        if role is None:
            raise TermServiceError('role is required')

        if role not in cls.user_roles:
            raise TermServiceError('invalid role')
        if UserTermAssociation.query.filter_by(user_id=user.id, term_id=term.id, role=role).count():
            raise TermServiceError('already has role')
        db.session.add(UserTermAssociation(user=user, term=term, role=role))

    @classmethod
    def add_group_association(cls, term, group, role):
        if term is None:
            raise TermServiceError('term is required')
        if group is None:
            raise TermServiceError('group is required')
        if role is None:
            raise TermServiceError('role is required')

        if role not in cls.group_roles:
            raise TermServiceError('invalid role')
        if GroupTermAssociation.query.filter_by(group_id=group.id, term_id=term.id, role=role).count():
            raise TermServiceError('already has role')
        db.session.add(GroupTermAssociation(group=group, term=term, role=role))

    @classmethod
    def remove_user_association(cls, term, user, role):
        if term is None:
            raise TermServiceError('term is required')
        if user is None:
            raise TermServiceError('user is required')
        if role is None:
            raise TermServiceError('role is required')

        if role not in cls.user_roles:
            raise TermServiceError('invalid role')
        asso = UserTermAssociation.query.filter_by(user_id=user.id, term_id=term.id, role=role).first()
        if asso is None:
            raise TermServiceError('no such role')
        db.session.delete(asso)

    @classmethod
    def remove_group_association(cls, term, group, role):
        if term is None:
            raise TermServiceError('term is required')
        if group is None:
            raise TermServiceError('group is required')
        if role is None:
            raise TermServiceError('role is required')

        if role not in cls.group_roles:
            raise TermServiceError('invalid role')
        asso = GroupTermAssociation.query.filter_by(group_id=group.id, term_id=term.id, role=role).first()
        if asso is None:
            raise TermServiceError('no such role')
        db.session.delete(asso)

    @staticmethod
    def is_user_eligible(term, user, role=None) -> bool:
        # FIXME inefficient
        # GroupTermAssociations.query.options(joinedload('group.users'))\
        #     .filter(UserAlias.id==user.id)
        if not any(term == asso.term and (role is None or role == asso.role)
                   for g in user.groups
                   for asso in g.term_associations):
            return False
        return True
