import boto3
from flask import current_app
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

def upload_bytes_to_s3(bytes_data, key_name, content_type=None):
    bucket = current_app.config.get("S3_BUCKET")
    if not bucket:
        raise RuntimeError("S3_BUCKET not configured")
    client_args = {}
    region = current_app.config.get("S3_REGION")
    endpoint = current_app.config.get("S3_ENDPOINT")
    if region:
        client_args["region_name"] = region
    if endpoint:
        client_args["endpoint_url"] = endpoint
    s3 = boto3.client("s3", **client_args)
    try:
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        s3.put_object(Bucket=bucket, Key=key_name, Body=bytes_data, **extra_args)
    except (BotoCoreError, NoCredentialsError) as e:
        raise RuntimeError(f"S3 upload failed: {e}")
    return key_name


def get_presigned_url(key_name, expires_in=3600):
    bucket = current_app.config.get("S3_BUCKET")
    if not bucket or not key_name:
        return None
    client_args = {}
    region = current_app.config.get("S3_REGION")
    endpoint = current_app.config.get("S3_ENDPOINT")
    if region:
        client_args["region_name"] = region
    if endpoint:
        client_args["endpoint_url"] = endpoint
    s3 = boto3.client("s3", **client_args)
    try:
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key_name},
            ExpiresIn=expires_in,
        )
    except Exception:
        return None


def check_s3_connection():
    """Checks if S3 bucket is accessible."""
    bucket = current_app.config.get("S3_BUCKET")
    if not bucket:
        return None # Not configured
    client_args = {}
    region = current_app.config.get("S3_REGION")
    endpoint = current_app.config.get("S3_ENDPOINT")
    if region:
        client_args["region_name"] = region
    if endpoint:
        client_args["endpoint_url"] = endpoint
    s3 = boto3.client("s3", **client_args)

    try:
        s3.head_bucket(Bucket=bucket)
        return True
    except (BotoCoreError, ClientError):
        return False
