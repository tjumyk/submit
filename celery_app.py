import hashlib
import json
import os
import subprocess
import time

import celery
import requests
from celery import Task

with open('config.json') as _f:
    config = json.load(_f)
site_config = config['SITE']
celery_config = config['AUTO_TEST']

server_url = site_config['root_url'] + site_config['base_url']

app = celery.Celery('submit', broker=celery_config['broker'], backend=celery_config['backend'])
app.conf.update(
    task_routes={
        'celery_app.run_test': {'queue': 'submit-auto-test'},
    },
    task_track_started=True
)


def md5sum(file_path: str, block_size: int = 65536):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        block = f.read(block_size)
        while block:
            md5.update(block)
            block = f.read(block_size)
        return md5.hexdigest()


def get_auth_param():
    return celery_config['worker']['name'], celery_config['worker']['password']


def report_started(submission_id: int, work_id: str, hostname: str, pid: int):
    data = {'hostname': hostname, 'pid': pid}
    resp = requests.put('%sapi/submissions/%d/worker-started/%s' % (server_url, submission_id, work_id),
                        json=data, auth=get_auth_param())
    resp.raise_for_status()


def report_result(submission_id: int, work_id: str, data: dict):
    resp = requests.put('%sapi/submissions/%d/worker-result/%s' % (server_url, submission_id, work_id),
                        json=data, auth=get_auth_param())
    resp.raise_for_status()


def get_submission(submission_id: int, work_id: str):
    resp = requests.get('%sapi/submissions/%d/worker-get-submission/%s' % (server_url, submission_id, work_id),
                        auth=get_auth_param())
    resp.raise_for_status()
    return resp.json()


def download_submission_file(submission_id: int, work_id: str, file: dict, local_save_path: str,
                             chunk_size: int = 65536):
    resp = requests.get('%sapi/submissions/%d/worker-submission-files/%s/%d' %
                        (server_url, submission_id, work_id, file['id']),
                        auth=get_auth_param(), stream=True)
    resp.raise_for_status()
    with open(local_save_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
    if file['md5'] != md5sum(local_save_path):
        raise RuntimeError('MD5 check of file "%s" failed' % file['requirement']['name'])


def upload_output_files(submission_id: int, work_id: str, files: dict):
    resp = requests.post('%sapi/submissions/%d/worker-output-files/%s' %
                         (server_url, submission_id, work_id),
                         files=files, auth=get_auth_param())
    resp.raise_for_status()


# noinspection PyAbstractClass
class MyTask(celery.Task):
    def on_success(self, result, work_id, args, kwargs):
        submission_id = args[0]
        report_result(submission_id, work_id, {
            'final_state': 'SUCCESS',
            'result': result
        })

    def on_failure(self, exc, work_id, args, kwargs, exc_info):
        submission_id = args[0]
        report_result(submission_id, work_id, {
            'final_state': 'FAILURE',
            'exception_class': type(exc).__name__,
            'exception_message': str(exc),
            'exception_traceback': exc_info.traceback
        })


@app.task(bind=True, base=MyTask)
def run_test(self: Task, submission_id: int):
    report_started(submission_id, self.request.id, self.request.hostname, os.getpid())

    submission = get_submission(submission_id, self.request.id)
    # TODO recognize task ID of the submission and copy corresponding assets for testing

    data_folder = config['DATA_FOLDER']
    exec_folder = os.path.join(data_folder, 'test_environments', self.request.id)
    if not os.path.lexists(exec_folder):
        os.makedirs(exec_folder)

    for file in submission['files']:
        local_save_path = os.path.join(exec_folder, file['requirement']['name'])
        download_submission_file(submission_id, self.request.id, file, local_save_path)

    # simulate a time-consuming task
    # TODO timeout mechanism
    # TODO Docker isolation
    # TODO network/cpu/memory restrictions
    time.sleep(12)
    result = subprocess.run(['ls', '-l'], stdout=subprocess.PIPE, check=True)

    files_to_upload = {}
    if result.stdout:
        files_to_upload['stdout.txt'] = result.stdout
    if result.stderr:
        files_to_upload['stderr.txt'] = result.stderr
    upload_output_files(submission_id, self.request.id, files_to_upload)

    return submission
