
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set in the environment")

    # Database: SQLite locally, PostgreSQL or MySQL on AWS RDS
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "resume_builder.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # S3 storage; local disk is used when S3_BUCKET is empty
    S3_BUCKET = os.environ.get("S3_BUCKET", "")
    AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
    S3_PRESIGN_EXPIRY = int(os.environ.get("S3_PRESIGN_EXPIRY", "300"))

    LOCAL_STORAGE_DIR = os.environ.get(
        "LOCAL_STORAGE_DIR",
        os.path.join(BASE_DIR, "local_storage"),
    )

    WTF_CSRF_TIME_LIMIT = None

