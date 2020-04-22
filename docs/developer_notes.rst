Developer Notes
===============

Testing
-------

A high code coverage percentage has been maintained with unit and integration tests for all code
using a package called Coverage (https://coverage.readthedocs.io/en/v4.5.x/) to track code coverage.

To run unit tests without using Coverage:

.. parsed-literal::
    $ python manage.py test

To run unit tests using Coverage with comprehensive code coverage report generated into an HTML file:

.. parsed-literal::
    coverage run manage.py test && coverage combine && coverage html

.. note::

    This command will generate a directory that is ignored by Git via our .gitignore file. To see the
    code coverage open the file /coverage_html/index.html in a browser.

.. note::
    Coverage options are specified in a configuration file called .coveragerc. This is where you would
    add files/directories you want to omit from the Coverage report.

.. note::
    'coverage combine' will take the coverage files created for multiprocesses (located in the base directory)
    and will combine them with the main coverage files . If a test using multiprocessing fails these
    coverage files will remain and must be deleted manually.

We also tried to split unit and integration tests up between core PresQT code and Target code. Tests
that cover core code reside in ``presqt/api_v1/tests/`` while target tests that cover target functions
reside in ``presqt/targets/{target_name}/tests/`` .

.. attention::
    All tests require their corresponding target tokens to be stored as environment variables since
    these tokens can not be stored publicly. Contact an administrator for access to these.

Docker Commands
---------------
To rebuild the docker container after a new package has been added to the requirements files:

.. parsed-literal::
    $ docker-compose up --build

Run the following command for an `interactive -i terminal -t` for this container:

.. parsed-literal::
    $ docker exec -i -t presqt_presqt_django_1 /bin/ash

Updating Documentation
----------------------
As the project grows we encourage developers to add documentation.
PresQT documentation is built using Sphinx and ReadtheDocs.

When documentation is added you should just need to run while in the ``/docs`` directory:

.. parsed-literal::
    $ make clean
    $ make html

Otherwise reference Sphinx documentation for more information on adding documentation,
https://www.sphinx-doc.org/en/master/usage/quickstart.html.


GitHub Differences
------------------
There is a slight difference in how we have implemented GitHub as opposed to other partners. Due to
the way GitHub's API handles files, there is no way for us to hit an endpoint with a given id. The
only way to navigate to a files endpoint is to know the associated GitHub username and repository
title. We have decided to make our own unique id's for these items by combining the repo_id and the
path to the file/dir. 

Example of an id:

.. parsed-literal::
    21387123:path2%Fto%2Ffile%2Ejpg 
    
We then translate this into two get requests. The first one will be to the repo id. 

Example: 

.. parsed-literal::
    https://api.github.com/repositories/21387123

From this, we can get a contents url that we can translate into a request. 

Example: 

.. parsed-literal::
    https://api.github.com/repos/PresQT-QA-TEST/Good_Egg-PresQT2-/contents/path/to/file.jpg

Using this custom generated id, we can hit this endpoint on PresQT to get file details.

.. parsed-literal::
    https://presqt-qa.crc.nd.edu/api_v1/targets/github/resources/21387123:path%252Fto%252Ffile%252Ejpg
