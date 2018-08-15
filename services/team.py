import re
from typing import Optional, List, Tuple

from sqlalchemy import or_, func

from error import BasicError
from models import Team, db, UserTeamAssociation, UserAlias, Task


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
    def get(_id) -> Optional[Team]:
        if _id is None:
            raise TeamServiceError('id is required')
        if type(_id) is not int:
            raise TeamServiceError('id must be an integer')

        return Team.query.get(_id)

    @staticmethod
    def get_all() -> List[Team]:
        return Team.query.all()

    @staticmethod
    def get_by_task_name(task: Task, name: str) -> Optional[Team]:
        if task is None:
            raise TeamServiceError('task is required')
        if not name:
            raise TeamServiceError('name is required')
        # should be no duplicate team name in a task, enforced by add() method
        return Team.query.filter_by(task_id=task.id, name=name).first()

    @staticmethod
    def get_for_task(task) -> List[Tuple[Team, int]]:
        if task is None:
            raise TeamServiceError('task is required')
        sub_query = db.session.query(Team.id.label('team_id'),
                                     func.count(UserTeamAssociation.user_id).label('total_user_associations')) \
            .filter(Team.task_id == task.id).outerjoin(UserTeamAssociation, Team.id == UserTeamAssociation.team_id) \
            .group_by(Team.id).subquery()
        return db.session.query(Team, sub_query.c.total_user_associations) \
            .filter(Team.id == sub_query.c.team_id) \
            .all()

    @staticmethod
    def get_team_association(task: Task, user: UserAlias) -> Optional[UserTeamAssociation]:
        """
        Notice: not necessarily member of returned teams
        """
        if task is None:
            raise TeamServiceError('task is required')
        if user is None:
            raise TeamServiceError('user is required')

        results = UserTeamAssociation.query.with_parent(user) \
            .filter(UserTeamAssociation.team_id == Team.id,
                    Team.task_id == task.id).all()
        if results:
            if len(results) > 1:
                raise TeamServiceError('user has multiple associated teams')
            return results[0]
        return None

    @staticmethod
    def add(task: Task, creator: UserAlias, name: str, slogan: Optional[str]) -> Team:
        if task is None:
            raise TeamServiceError('task is required')
        if creator is None:
            raise TeamServiceError('creator is required')
        if name is None:
            raise TeamServiceError('name is required')
        if not TeamService.name_pattern.match(name):
            raise TeamServiceError('invalid name format')

        if not TeamService._is_eligible_student(task, creator):
            raise TeamServiceError('not eligible student')

        if not task.is_team_task:
            raise TeamServiceError('task is not a team task')

        ass = UserTeamAssociation.query.filter_by(user=creator) \
            .filter(UserTeamAssociation.team_id == Team.id, Team.task_id == task.id) \
            .first()
        if ass:
            raise TeamServiceError('user already associated with another team', ass.team.name)

        if db.session.query(func.count()).filter(Team.name == name, Team.task_id == task.id).scalar():
            raise TeamServiceError('duplicate name')

        team = Team(task=task, creator=creator, name=name, slogan=slogan)
        if creator:
            ass = UserTeamAssociation(user=creator, team=team,
                                      is_user_agreed=True, is_creator_agreed=True)
            db.session.add(ass)
        return team

    @staticmethod
    def _is_eligible_student(task: Task, user: UserAlias):
        if task is None:
            raise TeamServiceError('task is required')
        if user is None:
            raise TeamServiceError('user is required')

        term = task.term
        for group in user.groups:
            if group.id == term.student_group_id:
                return True
        return False

    @staticmethod
    def is_creator(team: Team, user: UserAlias):
        if team is None:
            raise TeamServiceError('team is required')
        if user is None:
            raise TeamServiceError('user is required')

        # assume creator is already a member, i.e. double-agreed (enforced by add())
        return team.creator_id == user.id

    @staticmethod
    def update(team, **kwargs) -> dict:
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

        if not TeamService._is_eligible_student(team.task, user):
            raise TeamServiceError('not eligible student')

        if team.is_finalised:
            raise TeamServiceError('team already finalised')

        ass = UserTeamAssociation.query.filter_by(user=user) \
            .filter(UserTeamAssociation.team_id == Team.id, Team.task_id == team.task.id) \
            .first()
        if ass:
            if ass.team_id == team.id:
                raise TeamServiceError('user already associated with this team')
            raise TeamServiceError('user already associated with another team', ass.team.name)

        new_ass = UserTeamAssociation(user_id=user.id, team_id=team.id, is_creator_agreed=True, is_invited=True)
        db.session.add(new_ass)
        return new_ass

    @staticmethod
    def handle_invitation(team, user, is_accepted):
        """
        If is_accepted is True, invitation accepted.
        Otherwise, canceled by team creator or rejected by user
        """
        if team is None:
            raise TeamServiceError('team is required')
        if user is None:
            raise TeamServiceError('user is required')

        if team.is_finalised:
            raise TeamServiceError('team already finalised')

        ass = UserTeamAssociation.query.filter_by(user_id=user.id, team_id=team.id).first()
        if ass is None or not ass.is_invited:
            raise TeamServiceError('user was not invited to the team')
        if ass.is_user_agreed:
            raise TeamServiceError('invitation already accepted')

        if is_accepted:
            ass.is_user_agreed = True
            return ass
        else:
            db.session.delete(ass)
            return None

    @staticmethod
    def apply_join(team, user):
        if team is None:
            raise TeamServiceError('team is required')
        if user is None:
            raise TeamServiceError('user is required')

        if not TeamService._is_eligible_student(team.task, user):
            raise TeamServiceError('not eligible student')

        if team.is_finalised:
            raise TeamServiceError('team already finalised')

        ass = UserTeamAssociation.query.filter_by(user=user) \
            .filter(UserTeamAssociation.team_id == Team.id, Team.task_id == team.task.id) \
            .first()
        if ass:
            if ass.team_id == team.id:
                raise TeamServiceError('user already associated with this team')
            raise TeamServiceError('user already associated with another team', ass.team.name)

        new_ass = UserTeamAssociation(user_id=user.id, team_id=team.id, is_user_agreed=True, is_invited=False)
        db.session.add(new_ass)
        return new_ass

    @staticmethod
    def handle_join_application(team, user, is_accepted):
        """
        If is_accepted is True, application accepted.
        Otherwise, canceled by user or rejected by team creator
        """
        if team is None:
            raise TeamServiceError('team is required')
        if user is None:
            raise TeamServiceError('user is required')

        if team.is_finalised:
            raise TeamServiceError('team already finalised')

        ass = UserTeamAssociation.query.filter_by(user_id=user.id, team_id=team.id).first()
        if ass is None or ass.is_invited:
            raise TeamServiceError('user is not applying for joining this team')
        if ass.is_creator_agreed:
            raise TeamServiceError('application already accepted')

        if is_accepted:
            ass.is_creator_agreed = True
            return ass
        else:
            db.session.delete(ass)
            return None

    @staticmethod
    def leave(team: Team, user: UserAlias):
        """
        User leaves by himself or kicked out by the team creator.
        """
        if team is None:
            raise TeamServiceError('team is required')
        if user is None:
            raise TeamServiceError('user is required')

        if team.is_finalised:
            raise TeamServiceError('team already finalised')

        ass = UserTeamAssociation.query.filter_by(user_id=user.id, team_id=team.id).first()
        if ass is None or not ass.is_creator_agreed or not ass.is_user_agreed:
            raise TeamServiceError("user is not a member of this team")
        if team.creator_id == user.id:
            raise TeamServiceError('creator is not allowed to leave')
        db.session.delete(ass)

    @staticmethod
    def finalise(team):
        if team is None:
            raise TeamServiceError('team is required')

        if team.is_finalised:
            raise TeamServiceError('team already finalised')
        if db.session.query(func.count()) \
                .filter(UserTeamAssociation.team_id == team.id,
                        or_(UserTeamAssociation.is_creator_agreed == False,
                            UserTeamAssociation.is_user_agreed == False)) \
                .scalar():
            raise TeamServiceError('pending invitations or join applications')

        members = db.session.query(func.count()).filter(UserTeamAssociation.team_id == team.id).scalar()
        task = team.task
        if task.team_min_size is not None and members < task.team_min_size:
            raise TeamServiceError('too few members', 'At least %d members are required' % task.team_min_size)
        if task.team_max_size is not None and members > task.team_max_size:
            raise TeamServiceError('too many members', 'At most %d members are allowed' % task.team_max_size)

        team.is_finalised = True
