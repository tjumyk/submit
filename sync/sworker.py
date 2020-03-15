import json
import logging
import os
import signal
import time
from datetime import datetime

import requests

from server import app
from services.term import TermService
from sync.sservice import SyncService

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

worker_config = app.config['SYNC_WORKER']


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
    work_sub_folder = os.path.join(worker_config['work_folder'], str(time.time()))
    now = datetime.utcnow()

    with app.test_request_context():
        local_term_id = worker_config['local_term_id']
        remote_term_id = worker_config['remote_term_id']
        remote_server = worker_config['remote_server']
        term = TermService.get(local_term_id)

        for task in term.tasks:
            if not task.close_time or task.close_time > now:
                continue
            logger.info('Processing %s...' % task.title)

            logger.info('Getting local submissions...')
            sub_list = SyncService.list_submissions(task, 0)

            logger.info('Requesting diff...')
            resp = requests.post('%s/api/terms/%d/tasks/%s/submissions/diff' %
                                 (remote_server, remote_term_id, task.title),
                                 json=sub_list)
            if resp.status_code // 100 != 2:
                if resp.status_code == 404:
                    logger.warning(resp.content)
                    continue
                raise RuntimeError('[%d] %s' % (resp.status_code, resp.content))
            diff_list = resp.json()
            logger.info('Diff size: %d' % len(diff_list))

            if not diff_list:
                logger.info('Skip sync')
                continue

            if not os.path.exists(work_sub_folder):
                logger.info('Work folder: %s' % work_sub_folder)
                os.makedirs(work_sub_folder)

            with open(os.path.join(work_sub_folder, 'diff_list_%s.json' % task.title.replace(' ', '_')), 'w') as fo:
                fo.write(json.dumps(sub_list, indent=2))

            logger.info('Preparing data to sync...')
            diff_data = SyncService.prepare_submissions(diff_list)

            with open(os.path.join(work_sub_folder, 'diff_data_%s.json' % task.title.replace(' ', '_')), 'w') as fo:
                fo.write(json.dumps([s.to_dict() for s in diff_data], indent=2))

            logger.info('Syncing...')
            resp = requests.post('%s/api/terms/%d/tasks/%s/submissions' %
                                 (remote_server, remote_term_id, task.title),
                                 json=[s.to_dict() for s in diff_data])
            if resp.status_code // 100 != 2:
                raise RuntimeError('[%d] %s' % (resp.status_code, resp.content))
            logger.info('Sync completed: %r' % resp.content)


def main():
    logger.info('Staring Sync Worker...')

    # check config
    work_folder = worker_config['work_folder']
    period = worker_config['period']
    if not os.path.exists(work_folder):
        os.makedirs(work_folder, mode=0o700)
    assert period > 0

    logger.info('Starting main loop [period=%d]...', period)
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
