#!/usr/bin/env python3
"""Create S3 bucket using environment variables (useful for MinIO local).

Usage:
  python scripts/create_bucket.py

Reads S3_ENDPOINT, S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY from env.
"""
import os
import sys
import boto3


def main():
    endpoint = os.environ.get("S3_ENDPOINT")
    bucket = os.environ.get("S3_BUCKET")
    access = os.environ.get("AWS_ACCESS_KEY_ID")
    secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
    region = os.environ.get("S3_REGION")

    if not bucket:
        print("S3_BUCKET not set in environment", file=sys.stderr)
        sys.exit(2)

    client_args = {}
    if endpoint:
        client_args["endpoint_url"] = endpoint
    if region:
        client_args["region_name"] = region

    if access and secret:
        s3 = boto3.client("s3", aws_access_key_id=access, aws_secret_access_key=secret, **client_args)
    else:
        s3 = boto3.client("s3", **client_args)

    try:
        s3.create_bucket(Bucket=bucket)
        print(f"Created bucket {bucket}")
    except Exception as e:
        # ignore already exists or other errors
        print(f"Could not create bucket: {e}")


if __name__ == "__main__":
    main()
