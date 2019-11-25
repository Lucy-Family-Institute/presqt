import asyncio

import aiohttp


def run_urls_async(self_instance, url_list):
    """
    Open an async loop and begin async calls.

    Parameters
    ----------
    self_instance: Target Class Instance
        Instance of the Target class we are using for async calls.

    url_list: list
        List of urls to call asynchronously

    Returns
    -------
    The data returned from the async call
    """
    loop = asyncio.new_event_loop()
    data = loop.run_until_complete(async_main(self_instance, url_list))
    return data


def run_urls_async_with_pagination(self_instance, url_list):
    """
    Open an async loop and begin async calls.
    Also get all paginated pages and run them asynchronously.

    Parameters
    ----------
    self_instance: Target Class Instance
        Instance of the Target class we are using for async calls.

    url_list: list
        List of urls to call asynchronously.

    Returns
    -------
    The data returned from the async call
    """
    async_data = run_urls_async(self_instance, url_list)
    async_next_data = self_instance._get_follow_next_urls(async_data)
    async_data.extend(run_urls_async(self_instance, async_next_data))

    return async_data


async def async_get(self_instance, url, session):
    """
    Coroutine that uses aiohttp to make a GET request. This is the method that will be called
    asynchronously with other GETs.

    Parameters
    ----------
    self_instance: Target Class Instance
        Instance of the Target class we are using for async calls.

    url: str
        URL to call

    session: ClientSession object
        aiohttp ClientSession Object

    Returns
    -------
    Response JSON
    """
    async with session.get(url, headers=self_instance.session.headers) as response:
        assert response.status == 200
        return await response.json()


async def async_main(self_instance, url_list):
    """
    Main coroutine method that will gather the url calls to be made and will make them
    asynchronously.

    Parameters
    ----------
    self_instance: Target Class Instance
        Instance of the Target class we are using for async calls.

    url_list: list
        List of urls to call

    Returns
    -------
    List of data brought back from each coroutine called.
    """
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[async_get(self_instance, url, session) for url in url_list])