from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sections = db.relationship("ProfileSection", backref="user", cascade="all, delete-orphan")
    versions = db.relationship(
        "ResumeVersion", backref="user", cascade="all, delete-orphan",
        order_by="ResumeVersion.version_no.desc()",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ProfileSection(db.Model):
    """One row per (user, section). `data` holds the section's JSON content."""

    __tablename__ = "profile_sections"
    __table_args__ = (db.UniqueConstraint("user_id", "section", name="uq_user_section"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    section = db.Column(db.String(50), nullable=False)
    data = db.Column(db.JSON, nullable=False, default=dict)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ResumeVersion(db.Model):
    """Metadata for each generated resume. The PDF itself lives in S3."""

    __tablename__ = "resume_versions"
    __table_args__ = (db.UniqueConstraint("user_id", "version_no", name="uq_user_version"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    version_no = db.Column(db.Integer, nullable=False)
    template = db.Column(db.String(50), nullable=False)
    storage_key = db.Column(db.String(500), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
