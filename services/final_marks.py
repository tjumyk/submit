from typing import Optional, List, Iterable, Tuple

from error import BasicError
from models import FinalMarks, db, Task, UserAlias, Term


class FinalMarksServiceError(BasicError):
    pass


class FinalMarksService:
    _MAX_COMMENT_LENGTH = 128

    @staticmethod
    def get(user: UserAlias, task: Task) -> Optional[FinalMarks]:
        if user is None:
            raise FinalMarksServiceError('user is required')
        if task is None:
            raise FinalMarksServiceError('task is required')

        return db.session.query(FinalMarks) \
            .filter(FinalMarks.user_id == user.id,
                    FinalMarks.task_id == task.id) \
            .first()

    @staticmethod
    def get_for_user_term(user: UserAlias, term: Term, include_unreleased: bool = False) -> List[FinalMarks]:
        if user is None:
            raise FinalMarksServiceError('user is required')
        if term is None:
            raise FinalMarksServiceError('term is required')

        filters = [FinalMarks.user_id == user.id,
                   FinalMarks.task_id == Task.id,
                   Task.term_id == term.id]
        if not include_unreleased:
            filters.append(Task.is_final_marks_released == True)
        return db.session.query(FinalMarks) \
            .filter(*filters) \
            .all()

    @staticmethod
    def get_for_task(task: Task) -> List[FinalMarks]:
        if task is None:
            raise FinalMarksServiceError('task is required')

        return db.session.query(FinalMarks) \
            .filter(FinalMarks.task_id == task.id) \
            .all()

    @classmethod
    def set(cls, task: Task, user: UserAlias, marks: float, comment: Optional[str]) -> FinalMarks:
        if task is None:
            raise FinalMarksServiceError('task is required')
        if task.is_final_marks_released:
            raise FinalMarksServiceError('final marks are already released')
        if user is None:
            raise FinalMarksServiceError('user is required')
        if marks is None:
            raise FinalMarksServiceError('marks is required')
        if not isinstance(marks, (float, int)):
            raise FinalMarksServiceError('marks must be a number')
        if comment is not None:
            if not isinstance(comment, str):
                raise FinalMarksServiceError('comment must be a string')
            if len(comment) > cls._MAX_COMMENT_LENGTH:
                raise FinalMarksServiceError('comment is too long')

        student_group_id = task.term.student_group_id
        if not any(g.id == student_group_id for g in user.groups):
            raise FinalMarksServiceError('user is not a student of this term')

        record = db.session.query(FinalMarks) \
            .filter(FinalMarks.user_id == user.id,
                    FinalMarks.task_id == task.id).first()
        if record:
            record.marks = marks
            record.comment = comment
        else:
            record = FinalMarks(user_id=user.id, task_id=task.id, marks=marks, comment=comment)
            db.session.add(record)
        return record

    @classmethod
    def batch_set(cls, task: Task, data: List[Tuple[UserAlias, float, str]]) -> Tuple[
        List[FinalMarks], List[FinalMarks]]:
        if task is None:
            raise FinalMarksServiceError('task is required')
        if task.is_final_marks_released:
            raise FinalMarksServiceError('final marks are already released')

        # check data
        student_group_id = task.term.student_group_id
        data_map = {}
        for i, (user, marks, comment) in enumerate(data):
            if user is None:
                raise FinalMarksServiceError('user is None in row %d' % i)
            if not any(g.id == student_group_id for g in user.groups):
                raise FinalMarksServiceError('user %s is not a student of this term' % user.name)
            if marks is None:
                raise FinalMarksServiceError('marks for user %s is None' % user.name)
            if not isinstance(marks, (float, int)):
                raise FinalMarksServiceError('marks for user %s is not a number' % user.name)
            if comment is not None:
                if not isinstance(comment, str):
                    raise FinalMarksServiceError('comment for user %s is not a string' % user.name)
                if len(comment) > cls._MAX_COMMENT_LENGTH:
                    raise FinalMarksServiceError('comment for user %s is too long' % user.name)
            data_map[user.id] = (marks, comment)
        new_user_ids = set(data_map.keys())

        # find existing records
        updated_records = []
        for record in db.session.query(FinalMarks) \
                .filter(FinalMarks.user_id.in_(data_map.keys()),
                        FinalMarks.task_id == task.id):
            user_id = record.user_id
            marks, comment = data_map[user_id]
            record.marks = marks
            record.comment = comment
            new_user_ids.remove(user_id)
            updated_records.append(record)

        # add new records
        new_records = []
        for user_id in new_user_ids:
            marks, comment = data_map[user_id]
            record = db.session.add(FinalMarks(task_id=task.id, user_id=user_id, marks=marks, comment=comment))
            new_records.append(record)

        return new_records, updated_records

    @staticmethod
    def release(task: Task):
        if task is None:
            raise FinalMarksServiceError('task is required')
        if task.is_final_marks_released:
            raise FinalMarksServiceError('final marks are already released')

        task.is_final_marks_released = True
