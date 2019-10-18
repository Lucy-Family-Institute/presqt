import itertools
import json
import os
import requests

from presqt.targets.osf.classes.main import OSF
from presqt.targets.osf.utilities import get_osf_resource
from presqt.utilities import read_file, write_file


def osf_upload_metadata(token, resource_id, resource_main_dir, metadata_dict, project_id=None):
    """
    Upload the metadata of this PresQT action at the top level of the repo.

    Parameters
    ----------
    token : str
        The user's OSF token
    resource_id : str
        An id the upload is taking place on
    resource_main_dir : str
        The path to the bag to be uploaded
    metadata_dict : dict
        The metadata to be written to the project
    project_id : str
        The id of the project that has just been created
    """
    osf_instance = OSF(token)
    header = {'Authorization': 'Bearer {}'.format(token)}
    file_name = 'PRESQT_FTS_METADATA.json'
    encoded_metadata = json.dumps(metadata_dict, indent=4).encode('utf-8')
    put_url = "https://files.osf.io/v1/resources/{}/providers/osfstorage/"

    if resource_id:
        # Get the resource
        resource = get_osf_resource(resource_id, osf_instance)

        if resource.kind_name == 'project':
            if resource.parent_node_id is not None:
                project_id = resource.parent_node_id
            else:
                project_id = resource.id

        elif resource.kind_name == 'storage':
            project_id = resource.id.partition(':')[0]

        elif resource.kind_name == 'folder':
            # Find the project id for the given folder
            get_id_helper = requests.get(resource._endpoint, headers=header).json()['data'][
                'relationships']['target']['links']['related']['href']
            project_id = requests.get(get_id_helper, headers=header).json()['data']['id']

        # We need to find out if this project already has metadata associated with it.
        old_metadata_file = None
        project_data = osf_instance._get_all_paginated_data(
            'https://api.osf.io/v2/nodes/{}/files/osfstorage'.format(project_id))

        for data in project_data:
            if data['attributes']['name'] == file_name:
                old_metadata_file = requests.get(data['links']['move'], headers=header).content
                # Update the existing metadata
                updated_metadata = json.loads(old_metadata_file)

                # Loop through each 'action' in both metadata files and make a new list of them.
                joined_actions = [entry for entry in itertools.chain(updated_metadata['actions'],
                                                                     metadata_dict['actions'])]

                updated_metadata['actions'] = joined_actions
                encoded_metadata = json.dumps(updated_metadata, indent=4).encode('utf-8')

                # Now we need to update the metadata file with this updated metadata
                requests.put(data['links']['upload'], headers=header,
                             params={'kind': 'file'}, data=encoded_metadata)
                break

        # If it doesn't have an existing metadata file, we just make a new one.
        else:
            requests.put(put_url.format(project_id), headers=header, params={"name": file_name},
                         data=encoded_metadata)

    else:
        # If there is no resource_id, then this is a new project.
        requests.put(put_url.format(project_id), headers=header, params={"name": file_name},
                     data=encoded_metadata)
