import json
import os
import sys
import logging

import graypy

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("nginx")
logger.addHandler(logging.StreamHandler())
logger.addHandler(graypy.GELFTLSHandler(
    host='prometheus-logging.crc.nd.edu',
    port=12201,
    extra_fields=True,
    facility='n/a',
    localname="presqt_nginx_logging_" + os.environ["ENVIRONMENT"],
    level_names=True,
))

log_format ='{remote_addr} - {remote_user} [{timestamp}] "{request}" {status} {body_bytes_sent} "{http_referer}" "{http_user_agent}" "{http_x_forwarded_for}"'

if __name__ == "__main__":
    print("flogger is live")
    for line in sys.stdin:
        line = line.rstrip()
        data = json.loads(line)
        logger.info(log_format.format_map(data), extra=data)
