FROM python:3-alpine AS builder

WORKDIR /app

RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements/production.txt .
COPY requirements/base.txt .
COPY requirements/connectors.txt .
COPY . .
RUN pip install -r production.txt -r connectors.txt

# Stage 2
FROM python:3-alpine AS runner

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PORT=8000

WORKDIR /app

COPY --from=builder /app/venv venv
# COPY config config
COPY . .
COPY run.sh /run.sh
RUN chmod +x /run.sh
RUN cat /run.sh

ENV DJANGO_SECRET_KEY='#a*(l02@96-k=ft*+90rf$)dz$@&$h==7nqhl2(pd^sz-2_8y='
ENV POSTGRES_HOST=''
ENV POSTGRES_USER=''
ENV POSTGRES_DB=''
ENV POSTGRES_PASSWORD=''
ENV DJANGO_ADMIN_URL=''
ENV DJANGO_ALLOWED_HOSTS=''
ENV TRUSTED_ORIGINS=''
ENV REDIS_URL=''
ENV C_BROKER_URL=''
ENV C_RESULT_BACKEND=''

RUN python manage.py collectstatic --settings=config.settings.production

EXPOSE ${PORT}

CMD ["/run.sh"]
