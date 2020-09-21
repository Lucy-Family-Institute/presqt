import asyncio
import aiohttp

from rest_framework import status

from presqt.targets.osf.utilities import get_follow_next_urls
from presqt.utilities import PresQTValidationError


def run_urls_async(url_list, headers):
    """
    Open an async loop and begin async calls.

    Parameters
    ----------
    url_list: list
        List of urls to call asynchronously

    headers: dict
        Necessary header for OSF calls

    Returns
    -------
    The data returned from the async call
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    data = loop.run_until_complete(async_main(url_list, headers))
    return data


def run_urls_async_with_pagination(url_list, headers):
    """
    Open an async loop and begin async calls.
    Also get all paginated pages and run them asynchronously.

    Parameters
    ----------
    url_list: list
        List of urls to call asynchronously.

    headers: dict
        Necessary header for OSF calls

    Returns
    -------
    The data returned from the async call
    """
    async_data = run_urls_async(url_list, headers)
    async_next_data = get_follow_next_urls(async_data)
    async_data.extend(run_urls_async(async_next_data, headers))

    return async_data


async def async_get(url, session, headers):
    """
    Coroutine that uses aiohttp to make a GET request. This is the method that will be called
    asynchronously with other GETs.

    Parameters
    ----------
    url: str
        URL to call

    session: ClientSession object
        aiohttp ClientSession Object

    headers: dict
        Necessary header for OSF calls

    Returns
    -------
    Response JSON
    """
    async with session.get(url, headers=headers) as response:
        try:
            assert response.status == 200
            return await response.json()
        except AssertionError:
            if response.status == 403: #TODO: doing this to avoid private file errors look into it
                pass
            else:
                raise PresQTValidationError("The source target API returned an error. Please try again.",
                                            status.HTTP_500_INTERNAL_SERVER_ERROR)


async def async_main(url_list, headers):
    """
    Main coroutine method that will gather the url calls to be made and will make them
    asynchronously.

    Parameters
    ----------
    url_list: list
        List of urls to call

    headers: dict
        Necessary header for OSF calls

    Returns
    -------
    List of data brought back from each coroutine called.
    """
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[async_get(url, session, headers) for url in url_list])
