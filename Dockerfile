FROM python:3-alpine AS builder

WORKDIR /app

RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements/production.txt .
COPY requirements/base.txt .
COPY . .
RUN pip install -r production.txt

# Stage 2
FROM python:3-alpine AS runner

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PORT=8000

WORKDIR /app

RUN ls -al 
COPY --from=builder /app/venv venv
# COPY config config
COPY . .
ENV DJANGO_SECRET_KEY='#a*(l02@96-k=ft*+90rf$)dz$@&$h==7nqhl2(pd^sz-2_8y='
ENV POSTGRES_HOST=''
ENV POSTGRES_USER=''
ENV POSTGRES_DB=''
ENV POSTGRES_PASSWORD=''
ENV REDIS_URL=''
ENV DJANGO_ADMIN_URL=''
ENV DJANGO_ALLOWED_HOSTS=''
ENV TRUSTED_ORIGINS=''
ENV REDIS_URL=''

RUN python manage.py collectstatic --settings=config.settings.production

EXPOSE ${PORT}

CMD gunicorn --bind :${PORT} --workers 2 config.wsgi
