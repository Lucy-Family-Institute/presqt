FROM postgres:9.6.19

RUN apt-get update && apt-get install -y openssh-server

ENV ENVIRONMENT = ${ENVIRONMENT:-production}
ENV APPLICATION_DB = ${APPLICATION_DB:-NA}
ENV APPLICATION_USER = ${APPLICATION_USER:-NA}
ENV APPLICATION_PASSWORD = ${APPLICATION_PASSWORD:-NA}

ENV REMOTE_USER=${REMOTE_USER:-NA}
ENV REMOTE_SERVER=${REMOTE_SERVER:-NA}
ENV SSH_PRIVATE_KEY=${SSH_PRIVATE_KEY:-NA}

USER postgres
RUN mkdir /var/lib/postgresql/.ssh
RUN mkdir /var/lib/postgresql/downloaded_backup
