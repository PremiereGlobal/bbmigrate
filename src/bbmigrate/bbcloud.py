from atlassian.bitbucket import Cloud
import requests

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
        cloud=True
    )
    try:
        bitbucket_cloud.workspaces.get(workspace).projects.get(key)
        exists = True
    except requests.HTTPError as e:
        if e.response.status_code in (401, 404):
            exists = False
    return exists

def check_repo_exists(username, password, workspace, slug):

    bitbucket_cloud = Cloud(
        url = 'https://api.bitbucket.org/',
        username=username,
        password=password,
        cloud=True
    )

    try:
        bitbucket_cloud.workspaces.get(workspace).repositories.get(slug)
        exists = True
    except requests.HTTPError as e:
        if e.response.status_code in (401, 404):
            exists = False
    return exists

def make_project(username, password, workspace, project_key, description, project_name):
    try:
        url = 'https://api.bitbucket.org/2.0/workspaces/' + workspace + '/projects/' + project_key
        requests.put(url, auth=(username, password), json={
                "name":project_name,
                "description":description,
                "is_private":True,
            }
        )
    except requests.HTTPError as e:
        if e.response.status_code in (401, 404):
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
                }
            }
        )
    except requests.HTTPError as e:
        if e.response.status_code in (401, 404):
            raise e
    return