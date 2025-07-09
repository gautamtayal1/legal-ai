import os
import uuid
from typing import Tuple

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

def _get_s3_client():
    """Create and cache an S3 client"""
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def upload_file(file_bytes: bytes, filename: str) -> Tuple[str, str]:
    """Upload file bytes to S3.

    Returns
    -------
    key: str
        The object key used in S3.
    url: str
        The accessible URL to the object.
    """
    s3 = _get_s3_client()
    # Create unique key
    unique_key = f"uploads/{uuid.uuid4()}_{filename}"
    try:
        s3.put_object(Bucket=S3_BUCKET, Key=unique_key, Body=file_bytes)
    except ClientError as e:
        raise RuntimeError(f"Failed to upload to S3: {e}") from e

    url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{unique_key}"
    return unique_key, url 