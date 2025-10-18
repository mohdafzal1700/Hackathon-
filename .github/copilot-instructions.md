## Quick purpose

Short, actionable guidance for AI coding agents working on this repository (a Cookiecutter-Django based monolith). Use these notes to find the right files, follow project conventions, and run common workflows.

## Big picture

- Single Django monolith. Apps live under `hirethon_template/` (e.g. `users`, `organizations`, `shorturls`).
- Configuration split: `config/settings/{base.py,local.py,production.py,test.py}`. Environment-driven via `django-environ`.
- API layer: Django REST Framework + drf-spectacular for schema (`/api/schema/`) and Swagger UI (`/api/docs/`).
- Background work: Celery configured in `config/celery_app.py` and uses `CELERY_` prefixed settings. Broker from `CELERY_BROKER_URL` (see `requirements/base.txt` for Redis/Celery deps).
- Docker/Deployment: Dockerfiles and compose helpers under `compose/` and `production/`; local dev compose manifests available (see `local.yml` and `compose/django/Dockerfile.base`).

## Key files to read first

- `config/settings/base.py` — canonical settings, INSTALLED_APPS, env flags (e.g. `DJANGO_READ_DOT_ENV_FILE`), `AUTH_USER_MODEL` and `LOCAL_APPS`.
- `manage.py` — entrypoint: default `DJANGO_SETTINGS_MODULE = config.settings.local` and app path handling.
- `config/urls.py` — top-level routes, health check, API docs, and debug-only error views.
- `config/celery_app.py` — Celery app, autodiscovery of `tasks.py` in apps.
- `pyproject.toml` — test, lint and typecheck configuration (pytest addopts, mypy, black, isort, djlint, pylint presets).
- `hirethon_template/conftest.py` — pytest fixtures and test patterns used across suites.
- Example app pattern: `organizations/views.py` — shows DRF `APIView` permission checks, Membership usage and serializer flow.

## Common developer workflows & commands

- Run dev server (uses `local` settings):

  python manage.py runserver

- Create superuser:

  python manage.py createsuperuser

- Run tests (pytest is configured to use `config.settings.test`):

  pytest

  # coverage + HTML report
  coverage run -m pytest && coverage html

- Type checking:

  mypy hirethon_template

- Linters/formatters: configured via `pyproject.toml` (black/isort/djlint/pylint). Run locally as usual.

- Celery (run from project root or `hirethon_template` per README):

  cd hirethon_template
  celery -A config.celery_app worker -l info
  celery -A config.celery_app beat

- Docker base image build (required before some Docker flows):

  docker build -t cookiecutter-django-base:latest -f compose/django/Dockerfile.base .

Notes: pytest addopts is set in `pyproject.toml` to `--ds=config.settings.test --reuse-db` so tests reuse the test DB.

## Project-specific conventions and patterns

- Local apps must be added to `LOCAL_APPS` in `config/settings/base.py` (e.g. `hirethon_template.users`). Follow the existing layout.
- Custom user model: `AUTH_USER_MODEL = "users.User"` — prefer importing models through `get_user_model()` in code to stay flexible.
- API style: DRF class-based views/serializers. Example: `organizations/views.py` returns serialized data only after membership checks; admin checks compare `membership.role == "Admin"`.
- Celery tasks should live in `tasks.py` inside the app and will be autodiscovered by `config/celery_app.py`.
- Environment control: `.env` is optional. The project reads it only when `DJANGO_READ_DOT_ENV_FILE` is true — do not assume a `.env` is loaded unless tests or CI set this.

## Integration points & external dependencies

- Database: `DATABASE_URL` env var (configured in `base.py`).
- Celery/Redis: `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` (the project expects Redis + hiredis in `requirements/base.txt`).
- Authentication: `rest_framework_simplejwt` + `dj-rest-auth`. JWT cookies configured under `REST_AUTH` in `base.py`.
- API docs: `drf-spectacular` is used; serving is restricted by `SERVE_PERMISSIONS` (admin-only by default).

## Editing guidance for an AI agent

- Preserve patterns already present: mirror DRF view/serializer/task structure. Use `serializers.py`, `views.py`, `tasks.py` inside the same app folder.
- When changing settings, update only the correct file under `config/settings/` and avoid editing `manage.py` settings assumptions unless necessary.
- For tests, use fixtures from `hirethon_template/conftest.py` and factories referenced there (e.g. `hirethon_template.users.tests.factories`). Tests expect `--ds=config.settings.test` and may rely on `--reuse-db`.
- For database access, prefer Django ORM and respect `ATOMIC_REQUESTS=True` set on the default DB.
- For background work, add Celery tasks to app `tasks.py`; reference `app.send_task` or shared_task decorators as in standard patterns.

## Example references (use these in edits and PR messages)

- Permission-check example: `organizations/views.py` — check membership and `membership.role == "Admin"` before writes.
- Celery bootstrap: `config/celery_app.py` (autodiscover tasks).
- Settings + env conventions: `config/settings/base.py` and `pyproject.toml` for developer tooling.

If anything here is unclear or you want more examples (tests, factories, common serializers), tell me which area to expand and I'll iterate.
