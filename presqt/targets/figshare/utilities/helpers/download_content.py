import base64
import requests


def download_project(username, url, headers, project_name, files):
    """
    Function to extract all files from a given project.

    Parameters
    ----------
    username : str
        The user's FigShare username.
    url : str
        The url of the project's contents
    header: dict
        API header expected by FigShare
    project_name : str
        The name of the project that is being downloaded
    files : list
        A list of dictionaries with file information

    Returns
    -------
    A list of file dictionaries and a list of empty containers
    """
    initial_data = requests.get(url, headers=headers).json()
    action_metadata = {"sourceUsername": username}

    # Build list of article urls
    article_urls = [article['url'] for article in initial_data]

    for url in article_urls:
        # Here we go....
        article_data = requests.get(url, headers=headers).json()

        for file in article_data['files']:
            files.append({
                "file": file['download_url'],
                "hashes": {"md5": file['computed_md5']},
                "title": file['name'],
                "path": "/{}/{}/{}".format(project_name, article_data['title'], file['name']),
                "source_path": "/{}/{}/{}".format(project_name, article_data['title'], file['name']),
                "extra_metadata": {
                    "size": file['size']
                }
            })

    return files, [], action_metadata


def download_article(username, url, headers, project_name, files):
    """
    Function to extract all files from a given article.

    Parameters
    ----------
    username : str
        The user's FigShare username.
    url : str
        The url of the project's contents
    header: dict
        API header expected by FigShare
    project_name : str
        The name of the project that is being downloaded
    files : list
        A list of dictionaries with file information

    Returns
    -------
    A list of file dictionaries and a list of empty containers
    """
    article_data = requests.get(url, headers=headers).json()
    action_metadata = {"sourceUsername": username}

    for file in article_data['files']:
        files.append({
            "file": file['download_url'],
            "hashes": {"md5": file['computed_md5']},
            "title": file['name'],
            "path": "/{}/{}".format(article_data['title'], file['name']),
            "source_path": "/{}/{}/{}".format(project_name, article_data['title'], file['name']),
            "extra_metadata": {
                "size": file['size']
            }
        })

    return files, [], action_metadata
