"""Sectioned form model.

Each section declares its kind and fields. The same definition drives the form
rendering, parsing of submitted data, and what the resume templates receive.

kind:
  "single" - one set of fields (e.g. personal details)
  "list"   - repeatable entries (e.g. several jobs)
  "text"   - one free-text block
"""

SECTIONS = {
    "personal": {
        "title": "Personal details",
        "kind": "single",
        "fields": [
            {"name": "full_name", "label": "Full name", "type": "text", "required": True},
            {"name": "headline", "label": "Headline (e.g. Python Developer)", "type": "text"},
            {"name": "email", "label": "Email", "type": "email"},
            {"name": "phone", "label": "Phone", "type": "text"},
            {"name": "location", "label": "Location", "type": "text"},
            {"name": "linkedin", "label": "LinkedIn URL", "type": "text"},
            {"name": "github", "label": "GitHub URL", "type": "text"},
        ],
    },
    "summary": {
        "title": "Summary",
        "kind": "text",
        "fields": [{"name": "text", "label": "Professional summary", "type": "textarea"}],
    },
    "education": {
        "title": "Education",
        "kind": "list",
        "fields": [
            {"name": "institution", "label": "Institution", "type": "text"},
            {"name": "degree", "label": "Degree / Course", "type": "text"},
            {"name": "start", "label": "Start (e.g. 2022)", "type": "text"},
            {"name": "end", "label": "End (e.g. 2026)", "type": "text"},
            {"name": "grade", "label": "CGPA / Percentage", "type": "text"},
        ],
    },
    "experience": {
        "title": "Experience",
        "kind": "list",
        "fields": [
            {"name": "company", "label": "Company", "type": "text"},
            {"name": "role", "label": "Role", "type": "text"},
            {"name": "start", "label": "Start", "type": "text"},
            {"name": "end", "label": "End (or Present)", "type": "text"},
            {"name": "details", "label": "Details (one bullet per line)", "type": "textarea"},
        ],
    },
    "projects": {
        "title": "Projects",
        "kind": "list",
        "fields": [
            {"name": "name", "label": "Project name", "type": "text"},
            {"name": "link", "label": "Link", "type": "text"},
            {"name": "tech", "label": "Tech stack", "type": "text"},
            {"name": "details", "label": "Details (one bullet per line)", "type": "textarea"},
        ],
    },
    "skills": {
        "title": "Skills",
        "kind": "text",
        "fields": [{"name": "text", "label": "Skills (comma separated)", "type": "textarea"}],
    },
}

SECTION_ORDER = ["personal", "summary", "education", "experience", "projects", "skills"]

TEMPLATES = {
    "classic": "Classic - serif, single column",
    "modern": "Modern - coloured header, sans-serif",
    "minimal": "Minimal - compact, ATS friendly",
}


def parse_section(section_key, form):
    """Turn submitted form data into the JSON stored in the database."""
    spec = SECTIONS[section_key]
    names = [f["name"] for f in spec["fields"]]

    if spec["kind"] in ("single", "text"):
        return {n: (form.get(n) or "").strip() for n in names}

    columns = {n: form.getlist(n) for n in names}
    count = max((len(v) for v in columns.values()), default=0)
    entries = []
    for i in range(count):
        entry = {n: (columns[n][i] if i < len(columns[n]) else "").strip() for n in names}
        if any(entry.values()):
            entries.append(entry)
    return {"entries": entries}


def empty_section(section_key):
    spec = SECTIONS[section_key]
    if spec["kind"] == "list":
        return {"entries": []}
    return {f["name"]: "" for f in spec["fields"]}


def lines(value):
    """Split a textarea into non-empty lines (used by templates for bullets)."""
    return [ln.strip(" -•\t") for ln in (value or "").splitlines() if ln.strip()]


def skill_list(value):
    return [s.strip() for s in (value or "").replace("\n", ",").split(",") if s.strip()]
