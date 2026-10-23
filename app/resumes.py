import re
from datetime import datetime

from flask import (Blueprint, Response, abort, flash, redirect, render_template, request,
                   send_file, url_for)
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from . import db, storage
from .models import ProfileSection, ResumeVersion
from .pdf import build_context, render_html, render_pdf
from .sections import TEMPLATES

bp = Blueprint("resumes", __name__, url_prefix="/resumes")


def _rows():
    return ProfileSection.query.filter_by(user_id=current_user.id).all()


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "resume"


@bp.route("/")
@login_required
def history():
    return render_template("versions.html", versions=current_user.versions, templates=TEMPLATES)


@bp.route("/generate", methods=["GET", "POST"])
@login_required
def generate():
    rows = _rows()
    personal = next((r for r in rows if r.section == "personal"), None)

    if request.method == "POST":
        template = request.form.get("template")
        if template not in TEMPLATES:
            abort(400)
        if not personal or not personal.data.get("full_name"):
            flash("Fill in your personal details before generating a resume.", "danger")
            return redirect(url_for("profile.edit_section", section="personal"))

        context = build_context(current_user, rows)
        try:
            pdf_bytes = render_pdf(template, context)
        except Exception as exc:  # PDF rendering or browser problems
            flash(f"Could not render the PDF: {exc}", "danger")
            return redirect(url_for("resumes.generate"))

        # Retry once if two requests race for the same version number.
        for attempt in range(2):
            next_no = (db.session.query(func.max(ResumeVersion.version_no))
                       .filter_by(user_id=current_user.id).scalar() or 0) + 1
            stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{_slug(personal.data['full_name'])}-v{next_no}.pdf"
            key = f"resumes/user-{current_user.id}/v{next_no}-{stamp}-{template}.pdf"
            version = ResumeVersion(user_id=current_user.id, version_no=next_no,
                                    template=template, storage_key=key, filename=filename)
            db.session.add(version)
            try:
                db.session.flush()
                break
            except IntegrityError:
                db.session.rollback()
                if attempt == 1:
                    raise

        storage.save_pdf(key, pdf_bytes)
        db.session.commit()
        flash(f"Resume version {next_no} generated.", "success")
        return redirect(url_for("resumes.history"))

    return render_template("generate.html", templates=TEMPLATES, has_profile=bool(personal))


@bp.route("/preview/<template>")
@login_required
def preview(template):
    if template not in TEMPLATES:
        abort(404)
    return Response(render_html(template, build_context(current_user, _rows())),
                    mimetype="text/html")


def _own_version(version_id):
    version = db.session.get(ResumeVersion, version_id)
    if version is None or version.user_id != current_user.id:
        abort(404)
    return version


@bp.route("/<int:version_id>/download")
@login_required
def download(version_id):
    version = _own_version(version_id)
    url = storage.download_url(version.storage_key, version.filename)
    if url:
        return redirect(url)
    return send_file(storage.local_path(version.storage_key), as_attachment=True,
                     download_name=version.filename, mimetype="application/pdf")
