FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root

COPY . .

# Python ko batao src folder mein module hai
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "fastapi_auth_system.main:app", "--host", "0.0.0.0", "--port", "8000"]