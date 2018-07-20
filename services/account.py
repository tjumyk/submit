from sqlalchemy import or_

import oauth
from error import BasicError
from models import db, UserAlias, GroupAlias


class AccountServiceError(BasicError):
    pass


class AccountService:
    @staticmethod
    def get_current_user():
        user = oauth.get_user()
        if user is None:
            return None
        return AccountService.get_user(user.id)

    @staticmethod
    def get_user(_id):
        if _id is None:
            raise AccountServiceError('id is required')
        if type(_id) is not int:
            raise AccountServiceError('id must be an integer')
        return UserAlias.query.get(_id)

    @staticmethod
    def get_group(_id):
        if _id is None:
            raise AccountServiceError('id is required')
        if type(_id) is not int:
            raise AccountServiceError('id must be an integer')
        return GroupAlias.query.get(_id)

    @staticmethod
    def get_all_users():
        return UserAlias.query.all()

    @staticmethod
    def get_all_groups():
        return GroupAlias.query.all()

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
            if UserAlias.query.filter(or_(UserAlias.name == user.name, UserAlias.email == user.email)).count():
                raise AccountServiceError('failed to sync user', 'User name or email has been occupied')
            user_alias = UserAlias(id=user.id, name=user.name, email=user.email)
            db.session.add(user_alias)
        else:
            if user_alias.name != user.name:
                raise AccountServiceError('failed to sync user', 'Inconsistent user name')
            if user_alias.email != user.email:  # update email
                user_alias.email = user.email

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

        # add missing groups
        missing_group_ids = remote_group_ids - local_group_ids
        if missing_group_ids:
            missing_groups = [remote_groups[gid] for gid in missing_group_ids]
            if GroupAlias.query.filter(GroupAlias.name.in_([g.name for g in missing_groups])).count():
                raise AccountServiceError('failed to sync groups', 'Group name has been occupied')
            for group in missing_groups:
                group_alias = GroupAlias(id=group.id, name=group.name)
                user_alias.groups.append(group_alias)  # also add missing links

        # fix links
        for gid in local_linked_group_ids - local_group_ids:
            user_alias.groups.remove(local_linked_groups[gid])  # remove deleted link
        for gid in local_group_ids - local_linked_group_ids:
            user_alias.groups.append(local_groups[gid])  # add missing link
