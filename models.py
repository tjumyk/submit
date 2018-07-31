from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

user_groups_alias = db.Table('user_groups_alias',
                             db.Column('user_id', db.Integer, db.ForeignKey('user_alias.id'), primary_key=True),
                             db.Column('group_id', db.Integer, db.ForeignKey('group_alias.id'), primary_key=True))


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

    def to_dict(self, with_groups=True, with_group_ids=False, with_associations=False, with_advanced_fields=False):
        _dict = dict(id=self.id, name=self.name, email=self.email, nickname=self.nickname, avatar=self.avatar)
        if with_groups:
            _dict['groups'] = [group.to_dict() for group in self.groups]
        if with_group_ids:
            _dict['group_ids'] = [group.id for group in self.groups]
        if with_associations:
            _dict['course_associations'] = [a.to_dict(with_course=True) for a in self.course_associations]
            _dict['term_associations'] = [a.to_dict(with_term=True) for a in self.term_associations]
            _dict['team_associations'] = [a.to_dict(with_team=True) for a in self.team_associations]

        if with_advanced_fields:
            _dict['created_at'] = self.created_at
            _dict['modified_at'] = self.modified_at

        return _dict


class GroupAlias(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), unique=True, nullable=False)
    description = db.Column(db.String(256))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = db.relationship('UserAlias', secondary=user_groups_alias, backref=db.backref('groups', lazy=False))

    def to_dict(self, with_users=False, with_user_ids=False, with_associations=False, with_advanced_fields=False):
        _dict = dict(id=self.id, name=self.name, description=self.description)
        if with_users:
            _dict['users'] = [user.to_dict(with_groups=False) for user in self.users]
        if with_user_ids:
            _dict['user_ids'] = [user.id for user in self.users]
        if with_associations:
            _dict['course_associations'] = [a.to_dict(with_course=True) for a in self.course_associations]
            _dict['term_associations'] = [a.to_dict(with_term=True) for a in self.term_associations]

        if with_advanced_fields:
            _dict['created_at'] = self.created_at
            _dict['modified_at'] = self.modified_at

        return _dict


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(16), unique=True, nullable=False)
    name = db.Column(db.String(128), unique=True, nullable=False)
    icon = db.Column(db.String(128))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    terms = db.relationship('Term', backref=db.backref('course'))

    def __repr__(self):
        return '<Course %r>' % self.name

    def to_dict(self, with_terms=False, with_associations=False, with_advanced_fields=False):
        d = dict(id=self.id, code=self.code, name=self.name, icon=self.icon)
        if with_terms:
            d['terms'] = [t.to_dict(with_course=False) for t in self.terms]
        if with_associations:
            d['user_associations'] = [a.to_dict(with_user=True) for a in self.user_associations]
            d['group_associations'] = [a.to_dict(with_group=True) for a in self.group_associations]

        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d


