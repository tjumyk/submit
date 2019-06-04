import logging

from flask import Blueprint, jsonify, request

from auth_connect.oauth import requires_login
from models import db
from services.account import AccountService, AccountServiceError
from services.messsage import MessageService, MessageServiceError

message_api = Blueprint('message_api', __name__)
logger = logging.getLogger(__name__)


@message_api.route('/<int:mid>')
@requires_login
def get(mid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500

        msg = MessageService.get(mid)
        if msg is None:
            return jsonify(msg='message not found'), 404
        if not MessageService.is_receiver(msg, user):
            return jsonify(msg='access forbidden'), 403

        msg_dict = msg.to_dict(with_sender=True, with_receiver=True, with_body=True)
        msg_dict['is_read'] = msg.id in MessageService.get_is_read(user, msg)
        return jsonify(msg_dict)
    except (AccountServiceError, MessageServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


@message_api.route('/<int:mid>/mark-read')
@requires_login
def mark_read(mid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500

        msg = MessageService.get(mid)
        if msg is None:
            return jsonify(msg='message not found'), 404
        if not MessageService.is_receiver(msg, user):
            return jsonify(msg='access forbidden'), 403

        MessageService.set_is_read(msg, user, is_read=True)
        db.session.commit()
        return "", 204
    except (AccountServiceError, MessageServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


@message_api.route('/channels')
@requires_login
def get_channels():
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500

        channels = MessageService.get_all_channels()
        sub_channel_ids = set(sub.channel_id for sub in user.email_subscriptions)

        channels_dicts = []
        for ch in channels:
            d = ch.to_dict()
            d['is_subscribed'] = ch.id in sub_channel_ids
            channels_dicts.append(d)

        return jsonify(channels_dicts)
    except (AccountServiceError, MessageServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


@message_api.route('/channels/<int:cid>/subscribe')
@message_api.route('/channels/<int:cid>/unsubscribe')
@requires_login
def subscribe_channel(cid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500

        channel = MessageService.get_channel(cid)
        if channel is None:
            return jsonify(msg='channel not found'), 404

        is_subscribed = request.path.endswith('/subscribe')
        MessageService.set_email_subscription(user, channel, is_subscribed)
        db.session.commit()
        return "", 204
    except (AccountServiceError, MessageServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 500
