import re
from typing import Optional, List

from dateutil import parser
from sqlalchemy import func

from error import BasicError
from models import Task, db, Material, FileRequirement, SpecialConsideration, UserAlias, Team


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
        'evaluation_method',
        'auto_test_trigger',
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
    def add_material(cls, task, _type, name, description, file_path):
        if task is None:
            raise TaskServiceError('task is required')
        if not _type:
            raise TaskServiceError('type is required')
        if not name:
            raise TaskServiceError('name is required')
        if not file_path:
            raise TaskServiceError('file path is required')

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
        mat = Material(task=task, type=_type, name=name, description=description, file_path=file_path)
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
    def get_file_requirement(_id):
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
