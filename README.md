# PresQT

IMLS grant funded project(PresQT) to build Preservation Quality Tools and RESTful Services to Improve Preservation and Re-use of Research Data &amp; Software. More info at https://presqt.crc.nd.edu/ and https://osf.io/d3jx7/

## General Technical Documentation

Please see our [Gitbook](https://crc-nd.gitbook.io/presqt/) documentation repo.

## Developer Setup

### Prerequisites

- Local installation of Docker for Mac/Windows/Linux
- Knowledge of setting environment variables
- Knowledge of `docker-compose` utility.

To bring up a local version of PresQT, take the following steps:

1. Clone the repo to your local machine.
2. Export the following ENV_VARS:
   - POSTGRES_USER: Sets the user for the Postgres database.
   - POSTGRES_PASSWORD: Sets the password for the Postgres database.
   - POSTGRES_DB: Sets the name for the Postgres database.
   - ENVIRONMENT: Should be either `production` or `development`
   - SECRET_KEY: A Django "secret key" value.
3. Execute `docker-compose up` within the repo's base folder.
4. Navigate to http://127.0.0.1:8000 or http://localhost:8000 in your browser.