import json
import logging
import os
import re
import shutil
import tempfile
import time
import zipfile
from datetime import datetime
from io import StringIO
from typing import Optional

from flask import Blueprint, jsonify, request, current_app as app, send_from_directory

from anti_plagiarism.code_analysis import CodeSegmentIndex
from auth_connect.oauth import requires_login
from models import db, SpecialConsideration, UserTeamAssociation
from services.account import AccountService, AccountServiceError
from services.auto_test import AutoTestService, AutoTestServiceError
from services.final_marks import FinalMarksService, FinalMarksServiceError
from services.message_sender import MessageSenderService, MessageSenderServiceError
from services.messsage import MessageService, MessageServiceError
from services.submission import SubmissionService, SubmissionServiceError
from services.task import TaskService, TaskServiceError
from services.team import TeamService, TeamServiceError
from services.term import TermService, TermServiceError
from utils.message import build_message_with_template
from utils.upload import md5sum

task_api = Blueprint('task_api', __name__)
logger = logging.getLogger(__name__)


class SubmissionStatus:
    def __init__(self, attempts: Optional[int],
                 team_association: Optional[UserTeamAssociation],
                 special_consideration: Optional[SpecialConsideration]):
        self.attempts = attempts
        self.team_association = team_association
        self.special_consideration = special_consideration

    def to_dict(self):
        d = dict(attempts=self.attempts)
        d['team_association'] = self.team_association.to_dict(with_team=True) if self.team_association else None
        d['special_consideration'] = self.special_consideration.to_dict() if self.special_consideration else None
        return d


