import hashlib
import json
import os
import shutil
import ssl
import subprocess

import celery
import docker
import requests
from celery import Task

with open('config.json') as _f:
    config = json.load(_f)
site_config = config['SITE']
celery_config = config['AUTO_TEST']
worker_config = config.get('AUTO_TEST_WORKER')

server_url = site_config['root_url'] + site_config['base_url']

app = celery.Celery('submit', broker=celery_config['broker'], backend=celery_config['backend'])
app.conf.update(
    task_routes={
        'celery_app.run_test': {'queue': 'auto-test'},
    },
    task_track_started=True
)
broker_ssl_config = celery_config.get('broker_use_ssl')
if broker_ssl_config:
    cert_reqs = broker_ssl_config.get('cert_reqs')
    if cert_reqs:
        broker_ssl_config['cert_reqs'] = getattr(ssl, cert_reqs)
    app.conf.update(broker_use_ssl=broker_ssl_config)

docker_client = docker.from_env()


def md5sum(file_path: str, block_size: int = 65536):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        block = f.read(block_size)
        while block:
            md5.update(block)
            block = f.read(block_size)
        return md5.hexdigest()


def get_auth_param():
    return worker_config['name'], worker_config['password']


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

    # get submission info
    submission = get_submission(submission_id, self.request.id)
    submission_id = submission['id']
    task_id = submission['task_id']

    # check work folder
    data_folder = config['DATA_FOLDER']
    work_folder = os.path.join(data_folder, 'test_works', self.request.id)
    if os.path.lexists(work_folder):
        raise RuntimeError('Work folder already exists')

    # copy test environment to work folder
    env_folder = os.path.join(data_folder, 'test_environments', str(task_id))
    if os.path.isdir(env_folder):  # env folder has higher priority than env archive
        shutil.copytree(env_folder, work_folder)
    else:
        env_archive = os.path.join(data_folder, 'test_environments', '%d.zip' % task_id)
        if os.path.isfile(env_archive):
            shutil.unpack_archive(env_archive, work_folder)
        else:
            raise RuntimeError('Not test environment for task %s' % task_id)

    # download submission files into sub folder 'submission'
    submission_folder = os.path.join(work_folder, 'submission')
    if not os.path.lexists(submission_folder):
        os.mkdir(submission_folder)
    for file in submission['files']:
        local_save_path = os.path.join(work_folder, 'submission', file['requirement']['name'])
        download_submission_file(submission_id, self.request.id, file, local_save_path)

    # TODO timeout mechanism
    # TODO network/cpu/memory restrictions

    result = None
    files_to_upload = {}

    # If 'Dockerfile' exists, build docker image and run it
    dockerfile = os.path.join(work_folder, 'Dockerfile')
    if os.path.isfile(dockerfile):
        tag = 'submit-test-%s' % self.request.id
        image, build_logs = docker_client.images.build(path=work_folder, pull=True, tag=tag)
        files_to_upload['docker-build-logs.json'] = json.dumps(list(build_logs))
        run_logs = docker_client.containers.run(image.id, remove=True, network_disabled=True,
                                                stdout=True, stderr=True)
        files_to_upload['run.log'] = run_logs
    else:
        # Otherwise look for 'run.sh' and run it in the bare environment.
        # Make sure 'run.sh' has the execution permission. (chmod +x)
        run_script = os.path.join(work_folder, 'run.sh')
        if not os.path.isfile(run_script):
            raise RuntimeError('Start script not found')
        proc_result = subprocess.run([os.path.abspath(run_script)], cwd=work_folder, stdout=subprocess.PIPE, check=True)
        if proc_result.stdout:
            try:
                last_line = proc_result.stdout.decode().strip().split('\n')[-1].strip()
                try:
                    result = json.loads(last_line)
                except (ValueError, TypeError):
                    result = last_line
            except ValueError:
                pass
            files_to_upload['stdout.txt'] = proc_result.stdout
        if proc_result.stderr:
            files_to_upload['stderr.txt'] = proc_result.stderr

    if files_to_upload:
        upload_output_files(submission_id, self.request.id, files_to_upload)

    return result
