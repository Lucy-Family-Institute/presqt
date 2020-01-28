import os
import requests
import re
from presqt.utilities import PresQTResponseException

def suave_upload_resource(token, resource_id, resource_main_dir,
                        hash_algorithm, file_duplicate_action):
    # SUAVE upload to file
    #  token is username
    # questions for username:
    #  * do we make these surveys ephemeral? in which case a presqt login account would
    #      share the information. A user would need to be redirected back to the appropriate url.
    #  * do we associated with a suave user, it could be pressqt.


    file_metadata_list = [
        # {
        #     # "actionRootPath": '',
        #     # "destinationPath": '',
        #     # "title": '',
        #     # "destinationHash": {} # hash_algorithm = 'md5'
        # }
    ]
    resources_ignored = []
    resources_updated = []

    # need to find a way in suave to do something like:
    # contributor_name = requests.get('https://api.osf.io/v2/users/me/',
    #                                 headers={'Authorization': 'Bearer {}'.format(token)}).json()[
    #                                     'data']['attributes']['full_name']

    action_metadata = {"destinationUsername": token}
    for path, subdirs, files in os.walk(resource_main_dir):
        print (os.walk(resource_main_dir))
        if not subdirs and not files:
            resources_ignored.append(path)
        for name in files:
            print (name)
            if (name.endswith(".csv")):
                views = "1110001" # defaults
                view ="grid" # default
                survey_url="https://suave-dev.sdsc.edu/main/file=zaslavsk_SDG_Indicators.csv"
                survey_name=name
                afile = os.path.join(path , name)
                username=token
                returnedUrl = upload_to_suave(survey_url,survey_name,username,afile,"null",views,view)
                # this needs to be passed back to user
            else:
                resources_ignored.append(name)

    return {
        'resources_ignored': resources_ignored,
        'resources_updated': resources_updated,
        'action_metadata': action_metadata,
        'file_metadata_list': file_metadata_list,
        'project_id': '22222'
    }

def validate_csv(file):
    return True

def tsv2csv():
    return None

def upload_to_suave(survey_url,survey_name,user,new_file,dzc_file, views, view):
    userAuth = os.environ.get('SUAVE_USER')
    userPass = os.environ.get('SUAVE_PASSWORD')
    print (os.environ)
    if (userAuth == None or userPass == None):
        raise PresQTResponseException ("Suave Upload: SUAVE_USER and SUAVE_PASSWORD must be set as environment variables")
    referer = survey_url.split("/main")[0] +"/"
    upload_url = referer + "uploadCSV"
    new_survey_url_base = survey_url.split(user)[0]
    print ("send to suave")
    csv = {"file": open(new_file, "rb")}

    validate_csv(csv) # returns true for now

    if dzc_file == 'null' or dzc_file == None:
        dzc_file=''

    upload_data = {
        'name': survey_name,
        'dzc': dzc_file,
        'user':user
    }
    headers = {
        'User-Agent': 'suave user agent',
        'referer': referer
    }

    r = requests.post(upload_url, files=csv, data=upload_data, headers=headers,auth=(userAuth,userPass))
    if r.status_code == 200:
        regex = re.compile('[^0-9a-zA-Z_]')
        s_url = survey_name
        s_url =  regex.sub('_', s_url)

        url = new_survey_url_base + user + "_" + s_url + ".csv" + "&views=" + views + "&view=" + view
        return(url)
    else:
        raise PresQTResponseException("Error creating new survey. Check if a survey with this name already exists.")


def suave_metadata_upload(token, project_id, metadata_dict):
    return
