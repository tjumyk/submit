import re
from typing import Optional, List

from dateutil import parser
from sqlalchemy import func

from error import BasicError
from models import Task, db, Material, FileRequirement, SpecialConsideration, UserAlias, Team, user_groups_alias, Term, \
    Submission, UserTeamAssociation, AutoTestConfig


class TaskServiceError(BasicError):
    pass


class TaskService:
    title_max_length = 128

    file_name_pattern = re.compile('^[^\s?#/\\\\|()&]+$')

    material_type_max_length = 32
    material_name_max_length = 128
    material_description_max_length = 256
    material_file_path_max_length = 128

    file_requirement_name_max_length = 128
    file_requirement_description_max_length = 256

    fields = {
        'type',
        'title',
        'description',
        'open_time',
        'due_time',
        'close_time',
        'late_penalty',
        'is_team_task',
        'team_min_size',
        'team_max_size',
        'team_join_close_time',
        'submission_attempt_limit',
        'submission_history_limit',
        'evaluation_method'
    }

    auto_test_config_fields = {
        'name',
        'type',
        'description',
        'is_enabled',
        'is_private',
        'priority',
        'trigger',
        'docker_auto_remove',
        'docker_cpus',
        'docker_memory',
        'docker_network',
        'result_render_html',
        'result_conclusion_type',
        'result_conclusion_path',
        'result_conclusion_full_marks',
        'result_conclusion_apply_late_penalty',
        'results_conclusion_accumulate_method',
    }

    @staticmethod
    def get(_id) -> Optional[Task]:
        if _id is None:
            raise TaskServiceError('id is required')
        if type(_id) is not int:
            raise TaskServiceError('id must be an integer')

        return Task.query.get(_id)

    @staticmethod
    def get_all() -> List[Task]:
        return Task.query.all()

    @staticmethod
    def add(term, _type, title, description) -> Task:
        if term is None:
            raise TaskServiceError('term is required')
        if _type is None:
            raise TaskServiceError('type is required')
        if title is None:
            raise TaskServiceError('title is required')

        if len(title) > TaskService.title_max_length:
            raise TaskServiceError('title too long')

        # description of task has no length limit

        task = Task(term=term, type=_type, title=title, description=description)
        db.session.add(task)
        return task

    @classmethod
    def update(cls, task, **kwargs):
        if task is None:
            raise TaskServiceError('task is required')
        for k in kwargs:
            if k not in cls.fields:
                raise TaskServiceError('invalid field', k)
            if k in ['open_time', 'due_time', 'close_time', 'team_join_close_time']:  # fix datetime
                v = kwargs[k]
                if v:
                    kwargs[k] = parser.parse(v).replace(tzinfo=None)  # strip tzinfo from a UTC datetime
                else:
                    kwargs[k] = None
            if k in ['team_min_size', 'team_max_size',
                     'submission_attempt_limit', 'submission_history_limit']:  # validate limit numbers
                v = kwargs[k]
                if v is not None:
                    if type(v) is not int:
                        raise TaskServiceError('invalid value for "%s"' % k, "%r is not an integer" % v)
                    if v < 1:
                        raise TaskServiceError('invalid value for "%s"' % k, "%r is less than 1" % v)

        old = {k: getattr(task, k) for k in kwargs}
        for k, v in kwargs.items():
            setattr(task, k, v)
        return old

    @classmethod
    def add_material(cls, task, _type, name, description, file_path, is_private):
        if task is None:
            raise TaskServiceError('task is required')
        if not _type:
            raise TaskServiceError('type is required')
        if not name:
            raise TaskServiceError('name is required')
        if not file_path:
            raise TaskServiceError('file path is required')
        if is_private is None:
            raise TaskServiceError('is_private is required')

        if len(_type) > cls.material_type_max_length:
            raise TaskServiceError('type is too long')
        if len(name) > cls.material_name_max_length:
            raise TaskServiceError('name is too long')
        if description and len(description) > cls.material_description_max_length:
            raise TaskServiceError('description is too long')
        if len(file_path) > cls.material_file_path_max_length:
            raise TaskServiceError('file path is too long')
        if not cls.file_name_pattern.match(name):
            raise TaskServiceError('invalid name format')

        if db.session.query(func.count()).filter(Material.task_id == task.id,
                                                 Material.name == name).scalar():  # check in task scope
            raise TaskServiceError('duplicate name')
        if db.session.query(func.count()).filter(Material.file_path == file_path).scalar():  # check in global scope
            raise TaskServiceError('duplicate file path')
        mat = Material(task=task, type=_type, name=name, description=description, file_path=file_path,
                       is_private=is_private)
        db.session.add(mat)
        return mat

    @staticmethod
    def get_material(_id):
        if _id is None:
            raise TaskServiceError('id is required')
        if type(_id) is not int:
            raise TaskServiceError('id must be an integer')

        return Material.query.get(_id)

    @classmethod
    def add_auto_test_config(cls, task, **kwargs):
        if task is None:
            raise TaskServiceError('task is required')
        name = kwargs.pop('name', None)
        if not name:
            raise TaskServiceError('name is required')
        _type = kwargs.pop('type', None)
        if not _type:
            raise TaskServiceError('type is required')

        if len(name) > 128:
            raise TaskServiceError('name too long')

        config = AutoTestConfig(task_id=task.id, name=name, type=_type)

        environment = kwargs.pop('environment', None)
        if environment:
            if environment.task_id != task.id:
                raise TaskServiceError('environment material does not belong to this task')
            config.environment_id = environment.id

        file_requirement = kwargs.pop('file_requirement', None)
        if file_requirement:
            if file_requirement.task_id != config.task_id:
                raise TaskServiceError('target file requirement does not belong to this task')
            config.file_requirement_id = file_requirement.id

        template_file = kwargs.pop('template_file', None)
        if template_file:
            if template_file.task_id != task.id:
                raise TaskServiceError('template file material does not belong to this task')
            config.template_file_id = template_file.id

        for k, v in kwargs.items():
            if k not in cls.auto_test_config_fields:
                raise TaskServiceError('invalid field: %s' % k)
            if k == 'description':
                if v and len(v) > 256:
                    raise TaskServiceError('description too long')
            elif k == 'result_conclusion_path':
                if v and len(v) > 128:
                    raise TaskServiceError('result conclusion path too long')
            elif k == 'priority':
                if type(v) is not int:
                    raise TaskServiceError('priority must be an integer')
                if v < 0 or v > 255:
                    raise TaskServiceError('priority must be between 0 and 255')

            setattr(config, k, v)

        cls._check_auto_test_config(config)

        if db.session.query(func.count()).filter(AutoTestConfig.task_id == task.id,
                                                 AutoTestConfig.name == name).scalar():
            raise TaskServiceError('duplicate name')

        db.session.add(config)
        return config

    @classmethod
    def update_auto_test_config(cls, config: AutoTestConfig, **kwargs):
        if config is None:
            raise TaskServiceError('auto test config is required')

        if 'environment' in kwargs:
            environment = kwargs.pop('environment')
            if environment:
                if environment.task_id != config.task_id:
                    raise TaskServiceError('environment material does not belong to this task')
                config.environment_id = environment.id
            else:
                config.environment_id = None

        if 'file_requirement' in kwargs:
            file_requirement = kwargs.pop('file_requirement')
            if file_requirement:
                if file_requirement.task_id != config.task_id:
                    raise TaskServiceError('target file requirement does not belong to this task')
                config.file_requirement_id = file_requirement.id
            else:
                config.file_requirement_id = None

        if 'template_file' in kwargs:
            template_file = kwargs.pop('template_file')
            if template_file:
                if template_file.task_id != config.task_id:
                    raise TaskServiceError('template file material does not belong to this task')
                config.template_file_id = template_file.id
            else:
                config.template_file_id = None

        for k, v in kwargs.items():
            if k not in cls.auto_test_config_fields:
                raise TaskServiceError('invalid field: %s' % k)
            if k == 'name':
                if not v:
                    raise TaskServiceError('name is required')
                if len(v) > 128:
                    raise TaskServiceError('name too long')
            elif k == 'type':
                if not v:
                    raise TaskServiceError('type is required')
            elif k == 'description':
                if v and len(v) > 256:
                    raise TaskServiceError('description too long')
            elif k == 'result_conclusion_path':
                if v and len(v) > 128:
                    raise TaskServiceError('result conclusion path too long')
            elif k == 'priority':
                if type(v) is not int:
                    raise TaskServiceError('priority must be an integer')
                if v < 0 or v > 255:
                    raise TaskServiceError('priority must be between 0 and 255')
            setattr(config, k, v)
        cls._check_auto_test_config(config)

        if db.session.query(func.count()).filter(AutoTestConfig.task_id == config.task_id,
                                                 AutoTestConfig.name == config.name,
                                                 AutoTestConfig.id != config.id).scalar():
            raise TaskServiceError('duplicate name')

        return config

    @staticmethod
    def _check_auto_test_config(config: AutoTestConfig):
        if config.type in {'run-script', 'docker'} and not config.environment_id:
            raise TaskServiceError('no test environment specified')
        if config.type in {'anti-plagiarism', 'file-exists'} and not config.file_requirement_id:
            raise TaskServiceError('no target file requirement specified')

        con_type = config.result_conclusion_type
        acc_method = config.results_conclusion_accumulate_method
        if (con_type in {'int', 'float'} and acc_method not in {'last', 'first', 'highest', 'lowest', 'average'}) or \
                (con_type == 'bool' and acc_method not in {'last', 'first', 'and', 'or'}) or \
                (con_type in {'string', 'json'} and acc_method not in {'last', 'first'}):
            raise TaskServiceError('invalid accumulate method',
                                   'conclusion type: %s, accumulate method: %s' % (con_type, acc_method))

    @staticmethod
    def get_auto_test_config(_id):
        if _id is None:
            raise TaskServiceError('id is required')
        if type(_id) is not int:
            raise TaskServiceError('id must be an integer')

        return AutoTestConfig.query.get(_id)

    @classmethod
    def add_file_requirement(cls, task, name, description, is_optional, size_limit):
        if task is None:
            raise TaskServiceError('task is required')
        if not name:
            raise TaskServiceError('name is required')
        if is_optional is None:
            raise TaskServiceError('is_optional is required')

        if len(name) > cls.file_requirement_name_max_length:
            raise TaskServiceError('name is too long')
        if description and len(description) > cls.file_requirement_description_max_length:
            raise TaskServiceError('description is too long')
        if not cls.file_name_pattern.match(name):
            raise TaskServiceError('invalid name format')

        if db.session.query(func.count()).filter(FileRequirement.task_id == task.id,
                                                 FileRequirement.name == name).scalar():
            raise TaskServiceError('duplicate name')

        req = FileRequirement(task=task, name=name, description=description, is_optional=is_optional,
                              size_limit=size_limit)
        db.session.add(req)
        return req

    @staticmethod
    def get_file_requirement(_id) -> Optional[FileRequirement]:
        if _id is None:
            raise TaskServiceError('id is required')
        if type(_id) is not int:
            raise TaskServiceError('id must be an integer')

        return FileRequirement.query.get(_id)

    @staticmethod
    def get_special_consideration(_id) -> Optional[SpecialConsideration]:
        if _id is None:
            raise TaskServiceError('id is required')
        if type(_id) is not int:
            raise TaskServiceError('id must be an integer')

        return SpecialConsideration.query.get(_id)

    @staticmethod
    def get_special_considerations_for_task(task: Task) -> List[SpecialConsideration]:
        if task is None:
            raise TaskServiceError('task is required')

        return SpecialConsideration.query.with_parent(task).all()

    @staticmethod
    def get_special_consideration_for_task_user(task: Task, user: UserAlias) -> Optional[SpecialConsideration]:
        if task is None:
            raise TaskServiceError('task is required')
        if user is None:
            raise TaskServiceError('user is required')

        return SpecialConsideration.query.with_parent(user).with_parent(task).first()

    @staticmethod
    def get_special_consideration_for_team(team: Team) -> Optional[SpecialConsideration]:
        if team is None:
            raise TaskServiceError('team is required')

        return SpecialConsideration.query.with_parent(team).first()

    @staticmethod
    def add_special_consideration(task: Task, user: UserAlias, team: Team,
                                  due_time_extension: int, submission_attempt_limit_extension: int) \
            -> SpecialConsideration:
        if task is None:
            raise TaskServiceError('task is required')
        if user is None and team is None:
            raise TaskServiceError('at least one of user and team is required')
        if user is not None and team is not None:
            raise TaskServiceError('only one of user and team is required')
        if due_time_extension is not None:
            if type(due_time_extension) is not int:
                raise TaskServiceError('due time extension must be an integer')
            if due_time_extension <= 0:
                raise TaskServiceError('due time extension must be larger than 0',
                                       'You can leave it blank to specify no extension')
        if submission_attempt_limit_extension is not None:
            if type(submission_attempt_limit_extension) is not int:
                raise TaskServiceError('submission attempt limit extension must be an integer')
            if submission_attempt_limit_extension <= 0:
                raise TaskServiceError('submission attempt limit extension must be larger than 0',
                                       'You can leave it blank to specify no extension')

        if db.session.query(func.count()).filter(SpecialConsideration.task_id == task.id,
                                                 SpecialConsideration.user == user,
                                                 SpecialConsideration.team == team).scalar():
            raise TaskServiceError('special consideration already exists')

        spec = SpecialConsideration(task=task, user=user, team=team, due_time_extension=due_time_extension,
                                    submission_attempt_limit_extension=submission_attempt_limit_extension)
        db.session.add(spec)
        return spec

    @staticmethod
    def get_users_no_submission(task: Task):
        if task is None:
            raise TaskServiceError('task is required')
        if task.is_team_task:
            raise TaskServiceError('only for non-team task')

        q1 = db.session.query(UserAlias) \
            .filter(UserAlias.id == user_groups_alias.c.user_id,
                    user_groups_alias.c.group_id == Term.student_group_id,
                    Term.id == task.term_id)
        q2 = db.session.query(UserAlias) \
            .filter(UserAlias.id == Submission.submitter_id,
                    Submission.task_id == task.id)
        return q1.except_(q2).all()

    @staticmethod
    def get_teams_no_submission(task: Task):
        if task is None:
            raise TaskServiceError('task is required')
        if not task.is_team_task:
            raise TaskServiceError('only for team task')

        q1 = db.session.query(Team) \
            .filter(Team.task_id == task.id)
        q2 = db.session.query(Team) \
            .filter(UserTeamAssociation.team_id == Team.id,
                    UserTeamAssociation.user_id == Submission.submitter_id,
                    Team.task_id == task.id,
                    Submission.task_id == task.id)
        return q1.except_(q2).all()
