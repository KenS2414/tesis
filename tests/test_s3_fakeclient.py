import io
import boto3
import os
import pytest

from app import create_app
from utils.aws import upload_bytes_to_s3, get_presigned_url


app = create_app()


def test_upload_and_presign_with_fake_s3(monkeypatch):
    # configure app for testing
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("S3_BUCKET", "fake-bucket")
    app.config["S3_BUCKET"] = "fake-bucket"

    # Fake S3 client that stores objects in-memory
    class FakeS3:
        def __init__(self):
            self._store = {}

        def put_object(self, Bucket, Key, Body, **kwargs):
            self._store[(Bucket, Key)] = Body

        def get_object(self, Bucket, Key):
            body = self._store.get((Bucket, Key))
            if body is None:
                raise Exception("NoSuchKey")
            return {"Body": io.BytesIO(body)}

        def generate_presigned_url(self, ClientMethod, Params=None, ExpiresIn=None):
            b = Params.get("Bucket")
            k = Params.get("Key")
            return f"https://fake-s3/{b}/{k}"

    fake = FakeS3()
    monkeypatch.setattr(boto3, "client", lambda *a, **k: fake)

    with app.app_context():
        data = b"hello world"
        key = "test/path/file.bin"
        upload_bytes_to_s3(data, key_name=key, content_type="application/octet-stream")

        # ensure object exists via the fake client
        obj = fake.get_object(Bucket="fake-bucket", Key=key)
        assert obj["Body"].read() == data

        url = get_presigned_url(key)
        assert url is not None and url.startswith("https://fake-s3/")
