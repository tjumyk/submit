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
    _pre_submission_name = 'pre-submission.tar'
    _log_name = 'log'
    _numbered_submission_name_pattern = re.compile(r'^sub(\d+).tar$')

    def __init__(self, required_file_names: Iterable[str],
                 pre_submission_fallback: bool = True,
                 skip_overwritten: bool = True):
        self.required_file_names = set(required_file_names)
        self.pre_submission_fallback = pre_submission_fallback
        self.skip_overwritten = skip_overwritten

    def _scan_submission_tars(self, folder_path: str) -> list:
        folder_files = os.listdir(folder_path)
        if not folder_files:  # empty folder
            return []

        if len(folder_files) == 1 and folder_files[0] == self._pre_submission_name and self.pre_submission_fallback:
            _time = datetime.utcfromtimestamp(os.stat(os.path.join(folder_path, self._pre_submission_name)).st_mtime)
            print('[Waring] Fallback to use pre-submission in %s' % folder_path, file=sys.stderr)
            return [(self._pre_submission_name, _time)]

        if self._log_name not in folder_files:
            raise GiveImporterError('no log file in student folder: %s' % folder_path)

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

        if not self.skip_overwritten:
            for entry in log.entries[0: -len(numbered_files) - 1]:
                # keep an item in the returned list but set file name as None to indicate that it has been overwritten
                tars.append((None, entry.time))
        for entry in log.entries[-len(numbered_files) - 1: -1]:
            file = numbered_files.get(entry.number)
            tars.append((file, entry.time))
        if default_file:
            tars.append((self._default_submission_name, log.entries[-1].time))
        return tars

    def _import_student_folder(self, student_id: str, folder_path: str) -> list:
        all_extracted = []
        for file_name, time in self._scan_submission_tars(folder_path):
            if file_name is None:  # submission tar has been overwritten
                all_extracted.append((time, None))  # pass 'None' to the output
                continue

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

        # find the "root" folder, which contains a list of student folders, by locating any default submission file
        root = None
        for dir_path, dir_names, file_names in os.walk(extract_dir):
            if self._default_submission_name in file_names:
                root, _ = os.path.split(dir_path)
                break
        if root is None:
            raise GiveImporterError('failed to find a submission')
        dir_list = os.listdir(root)

        for name in sorted(dir_list):
            if name.startswith('.') or name == '__MACOSX':
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
