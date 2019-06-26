FROM python:3.7-alpine
ARG BUILD_ENVIRONMENT

# Installing client libraries and any other package you need
RUN apk update && apk add libpq

# Installing build dependencies
RUN apk add --virtual .build-deps gcc python-dev musl-dev postgresql-dev tzdata


# For development, we don't want to generate .pyc files
# or buffer any output.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/local/etc
COPY requirements requirements

RUN cp /usr/share/zoneinfo/America/Indianapolis /etc/localtime
RUN echo "America/Indianapolis" > /etc/timezone
RUN apk del tzdata

RUN pip install -r requirements/${BUILD_ENVIRONMENT}.txt

# Delete build dependencies
RUN apk del .build-deps

WORKDIR /usr/src/app
COPY . /usr/src/app

EXPOSE 8000

ENTRYPOINT ["/usr/src/app/docker/django_entrypoint.sh"]