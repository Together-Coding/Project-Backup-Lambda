import os
from typing import Any

import yaml


def load_configs() -> dict:
    with open("configs.yml", "rt") as fp:
        configs = yaml.load(fp.read(), Loader=yaml.FullLoader)

    return configs["application"].copy()


def get_value(key: str, type_: type = str) -> Any:
    return type_(app_configs.get(key))


# Load configs
app_configs: dict = load_configs()

# AWS
AWS_REGION = get_value("AWS_REGION")
SQS_NAME = get_value("SQS_NAME")
S3_BUCKET = get_value("S3_BUCKET")

# Etc
TIME_LIMIT = get_value("TIME_LIMIT", int)
SQLALCHEMY_DATABASE_URI = get_value("SQLALCHEMY_DATABASE_URI")
REDIS_URL = get_value("REDIS_URL")
REDIS_DB = get_value("REDIS_DB")

# User's file list - ZSET: enc(filename): size
REDIS_KEY_USER_FILE_LIST = "crs:{course_id}:{lesson_id}:{ptc_id}:files"
# User's file contents - STRING(binary): hash(enc(filename)): content
REDIS_KEY_USER_FILE_CONTENT = "crs:{course_id}:{lesson_id}:{ptc_id}:files:{hash}"  
