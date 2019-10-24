Development Environment Setup
=============================

Prerequisites
+++++++++++++
* Local installation of Docker for Mac/Windows/Linux
* Knowledge of Git procedures
* Knowledge of setting environment variables
* Knowledge of ``docker-compose`` utility.

**To bring up a local version of PresQT, take the following steps:**

1. Clone the repo to your local machine in the desired folder location:
    ``$ git clone https://github.com/ndlib/presqt.git``
2. Export the following ENV_VARS:
    * **ENVIRONMENT**: Should be either ``production`` or ``development``
    * **SECRET_KEY**: A Django "secret key" value.
    
    The following two are only needed if you intend on running all test cases.
    * CURATE_ND_TEST_TOKEN: A token for Curate's API.
    * GITHUB_TEST_USER_TOKEN: A token for GitHub's API.

Example Exportation:
    ``$ export ENVIRONMENT=development``
    ``$ export SECRET_KEY=y4xgryt7ex9g+4mcs4=^sg5afp3lz#=94eb6=6o6l61o=a31y_h``

3. Execute ``docker-compose`` up within the repo's base folder.
    ``$ docker-compose up``
4. Navigate to http://127.0.0.1/api_v1/ or http://localhost/api_v1/ in your browser.

.. toctree::
   :maxdepth: 3