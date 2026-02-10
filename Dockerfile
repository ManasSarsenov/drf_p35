FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /app

COPY . .

RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "root.wsgi:application", "--bind", "0.0.0.0:8000"]

#CMD ["uv", "run", "python3", "manage.py", "runserver", "0:8000"]
