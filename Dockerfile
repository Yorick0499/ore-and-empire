FROM python:3.12-slim-trixie
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/* && useradd --create-home --uid 1000 ore
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN ORE_BUILD_STATIC=1 SECRET_KEY=build-only-placeholder python manage.py collectstatic --noinput && mkdir -p backups telemetry-archives && chown -R ore:ore /app
USER ore
EXPOSE 8080
CMD ["gunicorn","-c","deploy/gunicorn.conf.py","ore_empire.wsgi:application"]
