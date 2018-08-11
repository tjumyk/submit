import re
from typing import Optional, List

from error import BasicError
from models import Team, db, UserTeamAssociation, UserAlias


class TeamServiceError(BasicError):
    pass


class TeamService:
    name_pattern = re.compile('^[\w]{3,16}$')
    slogan_max_length = 64
    profile_fields = {
        'slogan',
        'avatar'
    }

    @staticmethod
    def get(_id)->Optional[Team]:
        if _id is None:
            raise TeamServiceError('id is required')
        if type(_id) is not int:
            raise TeamServiceError('id must be an integer')

        return Team.query.get(_id)

    @staticmethod
    def get_all()->List[Team]:
        return Team.query.all()

    @staticmethod
    def get_for_term(term)->List[Team]:
        if term is None:
            raise TeamServiceError('term is required')
        return Team.query.with_parent(term).all()

    @staticmethod
    def get_for_user(user)->List[UserTeamAssociation]:
        if user is None:
            raise TeamServiceError('user is required')
        return UserTeamAssociation.query.with_parent(user).all()

    @staticmethod
    def add(term, name, creator=None)->Team:
        if term is None:
            raise TeamServiceError('term is required')
        if name is None:
            raise TeamServiceError('name is required')

        from .term import TermService
        if not TermService.is_user_eligible(term, creator, 'student'):
            raise TeamServiceError('user not eligible')

        if Team.query.filter_by(name=name).count():
            raise TeamServiceError('duplicate name')
        if not TeamService.name_pattern.match(name):
            raise TeamServiceError('invalid name format')
        team = Team(term=term, name=name)
        if creator:
            asso = UserTeamAssociation(user=creator, team=team, is_creator=True,
                                       is_user_agreed=True, is_creator_agreed=True)
            db.session.add(asso)
        return team

    @staticmethod
    def get_creator(team)->Optional[UserAlias]:
        asso = UserTeamAssociation.query.with_parent(team).filter_by(is_creator=True).first()
        if not asso:
            return None
        return asso.user

    @staticmethod
    def is_user_eligible(team, user):
        if team is None:
            raise TeamServiceError('team is required')
        if user is None:
            raise TeamServiceError('user is required')

        from .term import TermService
        return TermService.is_user_eligible(team.term, user, 'student')

    @staticmethod
    def get_user_associations(team)->List[UserTeamAssociation]:
        if team is None:
            raise TeamServiceError('team is required')
        return UserTeamAssociation.query.with_parent(team).all()

    @staticmethod
    def update(team, **kwargs)->dict:
        if team is None:
            raise TeamServiceError('team is required')

        for k in kwargs:
            if k not in TeamService.profile_fields:
                raise TeamServiceError('invalid field', k)
        old_values = {k: getattr(team, k) for k, v in kwargs.items()}
        for k, v in kwargs.items():
            if k == 'slogan':
                if len(k) > TeamService.slogan_max_length:
                    raise TeamServiceError('slogan too long')
            setattr(team, k, v)
        return old_values

    @staticmethod
    def dismiss(team):
        if team.is_finalised:
            raise TeamServiceError('team already finalised')
        db.session.delete(team)

    @staticmethod
    def invite(team, user):
        if team is None:
            raise TeamServiceError('team is required')
        if user is None:
            raise TeamServiceError('user is required')

        if team.is_finalised:
            raise TeamServiceError('team already finalised')

        user_team = UserTeamAssociation.query.filter_by(user_id=user.id, team_id=team.id).first()
        if user_team is not None:
            raise TeamServiceError('user already associated with team')
        if not TeamService.is_user_eligible(team, user):
            raise TeamServiceError('user not eligible')
        user_team = UserTeamAssociation(user_id=user.id, team_id=team.id, is_creator_agreed=True, is_invited=True)
        db.session.add(user_team)

    @staticmethod
    def cancel_invitation(team, user):
        if team is None:
            raise TeamServiceError('team is required')
        if user is None:
            raise TeamServiceError('user is required')

        if team.is_finalised:
            raise TeamServiceError('team already finalised')

        user_team = UserTeamAssociation.query.filter_by(user_id=user.id, team_id=team.id).first()
        if user_team is None:
            raise TeamServiceError('user not associated with team')
        if not user_team.is_invited:
            raise TeamServiceError('user was not invited to the team')
        if user_team.is_user_agreed:
            raise TeamServiceError('user already agreed')
        db.session.delete(user_team)

    @staticmethod
    def agree_invitation(team, user):
        if team is None:
            raise TeamServiceError('team is required')
        if user is None:
            raise TeamServiceError('user is required')

        if team.is_finalised:
            raise TeamServiceError('team already finalised')

        user_team = UserTeamAssociation.query.filter_by(user_id=user.id, team_id=team.id).first()
        if user_team is None:
            raise TeamServiceError('user not associated with team')
        if not user_team.is_invited:
            raise TeamServiceError('user was not invited to the team')
        if user_team.is_user_agreed:
            raise TeamServiceError('user already agreed')
        user_team.is_user_agreed = True

    @staticmethod
    def apply_join(team, user):
        if team is None:
            raise TeamServiceError('team is required')
        if user is None:
            raise TeamServiceError('user is required')

        if team.is_finalised:
            raise TeamServiceError('team already finalised')

        user_team = UserTeamAssociation.query.filter_by(user_id=user.id, team_id=team.id).first()
        if user_team is not None:
            raise TeamServiceError('user already associated with team')
        if not TeamService.is_user_eligible(team, user):
            raise TeamServiceError('user not eligible')
        user_team = UserTeamAssociation(user_id=user.id, team_id=team.id, is_user_agreed=True, is_invited=False)
        db.session.add(user_team)

    @staticmethod
    def cancel_join_application(team, user):
        if team is None:
            raise TeamServiceError('team is required')
        if user is None:
            raise TeamServiceError('user is required')

        if team.is_finalised:
            raise TeamServiceError('team already finalised')

        user_team = UserTeamAssociation.query.filter_by(user_id=user.id, team_id=team.id).first()
        if user_team is None:
            raise TeamServiceError('user not associated with team')
        if user_team.is_invited:
            raise TeamServiceError('user was invited to the team')
        if user_team.is_creator_agreed:
            raise TeamServiceError('team creator already agreed')
        db.session.delete(user_team)

    @staticmethod
    def agree_join_application(team, user):
        if team is None:
            raise TeamServiceError('team is required')
        if user is None:
            raise TeamServiceError('user is required')

        if team.is_finalised:
            raise TeamServiceError('team already finalised')

        user_team = UserTeamAssociation.query.filter_by(user_id=user.id, team_id=team.id).first()
        if user_team is None:
            raise TeamServiceError('user not associated with team')
        if user_team.is_invited:
            raise TeamServiceError('user was invited to the team')
        if user_team.is_creator_agreed:
            raise TeamServiceError('team creator already agreed')
        user_team.is_creator_agreed = True


    @staticmethod
    def finalise(team):
        if team is None:
            raise TeamServiceError('team is required')

        if team.is_finalised:
            raise TeamServiceError('team already finalised')
        for user_team in UserTeamAssociation.query.filter_by(team_id=team.id):
            if not user_team.is_creator_agreed or user_team.is_user_agreed:
                raise TeamServiceError('pending invitations or applications')
        team.is_finalised = True

    @staticmethod
    def is_member(team: Team, user: UserAlias):
        if team is None:
            raise TeamServiceError('team is required')
        if user is None:
            raise TeamServiceError('user is required')

        for asso in team.user_associations:
            if asso.user_id == user.id:
                return True
        return False