class UserCourseAssociation(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), primary_key=True)
    role = db.Column(db.String(16), nullable=False, primary_key=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('UserAlias', lazy=False, backref=db.backref('course_associations'))
    course = db.relationship('Course', lazy=False, backref=db.backref('user_associations'))

    def __repr__(self):
        return '<UserCourseAssociation (%r, %r)>' % (self.user_id, self.course_id)

    def to_dict(self, with_user=False, with_course=False, with_advanced_fields=False):
        d = dict(user_id=self.user_id, course_id=self.course_id, role=self.role)
        if with_user:
            d['user'] = self.user.to_dict()
        if with_course:
            d['course'] = self.course.to_dict()
        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d


class GroupCourseAssociation(db.Model):
    group_id = db.Column(db.Integer, db.ForeignKey('group_alias.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), primary_key=True)
    role = db.Column(db.String(16), nullable=False, primary_key=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    group = db.relationship('GroupAlias', lazy=False, backref=db.backref('course_associations'))
    course = db.relationship('Course', lazy=False, backref=db.backref('group_associations'))

    def __repr__(self):
        return '<GroupCourseAssociation (%r, %r)>' % (self.group_id, self.course_id)

    def to_dict(self, with_group=False, with_course=False, with_advanced_fields=False):
        d = dict(group_id=self.group_id, course_id=self.course_id, role=self.role)
        if with_group:
            d['group'] = self.group.to_dict()
        if with_course:
            d['course'] = self.course.to_dict()
        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d


class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.String(8), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = db.relationship('Task', backref=db.backref('term'))

    def __repr__(self):
        return '<Term %r, %r>' % (self.year, self.semester)

    def to_dict(self, with_course=True, with_tasks=False, with_associations=False, with_advanced_fields=False):
        d = dict(id=self.id, course_id=self.course_id, year=self.year, semester=self.semester)
        if with_course:
            d['course'] = self.course.to_dict()
        if with_tasks:
            d['tasks'] = [t.to_dict() for t in self.tasks]
        if with_associations:
            d['user_associations'] = [a.to_dict(with_user=True) for a in self.user_associations]
            d['group_associations'] = [a.to_dict(with_group=True) for a in self.group_associations]

        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d


class UserTermAssociation(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'), primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), primary_key=True)
    role = db.Column(db.String(16), nullable=False, primary_key=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('UserAlias', lazy=False, backref=db.backref('term_associations'))
    term = db.relationship('Term', lazy=False, backref=db.backref('user_associations'))

    def __repr__(self):
        return '<UserTermAssociation (%r, %r)>' % (self.user_id, self.term_id)

    def to_dict(self, with_user=False, with_term=False, with_advanced_fields=False):
        d = dict(user_id=self.user_id, term_id=self.term_id, role=self.role)
        if with_user:
            d['user'] = self.user.to_dict()
        if with_term:
            d['term'] = self.term.to_dict()
        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d


class GroupTermAssociation(db.Model):
    group_id = db.Column(db.Integer, db.ForeignKey('group_alias.id'), primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), primary_key=True)
    role = db.Column(db.String(16), nullable=False, primary_key=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    group = db.relationship('GroupAlias', lazy=False, backref=db.backref('term_associations'))
    term = db.relationship('Term', lazy=False, backref=db.backref('group_associations'))

    def __repr__(self):
        return '<GroupTermAssociation (%r, %r)>' % (self.group_id, self.term_id)

    def to_dict(self, with_group=False, with_term=False, with_advanced_fields=False):
        d = dict(group_id=self.group_id, term_id=self.term_id, role=self.role)
        if with_group:
            d['group'] = self.group.to_dict()
        if with_term:
            d['term'] = self.term.to_dict()
        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)

    name = db.Column(db.String(16), nullable=False)
    is_finalised = db.Column(db.Boolean, nullable=False, default=False)
    avatar = db.Column(db.String(128))
    slogan = db.Column(db.String(64))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    submissions = db.relationship('Submission', backref=db.backref('submitter_team'))

    def __repr__(self):
        return '<Team %r>' % self.name

    def to_dict(self, with_associations=False, with_advanced_fields=False):
        d = dict(id=self.id, term_id=self.term_id, name=self.name, is_finalised=self.is_finalised)
        if with_associations:
            d['user_associations'] = [a.to_dict(with_user=True) for a in self.user_associations]

        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d


class UserTeamAssociation(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'), primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), primary_key=True)

    is_creator = db.Column(db.Boolean, nullable=False, default=False)
    is_invited = db.Column(db.Boolean, nullable=False, default=False)
    is_user_agreed = db.Column(db.Boolean, nullable=False, default=False)
    is_creator_agreed = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('UserAlias', lazy=False, backref=db.backref('team_associations'))
    team = db.relationship('Team', lazy=False, backref=db.backref('user_associations'))

    def __repr__(self):
        return '<UserTeamAssociation (%r, %r)>' % (self.user_id, self.team_id)

    def to_dict(self, with_user=False, with_team=False, with_advanced_fields=False):
        d = dict(user_id=self.user_id, team_id=self.team_id,
                 is_creator=self.is_creator, is_user_agreed=self.is_user_agreed,
                 is_creator_agreed=self.is_creator_agreed)
        if with_user:
            d['user'] = self.user.to_dict()
        if with_team:
            d['team'] = self.team.to_dict()
        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)

    type = db.Column(db.String(32), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)

    open_time = db.Column(db.DateTime)
    due_time = db.Column(db.DateTime)

    is_team_task = db.Column(db.Boolean, nullable=False, default=False)
    team_min_size = db.Column(db.Integer)
    team_max_size = db.Column(db.Integer)

    submission_limit = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    materials = db.relationship('Material', backref=db.backref('task'))
    file_requirements = db.relationship('FileRequirement', backref=db.backref('task'))
    submissions = db.relationship('Submission', backref=db.backref('task'))

    def __repr__(self):
        return '<Task %r>' % self.title

    def to_dict(self, with_materials=True, with_file_requirements=True, with_advanced_fields=False):
        d = dict(id=self.id, term_id=self.term_id, type=self.type, title=self.title,
                 description=self.description, open_time=self.open_time, due_time=self.due_time,
                 is_team_task=self.is_team_task, team_min_size=self.team_min_size, team_max_size=self.team_max_size,
                 submission_limit=self.submission_limit)
        if with_materials:
            d['materials'] = [m.to_dict() for m in self.materials]
        if with_file_requirements:
            d['file_requirements'] = [f.to_dict() for f in self.file_requirements]
        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)

    type = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256))
    file = db.Column(db.String(128), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<Material %r>' % self.name

    def to_dict(self, with_advanced_fields=False):
        d = dict(id=self.id, task_id=self.task_id, type=self.type, name=self.name, description=self.description,
                 file=self.file)
        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
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

    def to_dict(self, with_advanced_fields=False):
        d = dict(id=self.id, task_id=self.task_id, name=self.name, description=self.description,
                 is_optional=self.is_optional, size_limit=self.size_limit)
        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at

        return d


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)

    submitter_id = db.Column(db.Integer, db.ForeignKey('user_alias.id'))
    submitter_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    files = db.relationship('SubmissionFile', backref=db.backref('submission'))

    def __repr__(self):
        return '<Submission %r>' % self.id

    def to_dict(self, with_advanced_fields=False):
        d = dict(id=self.id, task_id=self.task_id, submitter_id=self.submitter_id,
                 submitter_team_id=self.submitter_team_id)
        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d


class SubmissionFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)
    requirement_id = db.Column(db.Integer, db.ForeignKey('file_requirement.id'), nullable=False)

    file = db.Column(db.String(128))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirement = db.relationship('FileRequirement', backref=db.backref('submission_files'))

    def __repr__(self):
        return '<SubmissionFile %r>' % self.id

    def to_dict(self, with_advanced_fields=False):
        d = dict(id=self.id, submission_id=self.submission_id, requirement_id=self.requirement_id, )
        if with_advanced_fields:
            d['created_at'] = self.created_at
            d['modified_at'] = self.modified_at
        return d
