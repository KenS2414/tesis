import os
import sys
import socket
import subprocess
import time
import uuid

# ensure repo root is importable when pytest changes cwd
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import boto3
from botocore.config import Config as BConfig
import pytest

from app import create_app
from utils.aws import upload_bytes_to_s3, get_presigned_url


flask_app = create_app()
MINIO_IMAGE = "minio/minio:RELEASE.2024-12-13T22-19-12Z"


def _find_free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.mark.integration
def test_minio_e2e_upload_and_presign():
    # Skip if docker CLI not available in the environment
    try:
        subprocess.run(["docker", "version"], check=True, stdout=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.skip("docker CLI not available, skipping MinIO E2E test")

    port = _find_free_port()
    root_user = "testuser"
    root_pass = "testpass"
    container_id = None
    client = None
    key = "test-object.txt"
    bucket_name = f"resis-test-{uuid.uuid4().hex[:8]}"

    try:
        # Start MinIO container
        cmd = [
            "docker",
            "run",
            "-d",
            "--rm",
            "-p",
            f"{port}:9000",
            "-e",
            f"MINIO_ROOT_USER={root_user}",
            "-e",
            f"MINIO_ROOT_PASSWORD={root_pass}",
            MINIO_IMAGE,
            "server",
            "/data",
        ]
        proc = subprocess.run(cmd, check=True, stdout=subprocess.PIPE)
        container_id = proc.stdout.decode().strip()

        # Wait until MinIO is ready (simple retry loop)
        endpoint = f"http://127.0.0.1:{port}"
        cfg = BConfig(signature_version="s3v4")
        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=root_user,
            aws_secret_access_key=root_pass,
            config=cfg,
            region_name="us-east-1",
        )

        ready = False
        for _ in range(30):
            try:
                client.list_buckets()
                ready = True
                break
            except Exception:
                time.sleep(1)

        assert ready, "MinIO did not become ready in time"

        # Create bucket
        client.create_bucket(Bucket=bucket_name)

        # Configure app to use this MinIO bucket and perform upload + presign inside app context
        old_ak = os.environ.get("AWS_ACCESS_KEY_ID")
        old_sk = os.environ.get("AWS_SECRET_ACCESS_KEY")
        os.environ["AWS_ACCESS_KEY_ID"] = root_user
        os.environ["AWS_SECRET_ACCESS_KEY"] = root_pass
        try:
            with flask_app.app_context():
                flask_app.config["S3_BUCKET"] = bucket_name
                flask_app.config["S3_ENDPOINT"] = endpoint
                flask_app.config["S3_REGION"] = "us-east-1"

                # Upload via the app helper
                upload_bytes_to_s3(b"hello-minio", key, content_type="text/plain")

                # Verify presigned URL is returned and looks OK (call inside app context)
                url = get_presigned_url(key, expires_in=60)
                assert url and url.startswith("http")

            # Verify object exists in MinIO
            obj = client.get_object(Bucket=bucket_name, Key=key)
            body = obj["Body"].read()
            assert body == b"hello-minio"
        finally:
            # restore env
            if old_ak is None:
                os.environ.pop("AWS_ACCESS_KEY_ID", None)
            else:
                os.environ["AWS_ACCESS_KEY_ID"] = old_ak
            if old_sk is None:
                os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
            else:
                os.environ["AWS_SECRET_ACCESS_KEY"] = old_sk

    finally:
        # Cleanup: delete object and bucket if possible
        if client is not None:
            try:
                client.delete_object(Bucket=bucket_name, Key=key)
            except Exception:
                pass
            try:
                client.delete_bucket(Bucket=bucket_name)
            except Exception:
                pass
        # Stop and remove the container
        if container_id:
            try:
                subprocess.run(["docker", "rm", "-f", container_id], check=False)
            except Exception:
                pass
