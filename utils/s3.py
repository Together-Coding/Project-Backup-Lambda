from io import IOBase
from typing import Optional

import boto3
from botocore.errorfactory import ClientError

from configs import S3_BUCKET, AWS_REGION

_s3 = boto3.client("s3", region_name=AWS_REGION)


def _refine_key(key: str) -> str:
    """Refine S3 object key; as the leading slash(/) is treated as filename,
    it should be removed.

    Args:
        key (str): S3 object key

    Returns:
        str: Refined S3 object key
    """

    return key.strip("/")


def put_object(body: IOBase, key: str, bucket: Optional[str] = None, acl="private"):
    if not bucket:
        bucket = S3_BUCKET

    body.seek(0)
    return _s3.put_object(
        Bucket=bucket,
        Key=_refine_key(key),
        ACL=acl,
        Body=body.read(),
    )
