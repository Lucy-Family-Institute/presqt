FROM postgres:9.6.19

RUN apt-get update && apt-get install -y openssh-server

ENV ENVIRONMENT = ${ENVIRONMENT:-production}
ENV APPLICATION_DB = ${APPLICATION_DB:-NA}
ENV APPLICATION_USER = ${APPLICATION_USER:-NA}
ENV APPLICATION_PASSWORD = ${APPLICATION_PASSWORD:-NA}

USER postgres
RUN mkdir /var/lib/postgresql/.ssh
RUN mkdir /var/lib/postgresql/downloaded_backup

COPY docker/postgres_1_setup_db.sh /docker-entrypoint-initdb.d/postgres_1_setup_db.sh