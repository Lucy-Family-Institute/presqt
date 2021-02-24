# [PresQT][presqt-page]

IMLS grant funded project(PresQT) to build Preservation Quality Tools and RESTful Services to Improve Preservation and Re-use of Research Data &amp; Software. More info at https://presqt.crc.nd.edu/ and https://osf.io/d3jx7/

## General Technical Documentation

Please see our [ReadTheDocs][readthedocs] documentation page.

## Development Partners
[![][nd-logo]][nd-site]

[![][imls-logo]][imls-site]

## Developer Setup

### Prerequisites

- Local installation of Docker for Mac/Windows/Linux
- Knowledge of setting environment variables
- Knowledge of `docker-compose` utility.

To bring up a local version of PresQT, take the following steps:

1. Clone the repo to your local machine.
2. Export the following ENV_VARS:
   - ENVIRONMENT: Should be either `production` or `development`
   - SECRET_KEY: A Django "secret key" value.
3. Execute `docker-compose up` within the repo's base folder.
4. Navigate to http://127.0.0.1/api_v1/ or http://localhost/api_v1/ in your browser.


[presqt-page]: https://presqt.crc.nd.edu
[readthedocs]: https://presqt.readthedocs.io/en/latest/
[nd-logo]: https://studyprograms.capstonesource.com/wp-content/uploads/2019/07/notre-dame.jpg
[nd-site]: https://www.nd.edu/
[imls-site]: https://www.imls.gov/
[imls-logo]: https://i.imgur.com/iscE0JC.jpg
