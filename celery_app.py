import hashlib
import json
import os
import random
import shutil
import ssl
import subprocess
import tempfile

import celery
import docker
import requests
from celery import Task
from docker.errors import ContainerError, BuildError

EXIT_STATUS_TIMEOUT = 124

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


def download_material(material: dict, folder: str, chunk_size: int = 65536) -> str:
    resp = requests.get('%sapi/materials/%d/worker-download' % (server_url, material['id']), auth=get_auth_param(),
                        stream=True)
    resp.raise_for_status()

    name = material['name']
    name_parts = name.rsplit('.', 2)
    if len(name_parts) > 1:
        name_parts[0] = ''
        suffix = '.'.join(name_parts)
    else:
        suffix = None

    ffd = None
    try:
        fd, path = tempfile.mkstemp(suffix=suffix, dir=folder)
        ffd = os.fdopen(fd, 'wb')
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:
                ffd.write(chunk)
    finally:
        if ffd:
            ffd.close()

    if material['md5'] != md5sum(path):
        raise RuntimeError('MD5 check of material "%s" failed' % material['name'])
    return os.path.relpath(path, folder)


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


def get_run_params(config_file_path: str) -> dict:
    """
    Parse a config file and convert the configs into running params. The keys of the config object may be different from
    the corresponding running params as we simplified them to hide the low-level jargon for easier use.
    :param config_file_path: a JSON object
    :return: a dictionary of running params
    """
    with open(config_file_path) as f_limits:
        params = {}
        for k, v in json.load(f_limits).items():
            if k == 'auto_remove':
                params['remove'] = v
            elif k == 'cpu':
                period = 100000
                params['cpu_period'] = period
                params['cpu_quota'] = int(v * period)
            elif k == 'memory':
                params['mem_limit'] = v
            elif k == 'memory_and_swap':
                # Notice: this limit requires system kernel support and may cause performance degradation.
                # See this link: https://docs.docker.com/config/containers/resource_constraints/
                params['memswap_limit'] = v
            elif k == 'network':
                params['network_disabled'] = not v
        return params


