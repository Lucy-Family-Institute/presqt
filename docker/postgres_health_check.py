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

try:
    postgres = psycopg2.connect(
        host='presqt_postgres',
        user=os.environ['POSTGRES_USER'],
        database=os.environ['POSTGRES_DB'],
        password=os.environ['POSTGRES_PASSWORD']
    )
except psycopg2.OperationalError as error:
    sys.exit(1)
else:
    sys.exit()
