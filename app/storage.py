"""PDF storage: S3 in production, local disk when S3_BUCKET is not set."""
import os

from flask import current_app


def _use_s3():
    return bool(current_app.config["S3_BUCKET"])


def _s3():
    import boto3

    # Credentials come from the EC2 instance role (recommended) or env vars.
    return boto3.client("s3", region_name=current_app.config["AWS_REGION"])


def save_pdf(key, pdf_bytes):
    if _use_s3():
        _s3().put_object(
            Bucket=current_app.config["S3_BUCKET"],
            Key=key,
            Body=pdf_bytes,
            ContentType="application/pdf",
            ServerSideEncryption="AES256",
        )
    else:
        path = os.path.join(current_app.config["LOCAL_STORAGE_DIR"], key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(pdf_bytes)


def download_url(key, filename):
    """Presigned S3 URL, or None when files are stored locally."""
    if not _use_s3():
        return None
    return _s3().generate_presigned_url(
        "get_object",
        Params={
            "Bucket": current_app.config["S3_BUCKET"],
            "Key": key,
            "ResponseContentDisposition": f'attachment; filename="{filename}"',
            "ResponseContentType": "application/pdf",
        },
        ExpiresIn=current_app.config["S3_PRESIGN_EXPIRY"],
    )


def local_path(key):
    return os.path.join(current_app.config["LOCAL_STORAGE_DIR"], key)
