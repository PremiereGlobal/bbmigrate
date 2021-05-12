from atlassian.bitbucket import Cloud
import requests
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s [%(levelname)s]: %(message)s",
    stream=sys.stdout,
    datefmt='%m-%d %H:%M')

logger = logging.getLogger(__name__)

def check_description(dict, key):
    if key in dict:
        return True
    else:
        return False

def check_project_exists(username, password, workspace, key):

    bitbucket_cloud = Cloud(
        url = 'https://api.bitbucket.org/',
        username=username,
        password=password,
        cloud=True)
    try:
        bitbucket_cloud.workspaces.get(workspace).projects.get(key)
        exists = True
    except requests.HTTPError as e:
        if e.response.status_code in (404):
            exists = False
            logging.debug(f'Project "{key}" does not exist in Bitbucket Cloud workspace "{workspace}". Creating...')
        elif e.response.status_code in (401, 500, 503):
            logging.error('Failed to retrieve workspaces from Bitbucket Cloud! Service unavailable or user may not have permission.')
            raise e
    return exists

def check_repo_exists(username, password, workspace, slug):

    bitbucket_cloud = Cloud(
        url = 'https://api.bitbucket.org/',
        username=username,
        password=password,
        cloud=True)

    try:
        bitbucket_cloud.workspaces.get(workspace).repositories.get(slug)
        exists = True
    except requests.HTTPError as e:
        if e.response.status_code in (404):
            exists = False
            logging.debug(f'Repository "{slug}" does not exist in Bitbucket Cloud workspace "{workspace}". Creating...')
        elif e.response.status_code in (401, 500, 503):
            logging.error(f'Failed to retrieve repository "{slug}" from Bitbucket Cloud! Service unavailable or user may not have permission.')
            raise e
    return exists

def make_project(username, password, workspace, project_key, description, project_name):
    try:
        url = 'https://api.bitbucket.org/2.0/workspaces/' + workspace + '/projects/' + project_key
        requests.put(url, auth=(username, password), json={
                "name":project_name,
                "description":description,
                "is_private":True,})
    except requests.HTTPError as e:
        logging.error(f'Failed to create/update project "{project_name}" in Bitbucket Cloud workspace "{workspace}"! Service unavailable or user may not have permission.')
        if e.response.status_code in (401, 404, 500, 503):
            raise e
    return

def make_repo(username, password, workspace, slug, description, project_name):
    try:
        url = 'https://api.bitbucket.org/2.0/repositories/' + workspace + '/' + slug
        requests.put(url, auth=(username, password), json={
                "name":slug,
                "description":description,
                "is_private":True,
                "project": {
                    "key": project_name
                }})
    except requests.HTTPError as e:
        logging.error(f'Failed to create/update repository "{slug} in Bitbucket Cloud workspace "{workspace}"! Service unavailable or user may not have permission.')
        if e.response.status_code in (401, 404, 500, 503):
            raise e
    return