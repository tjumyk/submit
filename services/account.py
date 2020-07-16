from typing import Optional, List, Dict

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
    def get_user_by_name_list(name_list: List[str]) -> Dict[str, UserAlias]:
        if name_list is None:
            raise AccountServiceError('name list is required')
        for name in name_list:
            if not isinstance(name, str):
                raise AccountServiceError('name list must only contain strings')
            if not name:
                raise AccountServiceError('name list must not contain empty strings')
        return {u.name: u for u in db.session.query(UserAlias).filter(UserAlias.name.in_(name_list))}

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

    @classmethod
    def sync_users(cls):
        for user in oauth.get_users():
            cls.sync_user(user)

    @classmethod
    def sync_user_by_id(cls, uid: int) -> UserAlias:
        try:
            user = oauth.get_user_by_id(uid)
            return cls.sync_user(user)
        except oauth.OAuthError as e:
            raise AccountServiceError('Failed to sync user %d' % uid, e.msg)

    @classmethod
    def sync_user_by_name(cls, name: str) -> UserAlias:
        try:
            user = oauth.get_user_by_name(name)
            return cls.sync_user(user)
        except oauth.OAuthError as e:
            raise AccountServiceError('Failed to sync user %s' % name, e.msg)

    @classmethod
    def sync_user(cls, user: oauth.User) -> UserAlias:
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

        user_alias = cls._sync_user(user)

        groups = {g.id: g for g in user.groups}
        group_ids = set(groups.keys())
        groups_local = {g.id: g for g in GroupAlias.query.filter(GroupAlias.id.in_(groups.keys()))}
        groups_synced = {gid: cls._sync_group(group, groups_local.get(gid), skip_get_alias=True)
                         for gid, group in groups.items()}

        local_user_groups = {g.id: g for g in user_alias.groups}
        local_user_group_ids = set(local_user_groups)

        for gid in local_user_group_ids - group_ids:
            user_alias.groups.remove(local_user_groups[gid])  # remove deleted link
        for gid in group_ids - local_user_group_ids:
            user_alias.groups.append(groups_synced[gid])  # add missing link

        return user_alias

    @classmethod
    def sync_groups(cls):
        for group in oauth.get_groups():
            cls.sync_group(group)

    @classmethod
    def sync_group_by_id(cls, gid: int, sync_group_users: bool = False) -> GroupAlias:
        try:
            group = oauth.get_group_by_id(gid)
            group_users = None
            if sync_group_users:
                group_users = oauth.get_users_in_group(group.id)
            return cls.sync_group(group, group_users)
        except oauth.OAuthError as e:
            raise AccountServiceError('Failed to sync group %d' % gid, e.msg)

    @classmethod
    def sync_group(cls, group: oauth.Group, group_users: List[oauth.User] = None) -> GroupAlias:
        """
        Sync the group and associated users (if provided).
        """
        if group is None:
            raise AccountServiceError('group is required')

        group_alias = cls._sync_group(group)

        if group_users is not None:
            users = {u.id: u for u in group_users}
            user_ids = set(users)
            users_local = {u.id: u for u in db.session.query(UserAlias).filter(UserAlias.id.in_(user_ids)).all()}
            users_synced = {uid: cls._sync_user(user, users_local.get(uid), skip_get_alias=True)
                            for uid, user in users.items()}

            local_group_users = {u.id: u for u in group_alias.users}
            local_group_user_ids = set(local_group_users)

            # remove users from local group
            for uid in local_group_user_ids - user_ids:
                group_alias.users.remove(local_group_users[uid])
            # add users to local group
            for uid in user_ids - local_group_user_ids:
                group_alias.users.append(users_synced[uid])

        return group_alias

    @staticmethod
    def _sync_user(user: oauth.User, user_alias: UserAlias = None, skip_get_alias: bool = False) -> UserAlias:
        """
        Sync a remote user to local user alias.
        Associated groups are not synced here.
        """
        if user_alias is None and not skip_get_alias:
            user_alias = UserAlias.query.get(user.id)

        if user_alias is None:
            if user.nickname:
                _filter = or_(UserAlias.name == user.name, UserAlias.email == user.email,
                              UserAlias.nickname == user.nickname)
            else:
                _filter = or_(UserAlias.name == user.name, UserAlias.email == user.email)
            if db.session.query(func.count()).filter(_filter).scalar():
                raise AccountServiceError('failed to sync user', 'User name, nickname or email has been occupied')
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
        return user_alias

    @staticmethod
    def _sync_group(group: oauth.Group, group_alias: GroupAlias = None, skip_get_alias: bool = False) -> GroupAlias:
        """
        Sync a remote group to local group alias.
        Associated users are not synced here.
        """
        if group_alias is None and not skip_get_alias:
            group_alias = GroupAlias.query.get(group.id)

        if group_alias is None:
            if db.session.query(func.count()).filter(GroupAlias.name == group.name).scalar():
                raise AccountServiceError('failed to sync group', 'Group name has been occupied')
            group_alias = GroupAlias(id=group.id, name=group.name, description=group.description)
            db.session.add(group_alias)
        else:
            if group_alias.name != group.name:
                raise AccountServiceError('failed to sync group', 'Inconsistent group name')
            # update other fields
            if group_alias.description != group.description:
                group_alias.description = group.description

        return group_alias

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
