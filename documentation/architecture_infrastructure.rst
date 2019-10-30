Architecture/Infrastructure
===========================
Development Environments
------------------------
PresQT uses Docker throughout its pipeline to make it as easy as possible for newcomers to the
project to get up and running with PresQT services. This was accomplished by creating an easy to
use development environment using Docker compose.

The diagram below illustrates how we are using Docker Compose to create a constellation of 2
containers on developer machines representing the two essential components of PresQT:

* Nginx
    * Serves as a security layer for incoming requests to PresQT
    * Can also serve as a load balancer in the future
* Django/Gunicorn
    * After passing through the Nginx layer, this container processes API requests from users and 
      then takes the necessary actions to fulfill the user's requests by communicating with partner
      services via the their own APIs.

INSERT IMAGE HERE

QA/Production Deployments
-------------------------
Unsurprisingly, there is a significant overlap between the developer setup and the QA/Production 
deployment architecture. The following is how they will vary:

* One machine (the "Web Server") will be the host for the Nginx container and one or more identical 
  Django containers that will respond to APIs requests from client researchers in a load balanced manner.

INSERT IMAGE HERE

.. toctree::
   :maxdepth: 3