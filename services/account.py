from typing import Optional, List

from sqlalchemy import or_, func

from auth_connect import oauth
from error import BasicError
from models import db, UserAlias, GroupAlias


class AccountServiceError(BasicError):
    pass


class AccountService:
    @staticmethod
    def get_current_user() -> Optional[UserAlias]:
        user = oauth.get_user()
        if user is None:
            return None
        return AccountService.get_user(user.id)

    @staticmethod
    def get_user(_id) -> Optional[UserAlias]:
        if _id is None:
            raise AccountServiceError('id is required')
        if type(_id) is not int:
            raise AccountServiceError('id must be an integer')
        return UserAlias.query.get(_id)

    @staticmethod
    def get_user_by_name(name)->Optional[UserAlias]:
        if not name:
            raise AccountServiceError('name is required')
        return UserAlias.query.filter_by(name=name).first()

    @staticmethod
    def get_group(_id) -> Optional[GroupAlias]:
        if _id is None:
            raise AccountServiceError('id is required')
        if type(_id) is not int:
            raise AccountServiceError('id must be an integer')
        return GroupAlias.query.get(_id)

    @staticmethod
    def get_group_by_name(name) -> Optional[GroupAlias]:
        if not name:
            raise AccountServiceError('name is required')
        return GroupAlias.query.filter_by(name=name).first()

    @staticmethod
    def get_all_users() -> List[UserAlias]:
        return UserAlias.query.all()

    @staticmethod
    def get_all_groups() -> List[GroupAlias]:
        return GroupAlias.query.all()

    @staticmethod
    def add_group(name, description=None) -> GroupAlias:
        try:
            group = oauth.add_group(name, description)
            group_alias = GroupAlias(id=group.id, name=group.name, description=group.description)
            db.session.add(group_alias)
            return group_alias
        except oauth.OAuthError as e:
            raise AccountServiceError('Failed to add new group', e.msg)

    @staticmethod
    def sync_users():
        for user in oauth.get_users():
            AccountService.sync_user(user)

    @staticmethod
    def sync_user(user):
        """
        Sync OAuth user and groups with local copy (alias).

        For both User and Group, ID is the universal identifier, which is assumed to be constant for each resource.
        Name is also treated as constant universal identifier and will also be synced to verify the consistency.
        Email will be updated if an incoming User object has consistent ID and name with the local copy but different
        email.

        TODO How to sync deletion of Users or Groups in OAuth Server?
        """
        if user is None:
            raise AccountServiceError('user is required')

        # sync user
        user_alias = UserAlias.query.get(user.id)
        if user_alias is None:
            if user.nickname:
                _filter = or_(UserAlias.name == user.name, UserAlias.email == user.email,
                              UserAlias.nickname == user.nickname)
            else:
                _filter = or_(UserAlias.name == user.name, UserAlias.email == user.email)
            if db.session.query(func.count()).filter(_filter).scalar():
                raise AccountServiceError('failed to sync user', 'User name, email has been occupied')
            user_alias = UserAlias(id=user.id, name=user.name, email=user.email, nickname=user.nickname,
                                   avatar=user.avatar)
            db.session.add(user_alias)

            # additional initializations for new user alias
            from .messsage import MessageService
            MessageService.init_new_user_subscriptions(user_alias)
        else:
            if user_alias.name != user.name:
                raise AccountServiceError('failed to sync user', 'Inconsistent user name')
            # update other fields
            if user_alias.email != user.email:
                user_alias.email = user.email
            if user_alias.nickname != user.nickname:
                user_alias.nickname = user.nickname
            if user_alias.avatar != user.avatar:
                user_alias.avatar = user.avatar

        # prepare group sync
        remote_groups = {g.id: g for g in user.groups}
        local_groups = {g.id: g for g in GroupAlias.query.filter(GroupAlias.id.in_(remote_groups.keys()))}
        local_linked_groups = {g.id: g for g in user_alias.groups}
        remote_group_ids = set(remote_groups.keys())
        local_group_ids = set(local_groups.keys())
        local_linked_group_ids = set(local_linked_groups.keys())

        # check local group consistency
        for gid in local_group_ids:
            remote_group = remote_groups[gid]
            group_alias = local_groups[gid]
            if group_alias.name != remote_group.name:
                raise AccountServiceError('failed to sync groups', 'Inconsistent group name')
            # update other fields
            if group_alias.description != remote_group.description:
                group_alias.description = remote_group.description

        # add missing groups
        missing_group_ids = remote_group_ids - local_group_ids
        if missing_group_ids:
            missing_groups = [remote_groups[gid] for gid in missing_group_ids]
            if db.session.query(func.count()).filter(GroupAlias.name.in_([g.name for g in missing_groups])).scalar():
                raise AccountServiceError('failed to sync groups', 'Group name has been occupied')
            for group in missing_groups:
                group_alias = GroupAlias(id=group.id, name=group.name, description=group.description)
                user_alias.groups.append(group_alias)  # also add missing links

        # fix links
        for gid in local_linked_group_ids - local_group_ids:
            user_alias.groups.remove(local_linked_groups[gid])  # remove deleted link
        for gid in local_group_ids - local_linked_group_ids:
            user_alias.groups.append(local_groups[gid])  # add missing link

    @staticmethod
    def sync_groups():
        # prepare group sync
        remote_groups = {g.id: g for g in oauth.get_groups()}
        local_groups = {g.id: g for g in GroupAlias.query.filter(GroupAlias.id.in_(remote_groups.keys()))}
        remote_group_ids = set(remote_groups.keys())
        local_group_ids = set(local_groups.keys())

        # check local group consistency
        for gid in local_group_ids:
            remote_group = remote_groups[gid]
            group_alias = local_groups[gid]
            if group_alias.name != remote_group.name:
                raise AccountServiceError('failed to sync groups', 'Inconsistent group name')
            # update other fields
            if group_alias.description != remote_group.description:
                group_alias.description = remote_group.description

        # add missing groups
        missing_group_ids = remote_group_ids - local_group_ids
        if missing_group_ids:
            missing_groups = [remote_groups[gid] for gid in missing_group_ids]
            if db.session.query(func.count()).filter(GroupAlias.name.in_([g.name for g in missing_groups])).scalar():
                raise AccountServiceError('failed to sync groups', 'Group name has been occupied')
            for group in missing_groups:
                group_alias = GroupAlias(id=group.id, name=group.name, description=group.description)
                db.session.add(group_alias)

    @staticmethod
    def search_user_by_name(name, limit=5) -> List[UserAlias]:
        if name is None:
            raise AccountServiceError('name is required')
        if len(name) == 0:
            raise AccountServiceError('name must not be empty')

        _filter = or_(UserAlias.name.contains(name), UserAlias.nickname.contains(name))
        if limit is None:
            return UserAlias.query.filter(_filter).all()
        else:
            if type(limit) is not int:
                raise AccountServiceError('limit must be an integer')
            return UserAlias.query.filter(_filter).limit(limit)

    @staticmethod
    def search_group_by_name(name, limit=5) -> List[GroupAlias]:
        if name is None:
            raise AccountServiceError('name is required')
        if len(name) == 0:
            raise AccountServiceError('name must not be empty')

        _filter = or_(GroupAlias.name.contains(name), GroupAlias.description.contains(name))
        if limit is None:
            return GroupAlias.query.filter(_filter).all()
        else:
            if type(limit) is not int:
                raise AccountServiceError('limit must be an integer')
            return GroupAlias.query.filter(_filter).limit(limit)
