Development Environment Setup
=============================

Prerequisites
+++++++++++++
* Local installation of Docker for Mac/Windows/Linux
* Knowledge of Git procedures
* Knowledge of setting environment variables
* Knowledge of ``docker-compose`` utility.

Local Development Environment Setup
+++++++++++++++++++++++++++++++++++
 1. Clone the repo to your local machine in the desired folder location:

    .. parsed-literal::
        $ git clone https://github.com/ndlib/presqt.git

 2. Export **required** ENV_VARS:

    * **ENVIRONMENT**: Should be either ``production`` or ``development``
    * **SECRET_KEY**: A Django "secret key" value.

    .. parsed-literal::
        # Example Exportation
        $ export ENVIRONMENT=development
        $ export SECRET_KEY=y4xgryt7ex9g+4mcs4=^sg5afp3lz#=94eb6=6o6l61o=a31y_h

 3. Export **optional** ENV_VARS for testing:

    * **CURATE_ND_TEST_TOKEN**: The test token for Curate's API.
    * **GITHUB_TEST_USER_TOKEN**: The test token for GitHub's API.
    * **OSF_TEST_USER_TOKEN**: The test token for OSF's API.
    * **OSF_PRIVATE_USER_TOKEN**: The private test token for OSF's API.
    * **OSF_UPLOAD_TEST_USER_TOKEN**: The upload test token for OSF's API.
    * **OSF_PRESQT_FORK_TOKEN**: The PresQT fork user ttest token for OSF's API.
    * **ZENODO_TEST_USER_TOKEN**: The test token for Zenodo's API.

    .. Note::
        Contact an administrator to get the target test tokens.

 |  4. Execute ``docker-compose`` up within the repo's base folder.

     .. parsed-literal::
        $ docker-compose up --build

 5. Navigate to https://localhost/api_v1/ in your browser.

Cron Container
+++++++++++++++++
There is now a third docker container that is responsible for running clean up tasks at specified
times. It has been implemented in development to run the `delete_outdated_mediafiles` command every
15 minutes. The command has also been altered slightly to delete any mediafiles held in these
directories when you are in a development environment. The command is set to run daily at 4:30am for
our other servers.