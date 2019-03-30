import logging
import math
import os
import signal
import time
from datetime import datetime, timedelta

from sqlalchemy import or_

from models import Task, db
from server import app
from services.task import TaskService
from services.team import TeamService
from utils.mail import send_email

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

worker_config = app.config['PERIOD_WORKER']


class DelayedKeyboardInterrupt(object):
    def __init__(self):
        self.signal_received = None
        self.old_handler = None

    def __enter__(self):
        self.old_handler = signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig, frame):
        self.signal_received = (sig, frame)
        logger.info('SIGINT received. Delaying KeyboardInterrupt.')

    def __exit__(self, _type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received:
            self.old_handler(*self.signal_received)


def _exec_work():
    now = datetime.utcnow()
    expire = worker_config['expire']
    notify_open = worker_config['notify_open']
    due_notify_hours = worker_config['due_notify_hours']
    team_join_close_notify_hours = worker_config['team_join_close_notify_hours']
    with app.test_request_context():
        if notify_open:
            for task in db.session.query(Task) \
                    .filter(Task.open_time < now,
                            Task.open_time > now - timedelta(seconds=expire),
                            or_(Task.close_time.is_(None), Task.close_time > now)) \
                    .all():
                _process_task_open(task)
        for close_hours in team_join_close_notify_hours:
            for task in db.session.query(Task) \
                    .filter(Task.is_team_task == True,
                            Task.open_time < now,
                            Task.team_join_close_time < now + timedelta(hours=close_hours),
                            Task.team_join_close_time > now + timedelta(hours=close_hours) - timedelta(seconds=expire),
                            or_(Task.close_time.is_(None), Task.close_time > now),
                            ) \
                    .all():
                _process_task_team_join_close(task, close_hours)
        for due_hours in due_notify_hours:
            for task in db.session.query(Task) \
                    .filter(Task.open_time < now,
                            Task.due_time < now + timedelta(hours=due_hours),
                            Task.due_time > now + timedelta(hours=due_hours) - timedelta(seconds=expire),
                            or_(Task.close_time.is_(None), Task.close_time > now),
                            ) \
                    .all():
                _process_task_due(task, due_hours)


def _send_email_bcc_batched(template, bcc_list, mail_args):
    total_bcc = len(bcc_list)
    max_recipients_per_mail = worker_config['max_recipients_per_mail']
    batches = math.ceil(total_bcc / max_recipients_per_mail)
    logger.info('Sending "%s" emails to %d users in %d batches (batch size: %d)...'
                % (template, total_bcc, batches, max_recipients_per_mail))
    for i in range(batches):
        logger.info('Sending for batch %d...' % i)
        batch_bcc_list = bcc_list[i * max_recipients_per_mail: (i + 1) * max_recipients_per_mail]
        send_email(template, [], bcc_list=batch_bcc_list, mail_args=mail_args)


def _process_task_open(task):
    process_name = 'Task Open: %r at %s' % (task, task.open_time)
    mark_name = 'task_open_%d_%s.mark' % (task.id, str(task.open_time).replace(' ', '_'))
    work_folder = worker_config['work_folder']
    mark_path = os.path.join(work_folder, mark_name)
    try:
        with open(mark_path, 'x'):
            logger.info('[Process Started] %s' % process_name)
            term = task.term
            mail_args = dict(site=app.config['SITE'], term=term, task=task)
            bcc_list = [(u.name, u.email) for u in term.student_group.users]
            _send_email_bcc_batched('task_open', bcc_list, mail_args)
            logger.info('[Process Finished] %s' % process_name)
    except FileExistsError:
        logger.info('[Process Skipped] %s. Mark File: %s' % (process_name, mark_name))


def _process_task_team_join_close(task, close_hours):
    process_name = 'Task Team Join Close: %r at %s' % (task, task.team_join_close_time)
    mark_name = 'task_team_join_close_%d_%s.mark' % (task.id, str(task.team_join_close_time).replace(' ', '_'))
    work_folder = worker_config['work_folder']
    mark_path = os.path.join(work_folder, mark_name)
    try:
        with open(mark_path, 'x'):
            logger.info('[Process Started] %s' % process_name)
            mail_args = dict(site=app.config['SITE'], term=task.term, task=task, close_hours=close_hours)
            bcc_list = [(u.name, u.email) for u in TeamService.get_free_users_for_task(task)]
            _send_email_bcc_batched('task_team_join_close', bcc_list, mail_args)
            logger.info('[Process Finished] %s' % process_name)
    except FileExistsError:
        logger.info('[Process Skipped] %s. Mark File: %s' % (process_name, mark_name))


def _process_task_due(task, due_hours):
    process_name = 'Task Due in %d Hours: %r at %s' % (due_hours, task, task.due_time)
    mark_name = 'task_due_%d_%dh_%s.mark' % (task.id, due_hours, str(task.due_time).replace(' ', '_'))
    work_folder = worker_config['work_folder']
    mark_path = os.path.join(work_folder, mark_name)
    try:
        with open(mark_path, 'x'):
            logger.info('[Process Started] %s' % process_name)

            mail_args = dict(site=app.config['SITE'], term=task.term, task=task, due_hours=due_hours)
            if task.is_team_task:
                # lazy teams
                lazy_teams = TaskService.get_teams_no_submission(task)
                user_list = (ass.user for team in lazy_teams for ass in team.user_associations)
                bcc_list = [(u.name, u.email) for u in user_list]
                _send_email_bcc_batched('task_due_for_team', bcc_list, mail_args)

                # lazier users who even have no teams
                bcc_list = [(u.name, u.email) for u in TeamService.get_free_users_for_task(task)]
                _send_email_bcc_batched('task_due_for_no_team', bcc_list, mail_args)
            else:
                lazy_users = TaskService.get_users_no_submission(task)
                bcc_list = [(u.name, u.email) for u in lazy_users]
                _send_email_bcc_batched('task_due', bcc_list, mail_args)
            logger.info('[Process Finished] %s' % process_name)
    except FileExistsError:
        logger.info('[Process Skipped] %s. Mark File: %s' % (process_name, mark_name))


def main():
    logger.info('Staring Period Worker...')

    # check config
    work_folder = worker_config['work_folder']
    period = worker_config['period']
    expire = worker_config['expire']
    due_notify_hours = worker_config['due_notify_hours']
    team_join_close_notify_hours = worker_config['team_join_close_notify_hours']
    max_recipients_per_mail = worker_config['max_recipients_per_mail']
    if not os.path.exists(work_folder):
        os.makedirs(work_folder, mode=0o700)
    assert period > 0
    assert expire > period
    assert type(due_notify_hours) == list
    assert type(team_join_close_notify_hours) == list
    assert type(max_recipients_per_mail) == int and max_recipients_per_mail > 0

    # align to whole minutes
    now_second = datetime.now().second
    if now_second > 5:
        wait_seconds = 60 - now_second + 1
        logger.info('Waiting for %d seconds to align to whole minutes...', wait_seconds)
        try:
            time.sleep(wait_seconds)
        except KeyboardInterrupt:
            return

    logger.info('Starting main loop [period=%d, expire=%d]...', period, expire)
    while True:
        try:
            start_time = time.time()
            with DelayedKeyboardInterrupt():
                try:
                    _exec_work()
                except Exception as e:
                    logger.exception(str(e))
            time_elapsed = time.time() - start_time
            if time_elapsed < period:
                time.sleep(period - time_elapsed)  # sleep for the rest time in the current period
            else:
                delayed = time_elapsed - period
                if delayed > 0:
                    logger.warning('The following work is delayed for %s due to the over-period time of the last work'
                                   % delayed)
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    main()
