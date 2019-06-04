import math
from typing import List, Tuple, Optional

from error import BasicError
from models import UserAlias, MessageChannel, GroupAlias, Message, Term
from utils.mail import prepare_email, PreparedEmail
from utils.message import MultiFormatMessageContent

MAIL_BATCH_SIZE = 100


class MessageSenderServiceError(BasicError):
    pass


class MessageSenderService:
    @staticmethod
    def _prepare_batched_emails(content: MultiFormatMessageContent,
                                receivers: List[UserAlias], hide_peers: bool):
        if content is None:
            raise MessageSenderServiceError('content is required')
        if receivers is None:
            raise MessageSenderServiceError('receiver list is required')

        mails = []
        batches = math.ceil(len(receivers) / MAIL_BATCH_SIZE)
        for i in range(batches):
            receivers_batch = [(user.name, user.email)
                               for user in receivers[i * MAIL_BATCH_SIZE: (i + 1) * MAIL_BATCH_SIZE]]
            if hide_peers:
                mails.append(prepare_email(content, [], bcc_list=receivers_batch))
            else:
                mails.append(prepare_email(content, receivers_batch))
        return mails

    @classmethod
    def send_to_user(cls, channel: MessageChannel, term: Term, content: MultiFormatMessageContent,
                     sender: Optional[UserAlias], receiver: UserAlias) \
            -> Tuple[Message, Optional[PreparedEmail]]:
        if channel is None:
            raise MessageSenderServiceError('channel is required')
        if term is None:
            raise MessageSenderServiceError('term is required')
        if content is None:
            raise MessageSenderServiceError('content is required')
        if receiver is None:
            raise MessageSenderServiceError('receiver is required')

        from .messsage import MessageService
        if MessageService.has_email_subscription_of_channel(receiver, channel):
            mails = cls._prepare_batched_emails(content=content, receivers=[receiver], hide_peers=False)
            assert len(mails) == 1
            mail = mails[0]
        else:
            mail = None

        msg_body = content.site_html or content.text
        msg = MessageService.add(channel=channel, term=term, sender=sender, receiver=receiver, receiver_group=None,
                                 subject=content.subject, body=msg_body)

        return msg, mail

    @classmethod
    def send_to_users(cls, channel: MessageChannel, term: Term, content: MultiFormatMessageContent,
                      sender: Optional[UserAlias], receivers: List[UserAlias], hide_peers: bool = True) \
            -> Tuple[List[Message], List[PreparedEmail]]:
        if channel is None:
            raise MessageSenderServiceError('channel is required')
        if term is None:
            raise MessageSenderServiceError('term is required')
        if content is None:
            raise MessageSenderServiceError('content is required')
        if receivers is None:
            raise MessageSenderServiceError('receiver list is required')

        from .messsage import MessageService
        subs = MessageService.get_users_email_subscriptions_of_channel(receivers, channel)
        mails = cls._prepare_batched_emails(content=content, receivers=[sub.user for sub in subs],
                                            hide_peers=hide_peers)
        msg_body = content.site_html or content.text
        msgs = []
        for receiver in receivers:
            msgs.append(MessageService.add(channel=channel, term=term, sender=sender, receiver=receiver,
                                           receiver_group=None, subject=content.subject, body=msg_body))
        return msgs, mails

    @classmethod
    def send_to_group(cls, channel: MessageChannel, term: Term, content: MultiFormatMessageContent,
                      sender: Optional[UserAlias], receiver_group: GroupAlias, hide_peers: bool = True) \
            -> Tuple[Message, List[PreparedEmail]]:
        if channel is None:
            raise MessageSenderServiceError('channel is required')
        if term is None:
            raise MessageSenderServiceError('term is required')
        if content is None:
            raise MessageSenderServiceError('content is required')
        if receiver_group is None:
            raise MessageSenderServiceError('receiver group is required')

        from .messsage import MessageService
        subs = MessageService.get_group_email_subscriptions_of_channel(receiver_group, channel)
        mails = cls._prepare_batched_emails(content=content, receivers=[sub.user for sub in subs],
                                            hide_peers=hide_peers)
        msg_body = content.site_html or content.text
        msg = MessageService.add(channel=channel, term=term, sender=sender, receiver=None,
                                 receiver_group=receiver_group, subject=content.subject, body=msg_body)
        return msg, mails