def extract_result(raw_output, result_tag):
    """
    Try to parse the last non-empty line from the raw output as the result
    :param raw_output: raw output from the test script or command inside Docker
    :param result_tag: tag for the result line
    :return: result if parsed successfully
    """
    if not raw_output or not result_tag:
        return None
    if isinstance(raw_output, (bytes, bytearray)):
        raw_output = raw_output.decode()
    lines = raw_output.strip().split('\n')

    result = None
    for line in lines:
        line = line.strip()
        if line and line.startswith(result_tag):
            result = line[len(result_tag):].strip()

    if result is None:
        return None
    try:
        return json.loads(result)
    except (ValueError, TypeError):
        return result


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
    test_environment = submission.get('auto_test_environment')
    if test_environment is None:
        raise RuntimeError('Test environment not specified')
    env_id = test_environment['id']
    env_md5 = test_environment['md5']

    # check work folder
    data_folder = config['DATA_FOLDER']
    work_folder = os.path.join(data_folder, 'test_works', self.request.id)
    if os.path.lexists(work_folder):
        raise RuntimeError('Work folder already exists')

    # check cached test environment
    env_folder = os.path.join(data_folder, 'test_environments')
    env_meta_path = os.path.join(env_folder, '%d.json' % env_id)
    env_zip_path = None

    if os.path.isfile(env_meta_path):
        with open(env_meta_path) as f_meta:
            try:
                env_meta = json.load(f_meta)
                if env_meta['md5'] == env_md5:
                    env_zip_path = env_meta['path']
            except (TypeError, ValueError, KeyError):
                pass
        if env_zip_path and not os.path.isfile(os.path.join(env_folder, env_zip_path)):
            env_zip_path = None

    # download environment if no cache found
    if not env_zip_path:
        env_zip_path = download_material(test_environment, env_folder)
        try:
            # use exclusive file lock to avoid race condition
            lock_path = os.path.join(env_folder, "%d.lock" % env_id)
            with open(lock_path, 'x'):
                # save meta
                with open(env_meta_path, 'w') as f_meta:
                    json.dump({
                        'path': env_zip_path,
                        'md5': env_md5
                    }, f_meta)
            os.remove(lock_path)
        except FileExistsError:
            pass

    # unpack environment zip to work folder
    shutil.unpack_archive(os.path.join(env_folder, env_zip_path), work_folder)

    # download submission files into sub folder 'submission'
    submission_folder = os.path.join(work_folder, 'submission')
    if not os.path.lexists(submission_folder):
        os.mkdir(submission_folder)
    for file in submission['files']:
        local_save_path = os.path.join(work_folder, 'submission', file['requirement']['name'])
        download_submission_file(submission_id, self.request.id, file, local_save_path)

    files_to_upload = {}

    try:
        # generate randomized result tag
        result_tag = '##RESULT%d##' % random.randint(100000, 999999)
        # generate additional environment variables
        env_vars = {'RESULT_TAG': result_tag}

        # If 'Dockerfile' exists, build docker image and run it
        dockerfile = os.path.join(work_folder, 'Dockerfile')
        if os.path.isfile(dockerfile):
            # get config for running the Docker container

            run_params = {
                'remove': True,  # by default, remove container after exit
                'environment': env_vars
            }
            docker_run_config = os.path.join(work_folder, 'docker-run-config.json')
            if os.path.isfile(docker_run_config):
                run_params.update(get_run_params(docker_run_config))

            # build Docker image
            build_logs = None
            try:
                tag = 'submit-test-%s' % self.request.id
                image, build_logs = docker_client.images.build(path=work_folder, tag=tag)
            except BuildError as e:
                build_logs = e.build_log
                raise
            finally:
                if build_logs:
                    files_to_upload['docker-build-logs.json'] = json.dumps(list(build_logs), indent=2)

            # run a Docker container with the specified limits and the new image
            try:
                # logs from stdout and stderr are combined due to the design of the API
                logs = docker_client.containers.run(image.id, name=tag, stdout=True, stderr=True, **run_params)
                if logs:
                    files_to_upload['docker-run-logs.txt'] = logs
                result = extract_result(logs, result_tag)
            except ContainerError as e:
                if e.stderr:
                    files_to_upload['docker-run-error.txt'] = e.stderr  # the error does not provide stdout
                if e.exit_status == EXIT_STATUS_TIMEOUT:
                    raise TimeoutError('Test command timeout')
                raise RuntimeError('Test command returned non-zero exit status %d' % e.exit_status)

            if run_params.get('remove'):
                # If container should be removed, also try to remove the image
                # This operation may fail due to multiple repository references or other running containers
                try:
                    docker_client.images.remove(image.id)
                except docker.errors.APIError as e:
                    # keep the error message but do not treat it as a failure
                    files_to_upload['docker-remove-image-error.txt'] = str(e)
        else:
            # Otherwise look for 'run.sh' and run it in the bare environment, which has no system isolation or
            # time/resource/network restrictions.
            run_script = os.path.join(work_folder, 'run.sh')
            if not os.path.isfile(run_script):
                raise RuntimeError('Test script not found')

            # make a copy of the current environment and add additional env vars
            env = os.environ.copy()
            env.update(env_vars)

            proc_result = subprocess.run(['bash', os.path.abspath(run_script)], cwd=work_folder,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            if proc_result.stdout:
                files_to_upload['stdout.txt'] = proc_result.stdout
            if proc_result.stderr:
                files_to_upload['stderr.txt'] = proc_result.stderr

            if proc_result.returncode:
                if proc_result.returncode == EXIT_STATUS_TIMEOUT:
                    raise TimeoutError('Test script timeout')
                raise RuntimeError('Test script returned non-zero exit status %d' % proc_result.returncode)
            result = extract_result(proc_result.stdout, result_tag)
    finally:
        if files_to_upload:
            upload_output_files(submission_id, self.request.id, files_to_upload)

    return result
