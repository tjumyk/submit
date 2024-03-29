from collections import defaultdict
from io import StringIO

from flask import Blueprint, jsonify, request

from auth_connect.oauth import requires_login
from models import db
from services.account import AccountService, AccountServiceError
from services.final_marks import FinalMarksService, FinalMarksServiceError
from services.messsage import MessageService, MessageServiceError
from services.term import TermService, TermServiceError

term_api = Blueprint('term_api', __name__)


@term_api.route('/<int:term_id>')
@requires_login
def do_term(term_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404
        if not TermService.get_access_roles(term, user):
            return jsonify(msg='access forbidden'), 403
        return jsonify(term.to_dict())
    except TermServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@term_api.route('/<int:term_id>/tasks')
@requires_login
def term_tasks(term_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404
        if not TermService.get_access_roles(term, user):
            return jsonify(msg='access forbidden'), 403

        # Notice: must not expose task details in this api because there's no time check here
        return jsonify([t.to_dict(with_details=False, with_advanced_fields=False)
                        for t in sorted(term.tasks, key=lambda t: t.id)])
    except TermServiceError as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@term_api.route('/<int:term_id>/messages')
@requires_login
def term_messages(term_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500

        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404

        after_id = request.args.get('after_id')
        if after_id is not None:
            msgs = MessageService.get_for_term_user(term, user, int(after_id))
        else:
            msgs = MessageService.get_for_term_user(term, user)

        read_set = MessageService.get_is_read(user, *msgs)
        msg_dicts = []
        for msg in msgs:
            d = msg.to_dict(with_sender=True, with_receiver=False, with_body=False)
            d['is_read'] = msg.id in read_set
            msg_dicts.append(d)
        return jsonify(msg_dicts)
    except (AccountServiceError, MessageServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@term_api.route('/<int:term_id>/unread-messages-count')
@requires_login
def term_unread_messages_count(term_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500

        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404

        return jsonify(MessageService.get_unread_count_for_term_user(term, user))
    except (AccountServiceError, MessageServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@term_api.route('/<int:term_id>/mark-all-messages-read')
@requires_login
def term_messages_mark_all_read(term_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500

        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404

        msgs = MessageService.get_for_term_user(term, user)
        MessageService.set_is_read(user, True, *msgs)

        db.session.commit()
        return "", 204
    except (AccountServiceError, MessageServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@term_api.route('/<int:term_id>/students')
@requires_login
def term_students(term_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500

        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404
        roles = TermService.get_access_roles(term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        group = AccountService.get_group(term.student_group_id)
        if group is None:
            return jsonify(msg='student group not found'), 500
        return jsonify([u.to_dict() for u in sorted(group.users, key=lambda u:u.name)])
    except (AccountServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@term_api.route('/<int:term_id>/final-marks')
@requires_login
def term_final_marks(term_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500

        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404
        roles = TermService.get_access_roles(term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        return jsonify([m.to_dict(with_comment=True) for m in FinalMarksService.get_for_term(term)])
    except (AccountServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@term_api.route('/<int:term_id>/export-final-marks')
@requires_login
def term_export_final_marks(term_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500

        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404
        roles = TermService.get_access_roles(term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        tasks = sorted(term.tasks, key=lambda t: t.id)
        users_map = {}
        marks_map = defaultdict(dict)
        for m in FinalMarksService.get_for_term(term, joined_load_user=True):
            users_map[m.user_id] = m.user
            marks_map[m.user_id][m.task_id] = m

        with StringIO() as buffer:
            headers = ['ID', 'Name']
            for task in tasks:
                headers.append(task.title + ' Marks')
                headers.append(task.title + ' Comment')

            buffer.write('\t'.join(headers))
            buffer.write('\n')
            for u in sorted(users_map.values(), key=lambda x: x.name):
                row = [str(u.id), u.name]
                for task in tasks:
                    m = marks_map[u.id].get(task.id)
                    if m:
                        marks = m.marks
                        if int(marks) == marks:  # convert marks to int if value is not changed
                            marks = int(marks)
                        row.append(str(marks))
                        row.append(m.comment or '')
                    else:
                        row.append('')
                        row.append('')
                buffer.write('\t'.join(row))
                buffer.write('\n')
            return buffer.getvalue(), {'Content-Type': 'text/plain'}

    except (AccountServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@term_api.route('/<int:term_id>/my-final-marks')
@requires_login
def my_final_marks(term_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500

        term = TermService.get(term_id)
        if term is None:
            return jsonify(msg='term not found'), 404

        records = FinalMarksService.get_for_user_term(user, term)
        return jsonify([r.to_dict() for r in records])
    except (AccountServiceError, TermServiceError, FinalMarksServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
