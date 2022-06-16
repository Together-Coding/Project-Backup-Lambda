import os
import hashlib
import base64
from urllib.parse import unquote
from typing import Union
import tempfile
import zipfile

from redis import StrictRedis
from utils.db import UserProject
from utils.s3 import put_object
from configs import REDIS_URL, REDIS_DB, REDIS_KEY_USER_FILE_CONTENT, REDIS_KEY_USER_FILE_LIST

r = StrictRedis.from_url(
    REDIS_URL,
    db=REDIS_DB,
    decode_responses=True,
)


def text_decode(v: Union[str, bytes]) -> str:
    if type(v) == str:
        return unquote(base64.b64decode(v.encode()))
    elif type(v) == bytes:
        return unquote(base64.b64decode(v))

    raise TypeError("`v` must be str or bytes type.")


def get_hashed(name: Union[str, bytes]) -> str:
    if type(name) == str:
        name = name.encode()

    _md5 = hashlib.md5()
    _md5.update(name)
    return _md5.hexdigest()


def project_to_s3(course_id: int, lesson_id: int, proj: UserProject):
    """
    1. Download code from Redis
        1) Get file list
        2) Get file contents
    2. Compress into zip
        1) Write file contents info temp directory
        2) Zip temp directory
    3. Upload to S3
    4. Delete from Redis
    """

    # Get file list
    ptc_id = proj.participant_id

    list_key = REDIS_KEY_USER_FILE_LIST.format(course_id=course_id, lesson_id=lesson_id, ptc_id=ptc_id)
    file_key_func = lambda hash: REDIS_KEY_USER_FILE_CONTENT.format(
        course_id=course_id, lesson_id=lesson_id, ptc_id=ptc_id, hash=hash
    )

    data = r.zscan_iter(list_key, score_cast_func=int)
    enc_filenames = [filename for filename, _ in data]  # remove score values

    with tempfile.TemporaryDirectory() as tmpdirname:
        for enc_filename in enc_filenames:
            try:
                # Get file contents
                filename = text_decode(enc_filename)
                contents = r.get(file_key_func(get_hashed(enc_filename)))
            except UnicodeDecodeError:  # Does not support binary files :(
                continue

            if not filename:
                continue

            # Write file contents info temp directory
            filedir = os.path.dirname(filename)
            for _ in range(2):
                try:
                    with open(os.path.join(tmpdirname, filename), "wt") as fp:
                        fp.write(contents)
                    break
                except (FileNotFoundError, FileExistsError):
                    if not os.path.exists(os.path.join(tmpdirname, filename)):
                        os.makedirs(os.path.join(tmpdirname, filedir))

        # Zip temp directory
        zip_filename = f"{ptc_id}.zip"
        zip_path = os.path.join(tmpdirname, zip_filename)
        with zipfile.ZipFile(zip_path, "w") as zip:
            for dirname, subdirs, files in os.walk(tmpdirname):
                for filename in files:
                    if filename == zip_filename:
                        continue
                    zip.write(os.path.join(dirname, filename), filename)

        # Upload to S3
        s3_key = f"course/{course_id}/{lesson_id}/project/{ptc_id}.zip"
        with open(zip_path, "rb") as fp:
            put_object(body=fp, key=s3_key)
            print(f"Backup for project {proj.id} is done (lesson:{course_id}-{lesson_id} ptc:{ptc_id})")

    # Remove from redis
    for enc_filename in enc_filenames:
        try:
            # Delete file contents
            r.delete(file_key_func(get_hashed(enc_filename)))
        except:
            continue

    # Delete file list
    r.zremrangebyscore(list_key, '-inf', '+inf')
    print(f"Remove project {proj.id} from Redis")