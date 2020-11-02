FROM python:3.7.1-alpine
LABEL purpose="Python container for CRON, logging and Django"

ARG BUILD_ENVIRONMENT
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Specify environment variables that should be
# present inside of the container. Default them
# to 'NA' if they are not available.
ENV ENVIRONMENT=${ENVIRONMENT:-production}
ENV DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.${ENVIRONMENT}}

ENV APPLICATION_DB = ${APPLICATION_DB:-NA}
ENV APPLICATION_USER = ${APPLICATION_USER:-NA}
ENV APPLICATION_PASSWORD = ${APPLICATION_PASSWORD:-NA}

WORKDIR /usr/local/etc
COPY requirements requirements

# Install System Level Dependencies
# Installing client libraries and any other package you need
RUN apk update && apk add libpq make

# Installing build dependencies
RUN apk add --virtual .build-deps gcc python-dev musl-dev postgresql-dev tzdata

RUN cp /usr/share/zoneinfo/America/Indianapolis /etc/localtime
RUN echo "America/Indianapolis" > /etc/timezone
RUN apk del tzdata
RUN pip install -r requirements/${BUILD_ENVIRONMENT}.txt

# Delete build dependencies
RUN apk del .build-deps

WORKDIR /usr/src/app
