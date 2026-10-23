
"""Template engine: Jinja2 HTML -> PDF with Chromium."""
from flask import render_template

from .sections import SECTION_ORDER, empty_section, lines, skill_list


def build_context(user, rows):
    """Merge saved sections with empty defaults so templates never miss a key."""
    data = {key: empty_section(key) for key in SECTION_ORDER}
    for row in rows:
        data[row.section] = row.data
    return {
        "user": user,
        "p": data["personal"],
        "summary": data["summary"].get("text", ""),
        "education": data["education"].get("entries", []),
        "experience": data["experience"].get("entries", []),
        "projects": data["projects"].get("entries", []),
        "skills": skill_list(data["skills"].get("text", "")),
        "lines": lines,
    }


def render_html(template_name, context):
    return render_template(f"resumes/{template_name}.html", **context)


def render_pdf(template_name, context):
    """Render a resume to PDF while blocking external resource requests."""
    from playwright.sync_api import sync_playwright

    html = render_html(template_name, context)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(java_script_enabled=False)

            # Resume templates are self-contained. Block network requests.
            page.route("**/*", lambda route: route.abort())

            page.set_content(html, wait_until="load")
            return page.pdf(
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
            )
        finally:
            browser.close()
