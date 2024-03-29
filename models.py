import json
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

user_groups_alias = db.Table('user_groups_alias',
                             db.Column('user_id', db.Integer, db.ForeignKey('user_alias.id'), primary_key=True),
                             db.Column('group_id', db.Integer, db.ForeignKey('group_alias.id'), primary_key=True))

EXCEPTION_MESSAGE_SAFE_LENGTH = 32


class UserAlias(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    nickname = db.Column(db.String(16), unique=True)
    avatar = db.Column(db.String(128))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    submissions = db.relationship('Submission', backref=db.backref('submitter'))

    def __repr__(self):
        return '<UserAlias %r>' % self.name

    def to_dict(self, with_groups=True, with_group_ids=False, with_advanced_fields=False):
        _dict = dict(id=self.id, name=self.name, email=self.email, nickname=self.nickname, avatar=self.avatar)
        if with_groups:
            _dict['groups'] = [group.to_dict() for group in self.groups]
        if with_group_ids:
            _dict['group_ids'] = [group.id for group in self.groups]

        if with_advanced_fields:
            _dict['created_at'] = self.created_at
            _dict['modified_at'] = self.modified_at

        return _dict


class GroupAlias(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(24), unique=True, nullable=False)
    description = db.Column(db.String(256))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = db.relationship('UserAlias', secondary=user_groups_alias, backref=db.backref('groups', lazy=False))

    def to_dict(self, with_users=False, with_user_ids=False, with_advanced_fields=False):
        _dict = dict(id=self.id, name=self.name, description=self.description)
        if with_users:
            _dict['users'] = [user.to_dict(with_groups=False) for user in self.users]
        if with_user_ids:
            _dict['user_ids'] = [user.id for user in self.users]

        if with_advanced_fields:
            _dict['created_at'] = self.created_at
            _dict['modified_at'] = self.modified_at

        return _dict


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tutor_group_id = db.Column(db.Integer, db.ForeignKey('group_alias.id'), nullable=False)

    code = db.Column(db.String(16), unique=True, nullable=False)
    name = db.Column(db.String(128), unique=True, nullable=False)
    icon = db.Column(db.String(128))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    terms = db.relationship('Term', backref=db.backref('course'))
    tutor_group = db.relationship('GroupAlias', backref=db.backref('tutor_of_courses'))

    def __repr__(self):
        return '<Course %r>' % self.name

    def to_dict(self, with_terms=False, with_groups=False, with_advanced_fields=False):
        d = dict(id=self.id, code=self.code, name=self.name, icon=self.icon, tutor_group_id=self.tutor_group_id)
        if with_terms:
            d['terms'] = [t.to_dict(with_course=False, with_groups=with_groups) for t in self.terms]
        if with_groups:
            d['tutor_group'] = self.tutor_group.to_dict()

        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d


class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    student_group_id = db.Column(db.Integer, db.ForeignKey('group_alias.id'), nullable=False)

    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.String(8), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = db.relationship('Task', backref=db.backref('term'))
    student_group = db.relationship('GroupAlias', backref=db.backref('student_of_terms'))

    def __repr__(self):
        return '<Term %r, %r>' % (self.year, self.semester)

    def to_dict(self, with_course=True, with_tasks=False, with_groups=False, with_advanced_fields=False):
        d = dict(id=self.id, course_id=self.course_id, year=self.year, semester=self.semester,
                 student_group_id=self.student_group_id)
        if with_course:
            d['course'] = self.course.to_dict()
        if with_tasks:
            d['tasks'] = [t.to_dict() for t in self.tasks]
        if with_groups:
            d['student_group'] = self.student_group.to_dict()

        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'), nullable=False)

    name = db.Column(db.String(16), nullable=False)
    is_finalised = db.Column(db.Boolean, nullable=False, default=False)
    avatar = db.Column(db.String(128))
    slogan = db.Column(db.String(64))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = db.relationship('Task', backref=db.backref('teams'))
    creator = db.relationship('UserAlias', backref=db.backref('created_teams'))

    def __repr__(self):
        return '<Team %r>' % self.id

    def to_dict(self, with_creator=False, with_associations=False):
        d = dict(id=self.id, task_id=self.task_id, creator_id=self.creator_id,
                 name=self.name,
                 is_finalised=self.is_finalised,
                 avatar=self.avatar, slogan=self.slogan,
                 created_at=self.created_at, modified_at=self.modified_at)
        if with_creator:
            d['creator'] = self.creator.to_dict()
        if with_associations:
            d['user_associations'] = [a.to_dict(with_user=True) for a in
                                      sorted(self.user_associations, key=lambda a: a.created_at)]
        return d


class UserTeamAssociation(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'), primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), primary_key=True)

    is_invited = db.Column(db.Boolean, nullable=False, default=False)
    is_user_agreed = db.Column(db.Boolean, nullable=False, default=False)
    is_creator_agreed = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('UserAlias', lazy=False, backref=db.backref('team_associations',
                                                                       cascade="all, delete-orphan"))
    team = db.relationship('Team', lazy=False, backref=db.backref('user_associations',
                                                                  cascade="all, delete-orphan"))

    def __repr__(self):
        return '<UserTeamAssociation (%r, %r)>' % (self.user_id, self.team_id)

    def to_dict(self, with_user=False, with_team=False):
        d = dict(user_id=self.user_id, team_id=self.team_id,
                 is_invited=self.is_invited,
                 is_user_agreed=self.is_user_agreed,
                 is_creator_agreed=self.is_creator_agreed,
                 created_at=self.created_at,
                 modified_at=self.modified_at)
        if with_user:
            d['user'] = self.user.to_dict()
        if with_team:
            d['team'] = self.team.to_dict()
        return d


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)

    type = db.Column(db.String(32), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)

    open_time = db.Column(db.DateTime)
    due_time = db.Column(db.DateTime)
    close_time = db.Column(db.DateTime)
    late_penalty = db.Column(db.String(128))

    is_team_task = db.Column(db.Boolean, nullable=False, default=False)
    team_min_size = db.Column(db.Integer)
    team_max_size = db.Column(db.Integer)
    team_join_close_time = db.Column(db.DateTime)

    submission_attempt_limit = db.Column(db.Integer)
    submission_history_limit = db.Column(db.Integer)

    evaluation_method = db.Column(db.String(32))

    is_final_marks_released = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    materials = db.relationship('Material', backref=db.backref('task'))
    file_requirements = db.relationship('FileRequirement', backref=db.backref('task'))
    submissions = db.relationship('Submission', backref=db.backref('task'))

    def __repr__(self):
        return '<Task %r>' % self.title

    def to_dict(self, with_term=False, with_details=False, with_advanced_fields=False):
        d = dict(id=self.id, term_id=self.term_id,
                 type=self.type, title=self.title, description=self.description,
                 open_time=self.open_time, due_time=self.due_time,
                 is_team_task=self.is_team_task, team_min_size=self.team_min_size, team_max_size=self.team_max_size,
                 team_join_close_time=self.team_join_close_time,
                 is_final_marks_released=self.is_final_marks_released)
        if with_term:
            d['term'] = self.term.to_dict()
        if with_details:
            d['late_penalty'] = self.late_penalty
            d['close_time'] = self.close_time
            d['submission_attempt_limit'] = self.submission_attempt_limit
            d['submission_history_limit'] = self.submission_history_limit
            d['evaluation_method'] = self.evaluation_method
            d['materials'] = sorted((m.to_dict()
                                     for m in self.materials
                                     if not m.is_private or with_advanced_fields), key=lambda m: m['id'])
            d['file_requirements'] = sorted((f.to_dict() for f in self.file_requirements), key=lambda f: f['id'])
            d['auto_test_configs'] = sorted((c.to_dict(with_advanced_fields=with_advanced_fields)
                                             for c in self.auto_test_configs
                                             if not c.is_private or with_advanced_fields), key=lambda c: c['id'])
        if with_advanced_fields:
            d['special_considerations'] = sorted((s.to_dict(with_user_or_team=True)
                                                  for s in self.special_considerations), key=lambda s: s['id'])
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d


class SpecialConsideration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

    due_time_extension = db.Column(db.Integer)
    submission_attempt_limit_extension = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = db.relationship('Task', backref=db.backref('special_considerations'))
    user = db.relationship('UserAlias', backref=db.backref('special_considerations'))
    team = db.relationship('Team', backref=db.backref('special_considerations'))

    def __repr__(self):
        return '<SpecialConsideration %r>' % self.id

    def to_dict(self, with_task=False, with_user_or_team=False):
        d = dict(id=self.id, task_id=self.task_id,
                 user_id=self.user_id,
                 team_id=self.team_id,
                 due_time_extension=self.due_time_extension,
                 submission_attempt_limit_extension=self.submission_attempt_limit_extension,
                 created_at=self.created_at, modified_at=self.modified_at)
        if with_task:
            d['task'] = self.task.to_dict()
        if with_user_or_team:
            d['user'] = self.user.to_dict() if self.user else None
            d['team'] = self.team.to_dict() if self.team else None
        return d


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)

    type = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    is_private = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.String(256))
    file_path = db.Column(db.String(128), nullable=False, unique=True)
    size = db.Column(db.Integer)
    md5 = db.Column(db.String(32))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<Material %r>' % self.name

    def to_dict(self, with_advanced_fields=False):
        d = dict(id=self.id, task_id=self.task_id, type=self.type, name=self.name, description=self.description,
                 is_private=self.is_private,
                 size=self.size, md5=self.md5,
                 created_at=self.created_at,
                 modified_at=self.modified_at)
        if with_advanced_fields:
            d['file_path'] = self.file_path
        return d


class FileRequirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)

    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256))
    is_optional = db.Column(db.Boolean, nullable=False, default=False)
    size_limit = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<FileRequirement %r>' % self.name

    def to_dict(self):
        d = dict(id=self.id, task_id=self.task_id, name=self.name, description=self.description,
                 is_optional=self.is_optional, size_limit=self.size_limit,
                 created_at=self.created_at,
                 modified_at=self.modified_at)
        return d


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    submitter_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'), nullable=False)

    is_cleared = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    files = db.relationship('SubmissionFile', backref=db.backref('submission'))

    def __repr__(self):
        return '<Submission %r>' % self.id

    def to_dict(self, with_files=False, with_submitter=False, with_auto_tests=False, with_advanced_fields=False):
        d = dict(id=self.id, task_id=self.task_id,
                 submitter_id=self.submitter_id,
                 is_cleared=self.is_cleared,
                 created_at=self.created_at,
                 modified_at=self.modified_at)
        if with_files:
            d['files'] = [f.to_dict(with_advanced_fields=with_advanced_fields) for f in self.files]
        if with_submitter:
            d['submitter'] = self.submitter.to_dict() if self.submitter else None
        if with_auto_tests:
            d['auto_tests'] = [t.to_dict() for t in self.auto_tests]
        return d


class SubmissionFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)
    requirement_id = db.Column(db.Integer, db.ForeignKey('file_requirement.id'), nullable=False)

    path = db.Column(db.String(128), nullable=False, unique=True)
    size = db.Column(db.Integer)
    md5 = db.Column(db.String(32))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirement = db.relationship('FileRequirement', backref=db.backref('submission_files'))

    def __repr__(self):
        return '<SubmissionFile %r>' % self.id

    def to_dict(self, with_requirement=True, with_advanced_fields=False):
        d = dict(id=self.id, submission_id=self.submission_id, requirement_id=self.requirement_id,
                 size=self.size,
                 md5=self.md5,
                 created_at=self.created_at,
                 modified_at=self.modified_at)
        if with_requirement:
            d['requirement'] = self.requirement.to_dict()
        if with_advanced_fields:
            d['path'] = self.path
        return d


class AutoTestConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(32), nullable=False)

    description = db.Column(db.String(256))
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    is_private = db.Column(db.Boolean, nullable=False, default=False)
    priority = db.Column(db.Integer, nullable=False, default=0)

    # execution config
    trigger = db.Column(db.String(32))
    environment_id = db.Column(db.Integer, db.ForeignKey('material.id'))
    file_requirement_id = db.Column(db.Integer, db.ForeignKey('file_requirement.id'))
    docker_auto_remove = db.Column(db.Boolean, nullable=False, default=True)
    docker_cpus = db.Column(db.Float)
    docker_memory = db.Column(db.Integer)
    docker_network = db.Column(db.Boolean, nullable=False, default=False)
    template_file_id = db.Column(db.Integer, db.ForeignKey('material.id'))

    # result handling
    result_render_html = db.Column(db.Text)
    result_conclusion_type = db.Column(db.String(16), nullable=False, default='json')
    result_conclusion_path = db.Column(db.String(128))
    result_conclusion_full_marks = db.Column(db.Float)
    result_conclusion_apply_late_penalty = db.Column(db.Boolean, nullable=False, default=True)
    results_conclusion_accumulate_method = db.Column(db.String(32), nullable=False, default='last')

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = db.relationship('Task', backref=db.backref('auto_test_configs'))
    environment = db.relationship('Material', backref=db.backref('as_environment_for_auto_test_configs'),
                                  foreign_keys='[AutoTestConfig.environment_id]')
    file_requirement = db.relationship('FileRequirement', backref=db.backref('auto_test_configs'))
    template_file = db.relationship('Material', backref=db.backref('as_template_file_for_auto_test_configs'),
                                    foreign_keys='[AutoTestConfig.template_file_id]')

    def __repr__(self):
        return '<AutoTestConfig %r>' % self.id

    def to_dict(self, with_environment=False, with_file_requirement=False, with_template_file=False,
                with_advanced_fields=False) -> dict:
        d = dict(id=self.id, name=self.name, type=self.type, description=self.description,
                 task_id=self.task_id, is_enabled=self.is_enabled, is_private=self.is_private, priority=self.priority,
                 trigger=self.trigger, environment_id=self.environment_id, file_requirement_id=self.file_requirement_id,
                 template_file_id=self.template_file_id,
                 result_render_html=self.result_render_html, result_conclusion_type=self.result_conclusion_type,
                 result_conclusion_path=self.result_conclusion_path,
                 result_conclusion_full_marks=self.result_conclusion_full_marks,
                 result_conclusion_apply_late_penalty=self.result_conclusion_apply_late_penalty,
                 results_conclusion_accumulate_method=self.results_conclusion_accumulate_method)
        if with_environment:
            d['environment'] = self.environment.to_dict() if self.environment_id is not None else None
        if with_file_requirement:
            d['file_requirement'] = self.file_requirement.to_dict() if self.file_requirement is not None else None
        if with_template_file:
            d['template_file'] = self.template_file.to_dict() if self.template_file is not None else None
        if with_advanced_fields:
            d['docker_auto_remove'] = self.docker_auto_remove
            d['docker_cpus'] = self.docker_cpus
            d['docker_memory'] = self.docker_memory
            d['docker_network'] = self.docker_network
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at

        return d


class AutoTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)
    config_id = db.Column(db.Integer, db.ForeignKey('auto_test_config.id'), nullable=False)

    work_id = db.Column(db.String(36), nullable=False)

    hostname = db.Column(db.String(128))
    pid = db.Column(db.Integer)

    final_state = db.Column(db.String(16))
    result = db.Column(db.String())
    exception_class = db.Column(db.String(64))
    exception_message = db.Column(db.String())
    exception_traceback = db.Column(db.String())

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    stopped_at = db.Column(db.DateTime)

    submission = db.relationship('Submission', backref=db.backref('auto_tests'))
    config = db.relationship('AutoTestConfig', backref=db.backref('tests'))

    def __repr__(self):
        return '<AutoTest %r>' % self.id

    def to_dict(self, with_submission=False, with_advanced_fields=False):
        d = dict(id=self.id, submission_id=self.submission_id, config_id=self.config_id,
                 hostname=self.hostname, final_state=self.final_state,
                 exception_class=self.exception_class,
                 created_at=self.created_at, modified_at=self.modified_at,
                 started_at=self.started_at, stopped_at=self.stopped_at)

        # limit the length of message to avoid 'Exception Attack'
        exception_message = self.exception_message
        if not with_advanced_fields and exception_message and len(exception_message) > EXCEPTION_MESSAGE_SAFE_LENGTH:
            exception_message = exception_message[0: EXCEPTION_MESSAGE_SAFE_LENGTH] + '...'
        d['exception_message'] = exception_message

        try:
            if self.result is not None:
                d['result'] = json.loads(self.result)  # try to parse result as JSON string
            else:
                d['result'] = None
        except ValueError:
            d['result'] = self.result

        if with_submission:
            d['submission'] = self.submission.to_dict()
        if with_advanced_fields:
            d['work_id'] = self.work_id
            d['pid'] = self.pid
            d['output_files'] = [file.to_dict(with_advanced_fields=True) for file in self.output_files]
            d['exception_traceback'] = self.exception_traceback
        return d


class AutoTestOutputFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auto_test_id = db.Column(db.Integer, db.ForeignKey('auto_test.id'), nullable=False)

    path = db.Column(db.String(128), nullable=False)
    save_path = db.Column(db.String(128), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    auto_test = db.relationship('AutoTest', backref=db.backref('output_files'))

    def __repr__(self):
        return '<AutoTestOutputFile %r>' % self.id

    def to_dict(self, with_auto_test=False, with_advanced_fields=False):
        d = dict(id=self.id, auto_test_id=self.auto_test_id, path=self.path,
                 created_at=self.created_at, modified_at=self.modified_at)
        if with_auto_test:
            d['auto_test'] = self.auto_test.to_dict()
        if with_advanced_fields:
            d['save_path'] = self.save_path
        return d


class MessageChannel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    description = db.Column(db.String(128))

    def to_dict(self):
        return dict(id=self.id, name=self.name, description=self.description)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('message_channel.id'), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)

    sender_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'))
    receiver_group_id = db.Column(db.Integer, db.ForeignKey('group_alias.id'))

    subject = db.Column(db.String(128), nullable=False)
    body = db.Column(db.Text)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    sender = db.relationship('UserAlias', backref=db.backref('messages_sent'),
                             foreign_keys='[Message.sender_id]')
    receiver = db.relationship('UserAlias', backref=db.backref('messages_received'),
                               foreign_keys='[Message.receiver_id]')
    receiver_group = db.relationship('GroupAlias', backref=db.backref('messages_received'))
    channel = db.relationship('MessageChannel', backref=db.backref('messages'))
    term = db.relationship('Term', backref=db.backref('messages'))

    def to_dict(self, with_sender: bool = True, with_receiver: bool = True, with_channel: bool = True,
                with_term: bool = False, with_body=True):
        d = dict(id=self.id, channel_id=self.channel_id, term_id=self.term_id, sender_id=self.sender_id,
                 receiver_id=self.receiver_id, receiver_group_id=self.receiver_group_id, subject=self.subject,
                 created_at=self.created_at)
        if with_sender:
            d['sender'] = self.sender.to_dict() if self.sender_id is not None else None
        if with_receiver:
            d['receiver'] = self.receiver.to_dict() if self.receiver_id is not None else None
            d['receiver_group'] = self.receiver_group.to_dict() if self.receiver_group_id is not None else None
        if with_channel:
            d['channel'] = self.channel.to_dict()
        if with_term:
            d['term'] = self.term.to_dict()
        if with_body:
            d['body'] = self.body
        return d


class MessageIsRead(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'), primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), primary_key=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('UserAlias', lazy=False, backref=db.backref('messages_read',
                                                                       cascade="all, delete-orphan"))
    message = db.relationship('Message', lazy=False, backref=db.backref('users_read',
                                                                        cascade="all, delete-orphan"))


class EmailSubscription(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'), primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('message_channel.id'), primary_key=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('UserAlias', lazy=False, backref=db.backref('email_subscriptions',
                                                                       cascade="all, delete-orphan"))
    channel = db.relationship('MessageChannel', lazy=False, backref=db.backref('email_subscriptions',
                                                                               cascade="all, delete-orphan"))


class SubmissionComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    content = db.Column(db.String(1024), nullable=False)

    submission = db.relationship('Submission', backref=db.backref('comments'))
    author = db.relationship('UserAlias', backref=db.backref('submission_comments'))

    def __repr__(self):
        return '<SubmissionComment %r>' % self.id

    def to_dict(self, with_submission=False, with_author=True) -> dict:
        d = dict(id=self.id, submission_id=self.submission_id, author_id=self.author_id,
                 created_at=self.created_at, modified_at=self.modified_at, content=self.content)
        if with_submission:
            d['submission'] = self.submission.to_dict()
        if with_author:
            d['author'] = self.author.to_dict() if self.author_id is not None else None
        return d


class FinalMarks(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), primary_key=True)

    marks = db.Column(db.Float, nullable=False)
    comment = db.Column(db.String(128))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('UserAlias', backref=db.backref('final_marks'))
    task = db.relationship('Task', backref=db.backref('final_marks'))

    def __repr__(self):
        return '<FinalMarks %d:%d>' % (self.user_id, self.task_id)

    def to_dict(self, with_user: bool = False, with_task: bool = False, with_comment: bool = False,
                with_advanced_fields: bool = False):
        d = dict(user_id=self.user_id, task_id=self.task_id, marks=self.marks)
        if with_user:
            d['user'] = self.user.to_dict(with_groups=False)
        if with_task:
            d['task'] = self.task.to_dict()
        if with_comment:
            d['comment'] = self.comment
        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d
