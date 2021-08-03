from atlassian.bitbucket import Cloud
import requests
import sys
import logging
import time
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s [%(levelname)s]: %(message)s",
    stream=sys.stdout,
    datefmt='%m-%d %H:%M')

logger = logging.getLogger(__name__)

def check_project_exists(username, password, workspace, key):

    bitbucket_cloud = Cloud(
        url = 'https://api.bitbucket.org/',
        username=username,
        password=password,
        cloud=True)
    exists = False
    while True:
        try:
            bitbucket_cloud.workspaces.get(workspace).projects.get(key)
            exists = True
        except requests.HTTPError as e:
            if e.response.status_code in (404,):
                exists = False
                logging.debug(f'Project "{key}" does not exist in Bitbucket Cloud workspace "{workspace}". Creating...')
            elif e.response.status_code in (401, 500, 503):
                logging.error('Failed to retrieve workspaces from Bitbucket Cloud! Service unavailable or user may not have permission.')
                raise e
            elif e.response.status_code in (429,):
              logging.info("Got Throttle checking:"+slug)
              time.sleep(random.randrange(5.0,10.0))
              continue
        return exists

def check_repo_exists(username, password, workspace, slug):

    bitbucket_cloud = Cloud(
        url = 'https://api.bitbucket.org/',
        username=username,
        password=password,
        cloud=True)
    exists = False
    while True:
      try:
          bitbucket_cloud.workspaces.get(workspace).repositories.get(slug)
          exists = True
      except requests.HTTPError as e:
          if e.response.status_code in (404,):
              exists = False
              logging.debug(f'Repository "{slug}" does not exist in Bitbucket Cloud workspace "{workspace}". Creating...')
          elif e.response.status_code in (401, 500, 503):
              logging.error(f'Failed to retrieve repository "{slug}" from Bitbucket Cloud! Service unavailable or user may not have permission.')
              raise e
          elif e.response.status_code in (429,):
            logging.info("Got Throttle checking:"+slug)
            time.sleep(random.randrange(5.0,10.0))
            continue
      return exists

def make_project(username, password, workspace, project_key, description, project_name):
    while True:
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
            elif e.response.status_code in (429,):
                logging.info("Got Throttle checking:"+slug)
                time.sleep(random.randrange(5.0,10.0))
                continue
        return

def make_repo(username, password, workspace, slug, description, project_name):
    while True:
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
            elif e.response.status_code in (429,):
                logging.info("Got Throttle checking:"+slug)
                time.sleep(random.randrange(5.0,10.0))
                continue
        return


def duplicate_repo(username, password, workspace, project, repo):
    if check_repo_exists(username, password, workspace, repo['new_repo_name']):
        logger.info("Repo:{} already exists, skipping".format(repo['new_repo_name']))
        return

    if 'description' in repo:
        repo_desc = repo['description']
    else:
        repo_desc = ""
    try:
        make_repo(username, password, workspace, repo['new_repo_name'], repo_desc, project['new_project_key'])
    except:
        logger.exception(f'Unexpected error while creating repo "{new_repo_name}" in Bitbucket Cloud! Repo may not have been created.')
        sys.exit(1)




def duplicate_project(username, password, workspace, project):
    project_name = project['name']
    new_project_key = project['key'].replace("-", "")

    if check_project_exists(username, password, workspace, new_project_key):
        logger.info(f'Project "{project_name}" already exists, skipping')
        return 

    if 'description' in project:
        proj_desc = project['description']
    else:
        proj_desc = ""

    try:
        make_project(username, password, workspace, new_project_key, proj_desc, project_name)
    except Exception as e:
        logger.exception(f'Unexpected error while creating project "{project_name}" in Bitbucket Cloud!: {e}')
        sys.exit(1)

