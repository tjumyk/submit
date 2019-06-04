from operator import or_, and_
from typing import Optional, List, Set

from error import BasicError
from models import Message, db, MessageChannel, UserAlias, GroupAlias, user_groups_alias, MessageIsRead, \
    EmailSubscription, Term


class MessageServiceError(BasicError):
    pass


class MessageService:
    @staticmethod
    def get(_id: int) -> Optional[Message]:
        if _id is None:
            raise MessageServiceError('id is required')
        if type(_id) is not int:
            raise MessageServiceError('id must be an integer')
        return Message.query.get(_id)

    @staticmethod
    def get_all() -> List[Message]:
        return Message.query.all()

    @staticmethod
    def add(channel: MessageChannel, term: Term, sender: Optional[UserAlias], receiver: Optional[UserAlias],
            receiver_group: Optional[GroupAlias], subject: str, body: str) -> Message:
        if channel is None:
            raise MessageServiceError(msg='channel is required')
        if term is None:
            raise MessageServiceError(msg='term is required')
        if not subject:
            raise MessageServiceError(msg='subject is required')

        msg = Message(channel=channel, term=term, sender=sender, receiver=receiver, receiver_group=receiver_group,
                      subject=subject, body=body)
        db.session.add(msg)
        return msg

    @staticmethod
    def is_receiver(msg: Message, user: UserAlias) -> bool:
        if msg is None:
            raise MessageServiceError(msg='message is required')
        if user is None:
            raise MessageServiceError(msg='user is required')

        if msg.receiver_id and msg.receiver_id == user.id:
            return True
        if msg.receiver_group_id and any(msg.receiver_group_id == group.id for group in user.groups):
            return True
        return False

    @staticmethod
    def get_for_term_user(term: Term, user: UserAlias, after_id: int = None) -> List[Message]:
        if user is None:
            raise MessageServiceError(msg='user is required')

        filters = [
            Message.term_id == term.id,
            or_(Message.receiver_id == user.id,
                and_(Message.receiver_group_id == user_groups_alias.c.group_id,
                     user_groups_alias.c.user_id == user.id))
        ]
        if after_id is not None:
            filters.append(Message.id > after_id)

        msgs = db.session.query(Message) \
            .filter(*filters) \
            .order_by(Message.created_at.desc()) \
            .all()
        return msgs

    @staticmethod
    def get_unread_count_for_term_user(term: Term, user: UserAlias) -> List[Message]:
        if user is None:
            raise MessageServiceError(msg='user is required')

        unread_count = db.session.query(Message.id) \
            .filter(Message.term_id == term.id,
                    or_(Message.receiver_id == user.id,
                        and_(Message.receiver_group_id == user_groups_alias.c.group_id,
                             user_groups_alias.c.user_id == user.id))) \
            .except_(db.session.query(MessageIsRead.message_id).filter(MessageIsRead.user_id == user.id)) \
            .count()
        return unread_count

    @staticmethod
    def set_is_read(msg: Message, user: UserAlias, is_read: bool):
        if msg is None:
            raise MessageServiceError(msg='message is required')
        if user is None:
            raise MessageServiceError(msg='user is required')

        mark = MessageIsRead.query.filter_by(user_id=user.id, message_id=msg.id).first()
        if is_read:
            if mark is None:
                db.session.add(MessageIsRead(user_id=user.id, message_id=msg.id))
        else:
            if mark is not None:
                db.session.delete(mark)

    @staticmethod
    def get_is_read(user: UserAlias, *messages: Message) -> Set[int]:
        if user is None:
            raise MessageServiceError(msg='user is required')

        read_set = set()
        for result in db.session.query(MessageIsRead.message_id.label('mid')) \
                .filter(MessageIsRead.user_id == user.id,
                        MessageIsRead.message_id.in_([msg.id for msg in messages])).all():
            read_set.add(result.mid)
        return read_set

    @staticmethod
    def get_all_channels() -> List[MessageChannel]:
        return MessageChannel.query.all()

    @staticmethod
    def get_channel(_id: int) -> Optional[MessageChannel]:
        if _id is None:
            raise MessageServiceError('id is required')

        return MessageChannel.query.get(_id)

    @staticmethod
    def get_channel_by_name(name: str) -> Optional[MessageChannel]:
        if not name:
            raise MessageServiceError('name is required')

        return MessageChannel.query.filter_by(name=name).first()

    @staticmethod
    def add_channel(name: str, description: str = None) -> MessageChannel:
        if not name:
            raise MessageServiceError('name is required')

        if MessageChannel.query.filter_by(name=name).count():
            raise MessageServiceError('duplicate name')

        channel = MessageChannel(name=name, description=description)
        db.session.add(channel)
        return channel

    @staticmethod
    def set_email_subscription(user: UserAlias, channel: MessageChannel, subscribed: bool):
        if user is None:
            raise MessageServiceError('user is required')
        if channel is None:
            raise MessageServiceError('channel is required')

        existing_sub = EmailSubscription.query.filter_by(user_id=user.id, channel_id=channel.id).first()
        if subscribed:
            if existing_sub is None:
                db.session.add(EmailSubscription(user_id=user.id, channel_id=channel.id))
        else:
            if existing_sub is not None:
                db.session.delete(existing_sub)

    @staticmethod
    def has_email_subscription_of_channel(user: UserAlias, channel: MessageChannel) -> bool:
        if user is None:
            raise MessageServiceError('user is required')
        if channel is None:
            raise MessageServiceError('channel is required')

        return EmailSubscription.query.filter_by(user_id=user.id, channel_id=channel.id).count() > 0

    @staticmethod
    def get_users_email_subscriptions_of_channel(users: List[UserAlias], channel: MessageChannel) \
            -> List[EmailSubscription]:
        if users is None:
            raise MessageServiceError('user list is required')
        if channel is None:
            raise MessageServiceError('channel is required')

        return db.session.query(EmailSubscription).filter(EmailSubscription.user_id.in_([u.id for u in users]),
                                                          EmailSubscription.channel_id == channel.id).all()

    @staticmethod
    def get_group_email_subscriptions_of_channel(group: GroupAlias, channel: MessageChannel) -> List[EmailSubscription]:
        if group is None:
            raise MessageServiceError('group is required')
        if channel is None:
            raise MessageServiceError('channel is required')

        return db.session.query(EmailSubscription).filter(EmailSubscription.user_id == user_groups_alias.c.user_id,
                                                          user_groups_alias.c.group_id == group.id,
                                                          EmailSubscription.channel_id == channel.id).all()

    @staticmethod
    def init_default_channels():
        MessageService.add_channel('task', 'Task-related messages')
        MessageService.add_channel('team', 'Team-related messages')

    @classmethod
    def init_new_user_subscriptions(cls, user: UserAlias):
        cls.set_email_subscription(user, cls.get_channel_by_name('task'), True)
        cls.set_email_subscription(user, cls.get_channel_by_name('team'), True)
