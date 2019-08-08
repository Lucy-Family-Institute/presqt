import asyncio
import datetime
import aiohttp

import requests
from django.core.management import BaseCommand

# async def make_request():
#     url = 'https://api.osf.io/v2/files/5d49d02722a88600164dcbad'
#     requests.get(url, headers={'Authorization': 'Bearer Airlov2nBOb41T1d3FkTIbzC8ahq3nBWDxMbGyrUYvWDinKWJgrPO52uuS6KJIBXKXFtlv'})
#
# async def main():
#     await asyncio.gather(*[make_request() for x in range(10)])

async def fetch(session):
    async with session.get('https://api.osf.io/v2/files/5d49d02722a88600164dcbad', headers={'Authorization': 'Bearer Airlov2nBOb41T1d3FkTIbzC8ahq3nBWDxMbGyrUYvWDinKWJgrPO52uuS6KJIBXKXFtlv'}) as response:
        # print(response)
        assert response.status == 200
        return await response.json()

async def main():
    async with aiohttp.ClientSession() as session:
        responses = await asyncio.gather(*[fetch(session) for x in range(50)])
    #     html = await fetch(session, 'http://python.org')
        print(responses)

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        start_time = datetime.datetime.now()
        for i in range(50):
            requests.get('https://api.osf.io/v2/files/5d49d02722a88600164dcbad', headers={'Authorization': 'Bearer Airlov2nBOb41T1d3FkTIbzC8ahq3nBWDxMbGyrUYvWDinKWJgrPO52uuS6KJIBXKXFtlv'})
        end_time1 = datetime.datetime.now() - start_time


        start_time = datetime.datetime.now()
        # asyncio.run(main())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        end_time2 = datetime.datetime.now() - start_time

        print(end_time1)
        print(end_time2)
