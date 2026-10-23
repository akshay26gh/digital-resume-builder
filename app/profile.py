from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .models import ProfileSection
from .sections import SECTION_ORDER, SECTIONS, empty_section, parse_section

bp = Blueprint("profile", __name__)


def _get_row(section):
    return ProfileSection.query.filter_by(user_id=current_user.id, section=section).first()


@bp.route("/dashboard")
@login_required
def dashboard():
    rows = {r.section: r for r in ProfileSection.query.filter_by(user_id=current_user.id)}
    status = []
    for key in SECTION_ORDER:
        row = rows.get(key)
        filled = bool(row and any(
            (v if not isinstance(v, list) else v) for v in row.data.values()
        ))
        status.append({"key": key, "title": SECTIONS[key]["title"], "filled": filled})
    return render_template("dashboard.html", status=status, versions=current_user.versions[:5])


@bp.route("/profile/<section>", methods=["GET", "POST"])
@login_required
def edit_section(section):
    if section not in SECTIONS:
        abort(404)
    spec = SECTIONS[section]

    if request.method == "POST":
        data = parse_section(section, request.form)
        if section == "personal" and not data.get("full_name"):
            flash("Full name is required.", "danger")
        else:
            row = _get_row(section)
            if row is None:
                row = ProfileSection(user_id=current_user.id, section=section, data=data)
                db.session.add(row)
            else:
                row.data = data
            db.session.commit()
            flash(f"{spec['title']} saved.", "success")
            idx = SECTION_ORDER.index(section)
            if request.form.get("next") and idx + 1 < len(SECTION_ORDER):
                return redirect(url_for("profile.edit_section", section=SECTION_ORDER[idx + 1]))
            return redirect(url_for("profile.dashboard"))

    row = _get_row(section)
    data = row.data if row else empty_section(section)
    if spec["kind"] == "list" and not data.get("entries"):
        data = {"entries": [{f["name"]: "" for f in spec["fields"]}]}
    return render_template("section_form.html", key=section, spec=spec, data=data,
                           order=SECTION_ORDER, sections=SECTIONS)
