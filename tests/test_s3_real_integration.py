import os
import sys
import socket
import subprocess
import time
import uuid

import boto3
import pytest

# ensure project root is on sys.path for imports when pytest runs from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from models import Payment, Student
from utils.aws import get_presigned_url, upload_bytes_to_s3


app = create_app()
MINIO_IMAGE = "minio/minio:RELEASE.2024-12-13T22-19-12Z"


def _find_free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.mark.integration
def test_real_postgres_and_minio_payment_artifact_roundtrip():
    try:
        subprocess.run(["docker", "version"], check=True, stdout=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.skip("docker CLI not available, skipping real S3/Postgres integration test")

    bucket = f"resis-integration-{uuid.uuid4().hex[:8]}"
    access_key = "testuser"
    secret_key = "testpass"
    port = _find_free_port()
    endpoint = f"http://127.0.0.1:{port}"
    container_id = None

    object_key = f"integration/{uuid.uuid4().hex}.txt"
    student_email = f"integration-{uuid.uuid4().hex[:8]}@example.com"

    cmd = [
        "docker",
        "run",
        "-d",
        "--rm",
        "-p",
        f"{port}:9000",
        "-e",
        f"MINIO_ROOT_USER={access_key}",
        "-e",
        f"MINIO_ROOT_PASSWORD={secret_key}",
        MINIO_IMAGE,
        "server",
        "/data",
    ]
    proc = subprocess.run(cmd, check=True, stdout=subprocess.PIPE)
    container_id = proc.stdout.decode().strip()

    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1",
    )

    ready = False
    for _ in range(30):
        try:
            s3_client.list_buckets()
            ready = True
            break
        except Exception:
            time.sleep(1)

    assert ready, "MinIO did not become ready in time"
    s3_client.create_bucket(Bucket=bucket)

    old_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    old_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    old_endpoint = os.environ.get("S3_ENDPOINT")
    old_bucket = os.environ.get("S3_BUCKET")

    os.environ["AWS_ACCESS_KEY_ID"] = access_key
    os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key
    os.environ["S3_ENDPOINT"] = endpoint
    os.environ["S3_BUCKET"] = bucket

    try:
        with app.app_context():
            app.config["S3_BUCKET"] = bucket
            app.config["S3_ENDPOINT"] = endpoint
            app.config["S3_REGION"] = "us-east-1"
            db.create_all()

            student = Student(first_name="Integration", last_name="Runtime", email=student_email)
            db.session.add(student)
            db.session.commit()

            upload_bytes_to_s3(b"integration-artifact", object_key, content_type="text/plain")

            payment = Payment(student_id=student.id, amount=25.00, status="pending", proof_filename=object_key)
            db.session.add(payment)
            db.session.commit()

            persisted_payment = db.session.get(Payment, payment.id)
            assert persisted_payment is not None
            assert persisted_payment.proof_filename == object_key

            presigned_url = get_presigned_url(object_key, expires_in=120)
            assert presigned_url is not None
            assert object_key in presigned_url

            obj = s3_client.get_object(Bucket=bucket, Key=object_key)
            assert obj["Body"].read() == b"integration-artifact"

            db.session.delete(persisted_payment)
            db.session.delete(student)
            db.session.commit()

        s3_client.delete_object(Bucket=bucket, Key=object_key)
        s3_client.delete_bucket(Bucket=bucket)
    finally:
        if old_access_key is None:
            os.environ.pop("AWS_ACCESS_KEY_ID", None)
        else:
            os.environ["AWS_ACCESS_KEY_ID"] = old_access_key

        if old_secret_key is None:
            os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
        else:
            os.environ["AWS_SECRET_ACCESS_KEY"] = old_secret_key

        if old_endpoint is None:
            os.environ.pop("S3_ENDPOINT", None)
        else:
            os.environ["S3_ENDPOINT"] = old_endpoint

        if old_bucket is None:
            os.environ.pop("S3_BUCKET", None)
        else:
            os.environ["S3_BUCKET"] = old_bucket

        if container_id:
            subprocess.run(["docker", "rm", "-f", container_id], check=False)