import asyncio
import aiohttp

from django.core.management import BaseCommand

async def fetch(session):
    async with session.get('https://api.osf.io/v2/files/5d49d02722a88600164dcbad', headers={'Authorization': 'Bearer Airlov2nBOb41T1d3FkTIbzC8ahq3nBWDxMbGyrUYvWDinKWJgrPO52uuS6KJIBXKXFtlv'}) as response:
        assert response.status == 200
        return await response.json()

async def main():
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[fetch(session) for x in range(50)])

class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        loop = asyncio.get_event_loop()
        da_results = loop.run_until_complete(main())
        print(da_results)
