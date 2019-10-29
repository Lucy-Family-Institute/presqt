Architecture/Infrastructure
==================================
Development Environments
------------------------
One of the design goals for PresQT is to use Docker throughout our pipeline to make it as easy as 
possible to newcomers to the project to get up and running with PresQT services.

The first step towards making that goal a reality was creating an easy to use development environment 
using Docker compose.

The diagram below illustrates how we are using Docker Compose to create a constellation of 3 
containers on developer machines representing the three essential components of PresQT as it is 
currently constructed:

* Nginx
    * Serves as a security layer for incoming requests to PresQT
    * Can also serve as a load balancer in the future
* Django/Gunicorn
    * After passing through the Nginx layer, this container processes API requests from users and 
      then takes the necessary actions to fulfill the user's requests by communicating with partner services via the their own APIs. 

Those familiar with Docker may derive additional information on the setup by inspecting the 
visualization below.

How to Spin-Up a PresQT Development Environment
+++++++++++++++++++++++++++++++++++++++++++++++
We will include instructions in the Github repo on how a new developer/partner contributor can 
spin-up their own local development environment.

QA/Production Deployments
-------------------------
Unsurprisingly, there is a significant overlap between the developer setup and the QA/Production 
deployment architecture. Here are some of the points where the details vary:

* One machine (the "Web Server") will be the host for the Nginx container and one or more identical 
  Django containers that will respond to APIs requests from client researchers in a load balanced manner.


.. toctree::
   :maxdepth: 3