#!/bin/bash
# pipe none of the existing lines, but follow all appended lines
tail -n 0 -f /var/log/nginx/python_access.log | python flogger.py
