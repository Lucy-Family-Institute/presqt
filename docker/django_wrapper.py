"""
A simple script that checks for the existence of
an application database using environment variables
to avoid hardcoding connection info.

This is useful as Postgres bootstrapping can take
a variable amount of time after the container is 
actually "up".

The "depends on" directive in compose files can
be misleading since it only verifies that the 
container is up, not that bootstraping has completed.
"""
import os
import sys

import psycopg2

print(os.environ)

try:
    postgres = psycopg2.connect(
        host='postgres_db',
        user=os.environ['APPLICATION_USER'],
        database=os.environ['APPLICATION_DB'],
        password=os.environ['APPLICATION_PASSWORD']
    )
except psycopg2.OperationalError:
    sys.exit(1)
else:
    sys.exit()