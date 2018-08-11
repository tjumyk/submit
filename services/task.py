import re
from typing import Optional, List

from dateutil import parser, tz

from error import BasicError
from models import Task, db, Material, FileRequirement


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
        'submission_attempt_limit',
        'submission_history_limit'
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
            if k in ['open_time', 'due_time', 'close_time']:  # fix datetime
                v = kwargs[k]
                if v:
                    kwargs[k] = parser.parse(v).replace(tzinfo=tz.tzlocal()).astimezone(tz.tzutc())
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

        if Material.query.filter_by(task=task, name=name).count():  # check in task scope
            raise TaskServiceError('duplicate name')
        if Material.query.filter_by(file_path=file_path).count():  # check in global scope
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

        if FileRequirement.query.filter_by(task=task, name=name).count():
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
