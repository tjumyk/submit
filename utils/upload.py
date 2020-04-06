import hashlib
import os
from uuid import uuid4

from PIL import Image
from flask import current_app as app, send_from_directory

from error import BasicError


class UploadError(BasicError):
    pass


_cache_timeout = 365 * 24 * 60 * 60  # 1 year


def get_upload(path):
    return send_from_directory(app.config['UPLOAD']['root_folder'], path, cache_timeout=_cache_timeout)


def init_app(app):
    app.add_url_rule('/upload/<path:path>', None, get_upload)


def handle_upload(file, _type, image_check=False, image_check_squared=False):
    cfg = app.config['UPLOAD']
    upload_config = cfg[_type]
    name = os.path.basename(file.filename)
    _, ext = os.path.splitext(name)
    if ext:
        ext = ext[1:]  # remove dot
        ext = ext.lower()  # normalize to lower case
    if ext not in upload_config['accept_ext']:
        raise UploadError('invalid file extension')

    upload_root = cfg['root_folder']
    sub_folder = _type
    save_folder = os.path.join(upload_root, sub_folder)
    if not os.path.isdir(save_folder):
        os.makedirs(save_folder)

    save_file = None
    save_path = None
    for _ in range(5):
        _file = "%s.%s" % (str(uuid4()), ext)
        _path = os.path.join(save_folder, _file)
        if not os.path.lexists(_path):
            save_file = _file
            save_path = _path
            break
    if save_file is None:
        raise UploadError('file name space almost exhausted')
    file.save(save_path)

    if os.stat(save_path).st_size > upload_config['size_limit']:
        os.unlink(save_path)
        raise UploadError('file size too big')

    if image_check:
        try:
            with Image.open(save_path) as im:
                image_size = im.size
        except IOError:
            os.unlink(save_path)
            raise UploadError('invalid image file')
        if image_check_squared:
            if image_size[0] != image_size[1]:
                os.unlink(save_path)
                raise UploadError('image is not squared')

    url = '/'.join(['upload', sub_folder, save_file])
    return url


def handle_post_upload(old_url, _type):
    if not old_url:
        return
    parts = old_url.split('/')
    if len(parts) != 3:
        return
    root, sub_folder, file = parts
    if root != 'upload' or sub_folder != _type:
        return

    upload_root = app.config['UPLOAD']['root_folder']
    old_path = os.path.join(upload_root, sub_folder, file)
    if os.path.isfile(old_path):
        os.unlink(old_path)


def md5sum(file_path, block_size=65536):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        block = f.read(block_size)
        while block:
            md5.update(block)
            block = f.read(block_size)
        return md5.hexdigest()
