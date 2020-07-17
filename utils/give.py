import os
import re
import shutil
import sys
from datetime import datetime
from tarfile import TarFile
from typing import Iterable, List

from dateutil import tz

from error import BasicError

_tz_local = tz.tzlocal()
_tz_utc = tz.tzutc()


class GiveImporterError(BasicError):
    pass


class GiveLogEntry:
    def __init__(self, number: int, time: datetime):
        self.number = number
        self.time = time

    def __repr__(self):
        return '<GiveLogEntry %d %r>' % (self.number, self.time)


class GiveLog:
    def __init__(self, entries: List[GiveLogEntry]):
        self.entries = entries

    @staticmethod
    def parse(log_path: str):
        with open(log_path) as f:
            entries = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                s_num, timestamp, others = line.split('\t', 2)
                num = int(s_num.split()[-1])
                local_time = datetime.strptime(timestamp, '%a %b %d %H:%M:%S %Y')
                utc_time = local_time.replace(tzinfo=_tz_local).astimezone(_tz_utc).replace(tzinfo=None)
                entries.append(GiveLogEntry(num, utc_time))
            return GiveLog(entries)


class GiveImporter:
    _default_submission_name = 'submission.tar'
    _log_name = 'log'
    _numbered_submission_name_pattern = re.compile(r'^sub(\d+).tar$')

    def __init__(self, required_file_names: Iterable[str]):
        self.required_file_names = set(required_file_names)

    def _import_student_folder(self, student_id: str, folder_path: str) -> list:
        folder_files = os.listdir(folder_path)
        if not folder_files:  # empty folder
            return []

        tars = []
        log = GiveLog.parse(os.path.join(folder_path, self._log_name))
        default_file = None
        numbered_files = {}
        for file_name in folder_files:
            if file_name == self._default_submission_name:
                default_file = file_name
            else:
                match = self._numbered_submission_name_pattern.match(file_name)
                if match:
                    numbered_files[int(match.group(1))] = file_name

        for entry in log.entries[-len(numbered_files) - 1: -1]:
            file = numbered_files.get(entry.number)
            tars.append((file, entry.time))
        if default_file:
            tars.append((self._default_submission_name, log.entries[-1].time))

        all_extracted = []
        for file_name, time in tars:
            extract_dir = os.path.join(folder_path, '%s_extracted' % file_name)
            if os.path.exists(extract_dir):
                raise GiveImporterError('extract folder for tar already exists')
            os.mkdir(extract_dir)

            extracted = {}
            try:
                with TarFile.open(os.path.join(folder_path, file_name)) as f_tar:
                    for member in f_tar.getmembers():
                        member_name = member.name
                        if member_name in self.required_file_names:
                            f_tar.extract(member, extract_dir, set_attrs=False)
                            extracted[member_name] = os.path.join(extract_dir, member_name)
            except IOError as e:
                print('[Waring] Failed to extract files in tar "%s" for %s: %s' % (file_name, student_id, str(e)),
                      file=sys.stderr)
            all_extracted.append((time, extracted))
        return all_extracted

    def import_archive(self, archive_path: str, extract_dir: str):
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)
        if os.listdir(extract_dir):
            raise GiveImporterError('extract dir is not empty')

        try:
            shutil.unpack_archive(archive_path, extract_dir)
        except IOError as e:
            raise GiveImporterError('failed to unpack archive', str(e)) from e

        root = extract_dir
        dir_list = os.listdir(root)
        if len(dir_list) == 1:
            child = os.path.join(root, dir_list[0])
            if os.path.isdir(child):  # there is a wrapper folder
                root = child
                dir_list = os.listdir(root)

        for name in sorted(dir_list):
            if name.startswith('.'):
                continue
            path = os.path.join(root, name)
            if not os.path.isdir(path):
                raise GiveImporterError('unexpected file: %s' % name)
            student_id = name
            if student_id[0] != 'z':
                student_id = 'z' + student_id
            yield student_id, self._import_student_folder(student_id, path)


def _test():
    import tempfile

    with tempfile.TemporaryDirectory() as work_dir:
        for result in GiveImporter(['ass1.pdf']).import_archive('/home/kelvin/Documents/all_submissions.zip', work_dir):
            print(result)


if __name__ == '__main__':
    _test()
