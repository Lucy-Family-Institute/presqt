from presqt.targets.utilities import get_page_total


def get_follow_next_urls(data_list):
    """
    Get a list of 'next' urls to run asynchronously.

    Parameters
    ----------
    data_list: list
        List of json data.

    Returns
    -------
    List of urls
    """
    url_list = []
    for data in data_list:
        if data: #ToDo: doing this to avoid private file errors look into it
            meta = data['links']['meta']
            next_url = data['links']['next']
            if next_url:
                page_total = get_page_total(meta['total'], meta['per_page'])
                [url_list.append('{}{}'.format(
                    next_url[:-1], number)) for number in range(2, page_total + 1)]
    return url_list