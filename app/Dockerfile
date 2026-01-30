FROM python:3.11-slim

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY Pipfile Pipfile.lock ./

RUN pip install --no-cache-dir pipenv && \
    PIPENV_VENV_IN_PROJECT=1 pipenv install --system --deploy

COPY . .

CMD ["python", "-u", "main.py"]


