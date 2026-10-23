# Digital Resume Builder

User profile-based resume generator built with Flask.

| Requirement | Implementation |
|---|---|
| Host on EC2 | Gunicorn + Nginx (`deploy/`) |
| Metadata in RDS | SQLAlchemy -> PostgreSQL or MySQL via `DATABASE_URL` |
| Files in S3 | `boto3` (`app/storage.py`), presigned download URLs |
| Sectioned form model | `app/sections.py` drives forms, parsing and templates |
| Template engine to PDF | Jinja2 HTML templates + WeasyPrint (`app/pdf.py`) |
| Version resumes per user | `resume_versions` table, `v1, v2, ...` per user |

## Project layout

```
config.py            settings from environment
run.py / wsgi.py     dev entry point / gunicorn entry point
app/
  __init__.py        app factory
  models.py          User, ProfileSection, ResumeVersion
  sections.py        section definitions + form parsing
  auth.py            register / login / logout
  profile.py         dashboard + section editor
  resumes.py         preview, generate, history, download
  pdf.py             Jinja2 -> HTML -> PDF
  storage.py         S3 (or local disk in dev)
  templates/         UI pages
  templates/resumes/ classic, modern, minimal resume templates
deploy/              gunicorn.service, nginx.conf
```

## Run locally

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # leave DATABASE_URL and S3_BUCKET empty for local mode
python run.py                     # http://127.0.0.1:5000
```

Local mode uses SQLite and saves PDFs to `local_storage/`.

WeasyPrint needs system libraries:
- Ubuntu/Debian: `sudo apt install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b`
- macOS: `brew install pango`
- Windows: see the WeasyPrint install docs (GTK runtime)

## AWS setup

1. **RDS**: create a PostgreSQL (or MySQL) instance, create a database, and allow the EC2 security group on port 5432 (3306 for MySQL). Set `DATABASE_URL` in `.env`.
2. **S3**: create a private bucket (block all public access). Set `S3_BUCKET` and `AWS_REGION`.
3. **IAM role for EC2** with this policy (replace the bucket name), attached to the instance:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Action": ["s3:PutObject", "s3:GetObject"],
       "Resource": "arn:aws:s3:::YOUR_BUCKET/resumes/*"
     }]
   }
   ```
4. **EC2** (Ubuntu): open ports 22 and 80 in the security group, then:

```bash
sudo apt update
sudo apt install -y python3-venv nginx libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b
git clone <your-repo> ~/resume_builder && cd ~/resume_builder
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env     # set SECRET_KEY, DATABASE_URL, S3_BUCKET

sudo cp deploy/gunicorn.service /etc/systemd/system/resume_builder.service
sudo systemctl daemon-reload
sudo systemctl enable --now resume_builder

sudo cp deploy/nginx.conf /etc/nginx/sites-available/resume_builder
sudo ln -s /etc/nginx/sites-available/resume_builder /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

Tables are created automatically on first start (`db.create_all()`). For schema changes later, add Flask-Migrate.
Add HTTPS with `sudo apt install certbot python3-certbot-nginx && sudo certbot --nginx`.

## How it works

1. Register / login.
2. Fill the sections (Personal, Summary, Education, Experience, Projects, Skills). Each is stored as JSON in `profile_sections`.
3. Pick a template (preview is available) and click **Generate PDF**.
4. The app renders the Jinja2 template, converts it with WeasyPrint, uploads the PDF to S3 under `resumes/user-<id>/...`, and inserts a `resume_versions` row with the next version number for that user.
5. Download any previous version from **Versions** (S3 presigned URL, expires in 5 minutes by default).

## Adding a template

Create `app/templates/resumes/<name>.html` and add `"<name>": "Description"` to `TEMPLATES` in `app/sections.py`. Templates receive `p` (personal), `summary`, `education`, `experience`, `projects`, `skills`, and the helper `lines()`.

## Team

Team S3 Skyline - 44111153 - Akshay Kumar J
