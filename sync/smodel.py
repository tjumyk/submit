from typing import List


class SubmissionFileData:
    def __init__(self,
                 requirement_name: str,
                 path: str,
                 content: str,
                 size: int,
                 md5: str,
                 created_at: str,
                 modified_at: str):
        self.requirement_name = requirement_name
        self.path = path
        self.content = content
        self.size = size
        self.md5 = md5
        self.created_at = created_at
        self.modified_at = modified_at

    def to_dict(self) -> dict:
        return dict(self.__dict__)

    @staticmethod
    def from_dict(data: dict):
        return SubmissionFileData(**data)


class AutoTestOutputFileData:
    def __init__(self, path: str, content: str,
                 created_at: str, modified_at: str):
        self.path = path
        self.content = content
        self.created_at = created_at
        self.modified_at = modified_at

    def to_dict(self) -> dict:
        return dict(self.__dict__)

    @staticmethod
    def from_dict(data: dict):
        return AutoTestOutputFileData(**data)


class AutoTestData:
    def __init__(self,
                 config_name: str,
                 work_id: str,
                 hostname: str,
                 pid: int,
                 final_state: str,
                 result: str,
                 exception_class: str,
                 exception_message: str,
                 exception_traceback: str,
                 created_at: str,
                 modified_at: str,
                 started_at: str,
                 stopped_at: str,
                 output_files: List[AutoTestOutputFileData]):
        self.config_name = config_name
        self.work_id = work_id
        self.hostname = hostname
        self.pid = pid
        self.final_state = final_state
        self.result = result
        self.exception_class = exception_class
        self.exception_message = exception_message
        self.exception_traceback = exception_traceback
        self.created_at = created_at
        self.modified_at = modified_at
        self.started_at = started_at
        self.stopped_at = stopped_at
        self.output_files = output_files

    def to_dict(self) -> dict:
        d = {}
        for k, v in self.__dict__.items():
            if k == 'output_files':
                v = [f.to_dict() for f in self.output_files]
            d[k] = v
        return d

    @staticmethod
    def from_dict(data: dict):
        _data = dict(data)
        output_files = _data.pop('output_files')
        return AutoTestData(output_files=[AutoTestOutputFileData.from_dict(f) for f in output_files], **_data)


class SubmissionData:
    def __init__(self,
                 submitter_name: str,
                 is_cleared: bool,
                 created_at: str,
                 modified_at: str,
                 files: List[SubmissionFileData],
                 auto_tests: List[AutoTestData]):
        self.submitter_name = submitter_name
        self.is_cleared = is_cleared
        self.created_at = created_at
        self.modified_at = modified_at
        self.files = files
        self.auto_tests = auto_tests

    def to_dict(self) -> dict:
        d = {}
        for k, v in self.__dict__.items():
            if k == 'files' or k == 'auto_tests':
                v = [f.to_dict() for f in v]
            d[k] = v
        return d

    @staticmethod
    def from_dict(data: dict):
        _data = dict(data)
        files = _data.pop('files')
        auto_tests = _data.pop('auto_tests')
        return SubmissionData(files=[SubmissionFileData.from_dict(f) for f in files],
                              auto_tests=[AutoTestData.from_dict(t) for t in auto_tests],
                              **_data)
