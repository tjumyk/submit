from typing import Optional, List

from error import BasicError
from models import Task, db


class TaskServiceError(BasicError):
    pass


class TaskService:
    title_max_length = 128

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