@task_api.route('/<int:tid>')
@requires_login
def do_task(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)
        if not roles:
            return jsonify(msg='access forbidden'), 403

        preview_mode = request.args.get('preview')
        if preview_mode:
            return jsonify(task.to_dict())
        else:  # getting task details requires either admin/tutor role or after the opening time
            with_advanced_fields = True
            if 'admin' not in roles and 'tutor' not in roles:
                with_advanced_fields = False  # getting advanced fields requires admin or tutor role
                if not task.open_time or task.open_time > datetime.utcnow():
                    return jsonify(msg='task has not yet open'), 403
            return jsonify(task.to_dict(with_details=True, with_advanced_fields=with_advanced_fields))
    except (TaskServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/user-submission-summaries')
@requires_login
def task_user_submission_summaries(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        # allow access even before the opening time

        return jsonify([s.to_dict() for s in SubmissionService.get_user_summaries(task)])
    except (TaskServiceError, TermServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/team-submission-summaries')
@requires_login
def task_team_submission_summaries(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        # allow access even before the opening time

        return jsonify([s.to_dict() for s in SubmissionService.get_team_summaries(task)])
    except (TaskServiceError, TermServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/daily-submission-summaries')
@requires_login
def task_daily_submission_summaries(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        # allow access even before the opening time

        return jsonify([s.to_dict() for s in SubmissionService.get_daily_summaries(task)])
    except (TaskServiceError, TermServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/user-submissions/<int:uid>')
@requires_login
def task_user_submissions(tid, uid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        target_user = AccountService.get_user(uid)
        if target_user is None:
            return jsonify(msg='target user not found'), 404

        # allow access even before the opening time

        return jsonify([s.to_dict() for s in SubmissionService.get_for_task_and_user(task, target_user,
                                                                                     include_cleared=True)])
    except (TaskServiceError, TermServiceError, AccountServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/user-submissions/<int:uid>/last-auto-tests')
@requires_login
def task_user_submissions_last_auto_tests(tid, uid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        target_user = AccountService.get_user(uid)
        if target_user is None:
            return jsonify(msg='target user not found'), 404

        # allow access even before the opening time

        last_tests = SubmissionService.get_last_auto_tests_for_task_and_user(task, target_user, include_cleared=True,
                                                                             include_private_tests=True)
        return jsonify({sid: {cid: AutoTestService.test_to_dict(test) for cid, test in tests.items()}
                        for sid, tests in last_tests.items()})
    except (TaskServiceError, TermServiceError, AccountServiceError, SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/user-submissions/<int:uid>/auto-test-conclusions')
@requires_login
def task_user_submissions_auto_test_conclusions(tid, uid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        target_user = AccountService.get_user(uid)
        if target_user is None:
            return jsonify(msg='target user not found'), 404

        # allow access even before the opening time

        return jsonify(SubmissionService.get_auto_test_conclusions_for_task_and_user(task, target_user,
                                                                                     include_private_tests=True))
    except (TaskServiceError, TermServiceError, AccountServiceError, SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/users/<int:uid>')
@requires_login
def get_user(task_id, uid):
    """
    Convenience api for tutors to get student info
    """
    try:
        task = TaskService.get(task_id)
        if task is None:
            return jsonify('task not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 500
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        target_user = AccountService.get_user(uid)
        if target_user is None:
            return jsonify(msg='target user not found'), 404
        if 'student' not in TermService.get_access_roles(task.term, target_user):
            return jsonify(msg='target user is not a student of this task'), 403

        return jsonify(target_user.to_dict())
    except (AccountServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/anti-plagiarism/<int:requirement_id>')
@requires_login
def task_anti_plagiarism(task_id, requirement_id):
    try:
        task = TaskService.get(task_id)
        if task is None:
            return jsonify('task not found'), 404

        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 500
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        requirement = TaskService.get_file_requirement(requirement_id)
        if requirement is None:
            return jsonify(msg='requirement not found'), 404
        if requirement.task_id != task_id:
            return jsonify(msg='requirement does not belong to this task'), 400
        if not requirement.name.endswith('.py'):
            return jsonify(msg='file type not supported'), 400

        index = CodeSegmentIndex()
        data_folder = app.config['DATA_FOLDER']
        user_set = set()
        valid_file_count = 0
        syntax_error_count = 0
        io_error_count = 0

        if task.is_team_task:
            # If task is a team task, treat a team as a single 'user'.
            file_tuples = SubmissionService.get_team_files(requirement_id)
        else:
            file_tuples = SubmissionService.get_files(requirement_id)
        for sid, uid, file in file_tuples:
            user_set.add(uid)
            try:
                index.process_file(uid, sid, os.path.join(data_folder, file.path), file.md5)
            except SyntaxError:
                logger.debug('Syntax Error in (uid: %s, sid: %s)' % (uid, sid))
                syntax_error_count += 1
                continue
            except IOError:
                logger.warning('IO Error in (uid: %s, sid: %s)' % (uid, sid), exc_info=True)
                io_error_count += 1
                continue
            valid_file_count += 1
        logger.info('Processed users/teams: %d, valid files: %d, syntax errors: %d, io errors: %d' %
                    (len(user_set), valid_file_count, syntax_error_count, io_error_count))

        results = index.get_duplicates()[0:100]  # return top 100 results
        with StringIO() as buffer:
            index.pretty_print_results(results, file=buffer)
            return buffer.getvalue(), {'Content-Type': 'text/plain'}
    except (TaskServiceError, TermServiceError, AccountServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/submission-status/<int:uid>')
@requires_login
def task_user_submission_status(tid, uid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        target_user = AccountService.get_user(uid)
        if target_user is None:
            return jsonify(msg='target user not found'), 404
        if 'student' not in TermService.get_access_roles(task.term, target_user):
            return jsonify(msg='target user is not a student of this task'), 403

        attempts = SubmissionService.count_for_task_and_user(task, target_user, include_cleared=True)
        special = TaskService.get_special_consideration_for_task_user(task, target_user)
        status = SubmissionStatus(attempts, None, special)
        return jsonify(status.to_dict())
    except (TaskServiceError, TermServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/team-submission-status/<int:team_id>')
@requires_login
def task_team_submission_status(task_id, team_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(task_id)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='team not found'), 404
        if team.task_id != task_id:
            return jsonify(msg='team does not belong to this task'), 400

        # although seems redundant, we still get the association between this team and the team creator to make the
        # returned result consistent with other apis
        ass = TeamService.get_team_association_directly(team, team.creator)

        if team.is_finalised:
            attempts = SubmissionService.count_for_team(team, include_cleared=True)
            special = TaskService.get_special_consideration_for_team(team)
            status = SubmissionStatus(attempts, ass, special)
        else:
            status = SubmissionStatus(None, ass, None)
        return jsonify(status.to_dict())
    except (TaskServiceError, TermServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/my-submission-status')
@requires_login
def task_my_submission_status(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'student' not in roles:
            return jsonify(msg='only for students'), 403

        attempts = SubmissionService.count_for_task_and_user(task, user, include_cleared=True)
        special = TaskService.get_special_consideration_for_task_user(task, user)
        status = SubmissionStatus(attempts, None, special)
        return jsonify(status.to_dict())
    except (TaskServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/my-team-submission-status')
@requires_login
def task_my_team_submission_status(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'student' not in roles:
            return jsonify(msg='only for students'), 403

        # team check
        ass = TeamService.get_team_association(task, user)
        if ass and ass.team.is_finalised:
            attempts = SubmissionService.count_for_team(ass.team, include_cleared=True)
            special = TaskService.get_special_consideration_for_team(ass.team)
            status = SubmissionStatus(attempts, ass, special)
        else:
            status = SubmissionStatus(None, ass, None)
        return jsonify(status.to_dict())
    except (TaskServiceError, TermServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/team-submissions/<int:team_id>')
@requires_login
def task_team_submissions(tid, team_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='target team not found'), 404
        if team.task_id != tid:
            return jsonify(msg='target team does not belong to this task'), 400

        # allow access even before the opening time

        return jsonify([s.to_dict(with_submitter=True) for s in SubmissionService.get_for_team(team,
                                                                                               include_cleared=True)])
    except (TaskServiceError, TermServiceError, SubmissionServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/team-submissions/<int:team_id>/last-auto-tests')
@requires_login
def task_team_submissions_last_auto_tests(tid, team_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='target team not found'), 404
        if team.task_id != tid:
            return jsonify(msg='target team does not belong to this task'), 400

        # allow access even before the opening time

        last_tests = SubmissionService.get_last_auto_tests_for_team(team, include_cleared=True,
                                                                    include_private_tests=True)
        return jsonify({sid: {cid: AutoTestService.test_to_dict(test) for cid, test in tests.items()}
                        for sid, tests in last_tests.items()})
    except (TaskServiceError, TermServiceError, SubmissionServiceError, AutoTestServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/team-submissions/<int:team_id>/auto-test-conclusions')
@requires_login
def task_team_submissions_auto_test_conclusions(tid, team_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        team = TeamService.get(team_id)
        if team is None:
            return jsonify(msg='target team not found'), 404
        if team.task_id != tid:
            return jsonify(msg='target team does not belong to this task'), 400

        # allow access even before the opening time

        return jsonify(SubmissionService.get_auto_test_conclusions_for_team(team, include_private_tests=True))
    except (TaskServiceError, TermServiceError, SubmissionServiceError, AutoTestServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/my-submissions', methods=['GET', 'POST'])
@requires_login
def task_my_submissions(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'student' not in roles:
            return jsonify(msg='only for students'), 403

        if request.method == 'GET':
            # if not task.open_time or datetime.utcnow() < task.open_time:
            #     return jsonify(msg='task has not yet open'), 403
            return jsonify([s.to_dict() for s in SubmissionService.get_for_task_and_user(task, user)])
        else:  # POST
            # time check will be done in SubmissionService.add method

            # prepare files and paths
            data_folder = app.config['DATA_FOLDER']
            folder = os.path.join('tasks', str(task.id), 'submissions', user.name, str(time.time()))
            files = {}
            save_paths = {}
            requirements = {r.id: r for r in task.file_requirements}
            for name, file in request.files.items():
                try:
                    req_id = int(name)
                    req = requirements[req_id]
                except (ValueError, KeyError):
                    return jsonify(msg='invalid field', detail='invalid requirement id: %r' % name), 400
                files[req_id] = file
                save_paths[req_id] = os.path.join(folder, req.name)

            # create new submission
            allow_before_open = 'admin' in roles or 'tutor' in roles
            new_submission, submissions_to_clear, submitted_for_team = \
                SubmissionService.add(task, user, files, save_paths, allow_before_open)

            # clear outdated submissions according to history limit
            file_paths_to_remove = []
            for submission in submissions_to_clear:
                file_paths_to_remove.append(SubmissionService.clear_submission(submission))

            # prepare new folder
            folder_full = os.path.join(data_folder, folder)
            if os.path.lexists(folder_full):
                return jsonify(msg='submission folder already exists'), 500
            os.makedirs(folder_full)

            # save new files
            file_objects = {f.requirement.id: f for f in new_submission.files}
            for req_id in files:
                req = requirements[req_id]
                file = files[req_id]
                file_obj = file_objects[req_id]
                path = save_paths[req_id]
                full_path = os.path.join(data_folder, path)
                file.save(full_path)

                # size check
                size = os.stat(full_path).st_size
                if req.size_limit is not None and size > req.size_limit:
                    shutil.rmtree(folder_full)  # remove the whole folder
                    return jsonify(msg='file too big', detail=req.name), 400
                file_obj.size = size

                # md5 hash
                file_obj.md5 = md5sum(full_path)

            # remove outdated files
            for batch in file_paths_to_remove:
                for file_path in batch:
                    full_path = os.path.join(data_folder, file_path)
                    if os.path.isfile(full_path):
                        os.remove(full_path)
                # try to delete parent folder if empty now (try to be conservative and make it extensible)
                if batch:
                    folder = os.path.dirname(batch[0])
                    folder_full = os.path.join(data_folder, folder)
                    if os.path.isdir(folder_full) and not os.listdir(folder_full):
                        os.rmdir(folder_full)

            # also clear auto tests if any
            for submission in submissions_to_clear:
                for test in submission.auto_tests:
                    for file in test.output_files:
                        save_path_full = os.path.join(data_folder, file.save_path)
                        if os.path.lexists(save_path_full):
                            os.remove(save_path_full)
                    if test.output_files:  # try to remove parent folder if empty now
                        folder_path = os.path.dirname(test.output_files[0].save_path)
                        folder_path_full = os.path.join(data_folder, folder_path)
                        if os.path.lexists(folder_path_full) and not os.listdir(folder_path_full):
                            os.rmdir(folder_path_full)
                    result = AutoTestService.get_result(test)
                    result.forget()  # remove temporary result from storage (if any)

                    for file in test.output_files:
                        db.session.delete(file)
                    db.session.delete(test)

            db.session.commit()

            # start auto test if required
            if task.evaluation_method == 'auto_test':
                configs_to_run = []
                for config in task.auto_test_configs:
                    if not config.is_enabled or config.trigger != 'after_submit':
                        continue
                    configs_to_run.append(config)
                configs_to_run.sort(key=lambda c: c.id)  # sort by id first
                configs_to_run.sort(key=lambda c: c.priority, reverse=True)  # then by priority (reversed)
                # TODO how to use global priority control in Celery?
                for config in configs_to_run:
                    SubmissionService.run_auto_test(new_submission, config)
                db.session.commit()  # have to commit again

            # if this is a team task, notify other teammates about this submission
            if task.is_team_task:
                team_other_members = [ass.user for ass in submitted_for_team.user_associations
                                      if ass.user.id != user.id]
                if team_other_members:
                    submitter_name = '%s (%s)' % (user.nickname, user.name) if user.nickname else user.name
                    msg_args = dict(site=app.config['SITE'],
                                    submitter_name=submitter_name,
                                    submission=new_submission,
                                    team=submitted_for_team,
                                    task=task,
                                    term=task.term)
                    msg_content = build_message_with_template('team_new_teammate_submission', msg_args)
                    msg_channel = MessageService.get_channel_by_name('team')
                    msgs, mails = MessageSenderService.send_to_users(msg_channel, task.term, msg_content, None,
                                                                     team_other_members)
                    db.session.commit()
                    for mail in mails:
                        mail.send()

            return jsonify(new_submission.to_dict()), 201

    except (TaskServiceError, TermServiceError, SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
    except (MessageServiceError, MessageSenderServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 500


@task_api.route('/<int:tid>/my-submissions/last-auto-tests')
@requires_login
def task_my_submissions_last_auto_tests(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'student' not in roles:
            return jsonify(msg='only for students'), 403

        # if not task.open_time or datetime.utcnow() < task.open_time:
        #     return jsonify(msg='task has not yet open'), 403

        last_tests = SubmissionService.get_last_auto_tests_for_task_and_user(task, user)
        return jsonify({sid: {cid: AutoTestService.test_to_dict(test) for cid, test in tests.items()}
                        for sid, tests in last_tests.items()})
    except (TaskServiceError, TermServiceError, SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/my-submissions/auto-test-conclusions')
@requires_login
def task_my_submissions_auto_test_conclusions(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'student' not in roles:
            return jsonify(msg='only for students'), 403

        # if not task.open_time or datetime.utcnow() < task.open_time:
        #     return jsonify(msg='task has not yet open'), 403

        return jsonify(SubmissionService.get_auto_test_conclusions_for_task_and_user(task, user))
    except (TaskServiceError, TermServiceError, SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/my-team-submissions', methods=['GET'])
@requires_login
def task_my_team_submissions(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'student' not in roles:
            return jsonify(msg='only for students'), 403

        # team check
        ass = TeamService.get_team_association(task, user)
        if not ass:
            return jsonify(msg='user not in a team'), 403
        team = ass.team
        if not team.is_finalised:
            return jsonify(msg='team is not finalised'), 403

        # time check
        # if not task.open_time or datetime.utcnow() < task.open_time:
        #     return jsonify(msg='task has not yet open'), 403

        return jsonify([s.to_dict(with_submitter=True) for s in SubmissionService.get_for_team(team)])
    except (TaskServiceError, TermServiceError, TeamServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/my-team-submissions/last-auto-tests')
@requires_login
def task_my_team_submissions_last_auto_tests(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'student' not in roles:
            return jsonify(msg='only for students'), 403

        # team check
        ass = TeamService.get_team_association(task, user)
        if not ass:
            return jsonify(msg='user not in a team'), 403
        team = ass.team
        if not team.is_finalised:
            return jsonify(msg='team is not finalised'), 403

        # time check
        # if not task.open_time or datetime.utcnow() < task.open_time:
        #     return jsonify(msg='task has not yet open'), 403

        last_tests = SubmissionService.get_last_auto_tests_for_team(team)
        return jsonify({sid: {cid: AutoTestService.test_to_dict(test) for cid, test in tests.items()}
                        for sid, tests in last_tests.items()})
    except (TaskServiceError, TermServiceError, TeamServiceError, SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/my-team-submissions/auto-test-conclusions')
@requires_login
def task_my_team_submissions_auto_test_conclusions(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'student' not in roles:
            return jsonify(msg='only for students'), 403

        # team check
        ass = TeamService.get_team_association(task, user)
        if not ass:
            return jsonify(msg='user not in a team'), 403
        team = ass.team
        if not team.is_finalised:
            return jsonify(msg='team is not finalised'), 403

        # time check
        # if not task.open_time or datetime.utcnow() < task.open_time:
        #     return jsonify(msg='task has not yet open'), 403

        return jsonify(SubmissionService.get_auto_test_conclusions_for_team(team))
    except (TaskServiceError, TermServiceError, TeamServiceError, SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/teams', methods=['GET', 'POST'])
@requires_login
def do_teams(task_id):
    try:
        task = TaskService.get(task_id)
        if task is None:
            return jsonify(msg='task not found'), 404

        if request.method == 'GET':
            return jsonify([(t.to_dict(with_creator=True), total_user_associations)
                            for t, total_user_associations in TeamService.get_summaries_for_task(task)])
        else:  # POST
            user = AccountService.get_current_user()
            if user is None:
                return jsonify(msg='no user info'), 403

            params = request.json
            team = TeamService.add(task, user, params.get('name'), params.get('slogan'))
            db.session.commit()
            return jsonify(team.to_dict(with_associations=True)), 201
    except (TaskServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/team_free_users', methods=['GET'])
@requires_login
def team_free_users(task_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(task_id)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        return jsonify([u.to_dict(with_groups=False) for u in TeamService.get_free_users_for_task(task)])
    except (TaskServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/my-team-association', methods=['GET'])
@requires_login
def my_team_association(task_id):
    try:
        task = TaskService.get(task_id)
        if task is None:
            return jsonify(msg='task not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403

        ass = TeamService.get_team_association(task, user)
        if not ass:
            return "", 204
        return jsonify(ass.to_dict(with_team=True))
    except (TaskServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/team-associations/<int:uid>', methods=['GET'])
@requires_login
def team_association(task_id, uid):
    try:
        task = TaskService.get(task_id)
        if task is None:
            return jsonify(msg='task not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        target_user = AccountService.get_user(uid)
        if target_user is None:
            return jsonify(msg='user not found'), 404
        ass = TeamService.get_team_association(task, target_user)
        if not ass:
            return "", 204
        return jsonify(ass.to_dict(with_team=True))
    except (TaskServiceError, TeamServiceError, TermServiceError, AccountServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/team-association-by-user-name/<string:name>', methods=['GET'])
@requires_login
def team_association_by_user_name(task_id, name):
    try:
        task = TaskService.get(task_id)
        if task is None:
            return jsonify(msg='task not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 403
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        target_user = AccountService.get_user_by_name(name)
        if target_user is None:
            return jsonify(msg='user not found'), 404
        ass = TeamService.get_team_association(task, target_user)
        if not ass:
            return "", 204
        return jsonify(ass.to_dict(with_team=True))
    except (TaskServiceError, TeamServiceError, TermServiceError, AccountServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/download-materials-zip', methods=['GET'])
@requires_login
def download_materials_zip(task_id):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(task_id)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)
        if not roles:
            return jsonify(msg='access forbidden'), 403

        include_private = request.args.get('include_private') == 'true'
        if 'admin' not in roles and 'tutor' not in roles:
            if include_private:
                return jsonify(msg='access forbidden'), 403
            if not task.open_time or task.open_time > datetime.utcnow():
                return jsonify(msg='task has not yet open'), 403

        tmp_dir = os.path.join(tempfile.gettempdir(), 'submit-material-zips')
        tmp_dir_required_mode = 0o700
        if os.path.lexists(tmp_dir):
            mode = os.stat(tmp_dir).st_mode & 0o777
            if mode != tmp_dir_required_mode:
                return jsonify(msg='tmp folder has incorrect mode: %s' % oct(mode)), 500
        else:
            os.makedirs(tmp_dir, mode=tmp_dir_required_mode)

        zip_file_name = None

        # try to get cached zip file
        if include_private:
            zip_meta_path = os.path.join(tmp_dir, "%d-private.json" % task_id)
        else:
            zip_meta_path = os.path.join(tmp_dir, "%d.json" % task_id)
        if os.path.isfile(zip_meta_path):
            with open(zip_meta_path) as f_meta:
                try:
                    zip_meta = json.load(f_meta)
                    zip_items = zip_meta['items']

                    match = True
                    for mat in task.materials:
                        if mat.is_private and not include_private:
                            continue
                        if zip_items.pop(mat.name) != mat.md5:
                            match = False
                            break
                    if match and not zip_items:  # no remaining items (exact match)
                        zip_file_name = zip_meta['zip']
                except (TypeError, ValueError, KeyError):
                    pass
            if not zip_file_name or not os.path.isfile(os.path.join(tmp_dir, zip_file_name)):
                zip_file_name = None

        if not zip_file_name:
            # make zip
            data_folder = app.config['DATA_FOLDER']
            zip_items = {}
            ffd = None
            try:
                fd, zip_file_path = tempfile.mkstemp(suffix='.zip', dir=tmp_dir)
                ffd = os.fdopen(fd, 'wb')
                zip_file_name = os.path.relpath(zip_file_path, tmp_dir)
                with zipfile.ZipFile(ffd, 'w', zipfile.ZIP_DEFLATED) as f_zip:
                    for mat in task.materials:
                        if mat.is_private and not include_private:
                            continue
                        f_zip.write(os.path.join(data_folder, mat.file_path),
                                    os.path.join('materials', mat.type, mat.name))
                        zip_items[mat.name] = mat.md5
            finally:
                if ffd:
                    ffd.close()

            try:
                # use exclusive file lock to avoid race condition
                lock_path = os.path.join(tmp_dir, "%d.lock" % task_id)
                with open(lock_path, 'x'):
                    # save meta
                    with open(zip_meta_path, 'w') as f_meta:
                        json.dump({
                            'zip': zip_file_name,
                            'items': zip_items
                        }, f_meta)
                os.remove(lock_path)
            except FileExistsError:
                pass

        # build attachment name
        term = task.term
        course = term.course
        zip_attachment_name = '%s-%dS%s-%s' % (course.code, term.year, term.semester, task.title)
        if include_private:
            zip_attachment_name += '-private'
        zip_attachment_name += '.zip'
        zip_attachment_name = zip_attachment_name.replace(' ', '_')
        return send_from_directory(tmp_dir, zip_file_name, as_attachment=True,
                                   attachment_filename=zip_attachment_name, cache_timeout=0)
    except (TaskServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/auto-test-conclusions')
@requires_login
def task_auto_test_conclusions(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        # allow access even before the opening time

        return jsonify(SubmissionService.get_auto_test_conclusions_for_task(task, include_private_tests=True))
    except (TaskServiceError, TermServiceError, AccountServiceError, SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/last-late-penalties')
@requires_login
def task_last_late_penalties(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        # allow access even before the opening time


        all_penalties = SubmissionService.get_late_penalties_for_task(task)
        if all_penalties is None:
            return '', 204
        last_penalties = {}
        for unit_id, penalties in all_penalties.items():
            if penalties:
                # pick the late penalty for the last submission of each unit (User/Team)
                last_penalties[unit_id] = penalties[max(penalties.keys())]
        return jsonify(last_penalties)
    except (TaskServiceError, TermServiceError, AccountServiceError, SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/export-results')
@requires_login
def task_export_results(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        # allow access even before the opening time

        configs = task.auto_test_configs
        conclusions = SubmissionService.get_auto_test_conclusions_for_task(task, include_private_tests=True)

        if task.is_team_task:
            expand_team_members = request.args.get('members') == 'true'
            summaries = SubmissionService.get_team_summaries(task)
            with StringIO() as buffer:
                if not expand_team_members:
                    buffer.write('\t'.join(['ID', 'Name'] + [c.name for c in configs]))
                    buffer.write('\n')
                    for summary in summaries:
                        team_conclusions = conclusions.get(summary.team.id, {})
                        buffer.write('\t'.join([str(summary.team.id), summary.team.name] +
                                               [str(team_conclusions.get(c.id)) for c in configs]))
                        buffer.write('\n')
                else:
                    buffer.write('\t'.join(['TeamID', 'TeamName', 'UserID', 'UserName'] + [c.name for c in configs]))
                    buffer.write('\n')
                    for summary in summaries:
                        team = summary.team
                        team_conclusions = conclusions.get(team.id, {})
                        conclusion_columns = [str(team_conclusions.get(c.id)) for c in configs]
                        for ass in team.user_associations:
                            buffer.write('\t'.join([str(team.id), team.name, str(ass.user.id), ass.user.name] +
                                                   conclusion_columns))
                            buffer.write('\n')
                return buffer.getvalue(), {'Content-Type': 'text/plain'}
        else:
            summaries = SubmissionService.get_user_summaries(task)
            with StringIO() as buffer:
                buffer.write('\t'.join(['ID', 'Name'] + [c.name for c in configs]))
                buffer.write('\n')
                for summary in summaries:
                    user_conclusions = conclusions.get(summary.user.id, {})
                    buffer.write('\t'.join([str(summary.user.id), summary.user.name] +
                                           [str(user_conclusions.get(c.id)) for c in configs]))
                    buffer.write('\n')
                return buffer.getvalue(), {'Content-Type': 'text/plain'}
    except (TaskServiceError, TermServiceError, AccountServiceError, SubmissionServiceError, AutoTestServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/export-teams')
@requires_login
def task_export_teams(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404

        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        if not task.is_team_task:
            return jsonify(msg='task is not team task'), 400

        teams = TeamService.get_for_task(task, joined_load_user_associations=True)
        with StringIO() as buffer:
            buffer.write('\t'.join(['TeamID', 'TeamName', 'UserID', 'UserName']))
            buffer.write('\n')
            for team in teams:
                for ass in team.user_associations:
                    buffer.write('\t'.join([str(team.id), team.name, str(ass.user.id), ass.user.name]))
                    buffer.write('\n')
            return buffer.getvalue(), {'Content-Type': 'text/plain'}
    except (TaskServiceError, TermServiceError, AccountServiceError, TeamServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/find-submission-by-auto-test-id/<int:test_id>')
@requires_login
def task_find_submission_by_auto_test_id(task_id, test_id):
    try:
        task = TaskService.get(task_id)
        if task is None:
            return jsonify('task not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 500
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        auto_test = AutoTestService.get(test_id)

        if auto_test is None:
            return jsonify(msg='auto test not found'), 404
        submission = auto_test.submission
        if submission.task_id != task.id:
            return jsonify(msg='submission does not belong to this task'), 400

        return jsonify(submission.to_dict())
    except (AccountServiceError, TermServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:task_id>/comment-summaries')
@requires_login
def task_comment_summaries(task_id):
    try:
        task = TaskService.get(task_id)
        if task is None:
            return jsonify('task not found'), 404
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='no user info'), 500
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        return jsonify([s.to_dict() for s in SubmissionService.get_comment_summaries(task)])
    except (AccountServiceError, TermServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/download-user-submissions/<int:user_id>')
@task_api.route('/<int:tid>/download-team-submissions/<int:team_id>')
@requires_login
def task_download_submissions(tid, user_id=None, team_id=None):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403
        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        if not task.is_team_task and team_id is not None:
            return jsonify(msg='only for team task'), 400

        if team_id is not None:
            team = TeamService.get(team_id)
            if team is None:
                return jsonify(msg='team not found'), 404
            if team.task_id != tid:
                return jsonify(msg='target team does not belong to this task'), 400
            submissions = SubmissionService.get_for_team(team)
            target_name = team.name
        else:
            target_user = AccountService.get_user(user_id)
            if target_user is None:
                return jsonify(msg='user not found'), 404
            submissions = SubmissionService.get_for_task_and_user(task, target_user)
            target_name = target_user.name

        data_folder = app.config['DATA_FOLDER']
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_name = '%s.zip' % target_name
            zip_path = os.path.join(tmp_dir, zip_name)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as f_zip:
                for sub in submissions:
                    for sub_file in sub.files:
                        f_zip.write(os.path.join(data_folder, sub_file.path),
                                    os.path.join(target_name, str(sub.id), sub_file.requirement.name))
            return send_from_directory(tmp_dir, zip_name, as_attachment=True, attachment_filename=zip_name,
                                       cache_timeout=0)
    except (TaskServiceError, TermServiceError, AccountServiceError, TeamServiceError, SubmissionServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/final-marks')
@requires_login
def do_final_marks(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403

        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        return jsonify([m.to_dict(with_user=False, with_comment=True, with_advanced_fields=True)
                        for m in FinalMarksService.get_for_task(task)])
    except (AccountServiceError, TaskServiceError, TermServiceError, FinalMarksServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/my-final-marks')
@requires_login
def do_my_final_marks(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404

        if not task.is_final_marks_released:
            return jsonify(msg='final marks not released'), 403
        record = FinalMarksService.get(user, task)
        if record is None:
            return "", 204
        return jsonify(record.to_dict(with_comment=True))
    except (AccountServiceError, TaskServiceError, TermServiceError, FinalMarksServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400


@task_api.route('/<int:tid>/export-final-marks')
@requires_login
def export_final_marks(tid):
    try:
        user = AccountService.get_current_user()
        if user is None:
            return jsonify(msg='user info required'), 500
        task = TaskService.get(tid)
        if task is None:
            return jsonify(msg='task not found'), 404
        roles = TermService.get_access_roles(task.term, user)

        # role check
        if not roles:
            return jsonify(msg='access forbidden'), 403

        if 'admin' not in roles and 'tutor' not in roles:
            return jsonify(msg='only for admins or tutors'), 403

        basic_str_pattern = re.compile(r'^[ -~]*$')
        with StringIO() as buffer:
            buffer.write('\t'.join(['ID', 'Name', 'Marks', 'Comment']))
            buffer.write('\n')
            for record in sorted(FinalMarksService.get_for_task(task, joined_load_user=True),
                                 key=lambda x: x.user.name):
                marks = record.marks
                if int(marks) == marks:  # convert marks to int if value is not changed
                    marks = int(marks)
                comment = record.comment
                if comment:
                    if not basic_str_pattern.fullmatch(comment):
                        comment = "json:" + json.dumps(comment)
                else:
                    comment = ''
                buffer.write('\t'.join([str(record.user_id), record.user.name, str(marks), comment]))
                buffer.write('\n')
            return buffer.getvalue(), {'Content-Type': 'text/plain'}
    except (AccountServiceError, TaskServiceError, TermServiceError, FinalMarksServiceError) as e:
        return jsonify(msg=e.msg, detail=e.detail), 400
