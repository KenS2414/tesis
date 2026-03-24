import os
import sys
import io
import boto3
import pytest

# ensure project root is on sys.path for imports when pytest runs from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from extensions import db as _db
from utils.aws import get_presigned_url
import init_db


app = create_app()


@pytest.fixture
def s3_test_env(tmp_path, monkeypatch):
    # set minimal env for app and S3
    monkeypatch.setenv("SECRET_KEY", "test-secret-123")
    monkeypatch.setenv("ADMIN_PASSWORD", "adminpass123")
    monkeypatch.setenv("S3_BUCKET", "test-bucket")
    # ensure app uses S3 for uploads during this test
    app.config["S3_BUCKET"] = "test-bucket"
    # ensure clean DB (use absolute path)
    db_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.db"))
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass
    # ensure SQLAlchemy metadata is clean in-process as well
    with app.app_context():
        try:
            _db.drop_all()
        except Exception:
            pass
        _db.create_all()
    # initialize admin user
    init_db.init_db(app)
    # disable CSRF for tests
    app.config["WTF_CSRF_ENABLED"] = False

    # do not push app context here; will be pushed in the test to avoid interfering with test_client session handling
    # Provide a fake S3 client via monkeypatch to avoid external dependencies
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

    fake_s3 = FakeS3()
    monkeypatch.setattr(boto3, "client", lambda *a, **k: fake_s3)
    yield
    # cleanup
    try:
        os.remove(db_file)
    except OSError:
        pass


def test_upload_to_s3_and_presigned_url(s3_test_env):
    # fake boto3.client was already monkeypatched by fixture
    s3 = boto3.client("s3")

    client = app.test_client()
    # push app context so models and db.session work and to match other tests
    ctx = app.app_context()
    ctx.push()
    # Use context manager so session cookies persist correctly for the whole flow
    with client:
        # Register a student user
        client.get("/register")
        resp = client.post(
            "/register",
            data={
                "username": "s3student@example.com",
                "password": "pass1234",
                "first_name": "S3",
                "last_name": "Student",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # ensure we are logged in (explicit login to guarantee session)
        resp_login = client.post(
            "/login",
            data={"username": "s3student@example.com", "password": "pass1234"},
            follow_redirects=True,
        )
        assert resp_login.status_code == 200

        # Prepare a valid tiny PNG using Pillow
        from PIL import Image

        img_buf = io.BytesIO()
        img = Image.new("RGB", (1, 1), color=(255, 255, 255))
        img.save(img_buf, format="PNG")
        img_buf.seek(0)
        png_bytes = img_buf.getvalue()

        # Submit a payment with file
        data = {
            "amount": "20.00",
            "proof": (io.BytesIO(png_bytes), "receipt.png", "image/png"),
        }
        client.get("/payments/new")
        resp = client.post(
            "/payments/new",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert resp.status_code == 200
    # leave app context open for DB assertions; will pop after checks

    # Verify payment stored and proof_filename present
    from models import Student, Payment

    student = Student.query.filter_by(email="s3student@example.com").first()
    if student is None:
        # helpful debug output when test fails
        all_students = Student.query.all()
        raise AssertionError(
            f"Expected student created but none found. All students: {all_students}"
        )
    assert student is not None
    payment = (
        Payment.query.filter_by(student_id=student.id)
        .order_by(Payment.id.desc())
        .first()
    )
    assert payment is not None
    assert payment.proof_filename is not None

    # Verify object exists in fake S3
    obj = s3.get_object(Bucket="test-bucket", Key=payment.proof_filename)
    body = obj["Body"].read()
    assert body.startswith(b"\x89PNG")

    # Presigned URL should be generated
    url = get_presigned_url(payment.proof_filename)
    assert url is not None and url.startswith("https://")
    # pop app context now
    ctx.pop()