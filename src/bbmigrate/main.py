from copy import Error
from argparse_prompt import PromptParser
import os
import sys
import subprocess
import logging
from datetime import datetime
from atlassian import Bitbucket
from bbmigrate import bbcloud

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s [%(levelname)s]: %(message)s",
    stream=sys.stdout,
    datefmt='%m-%d %H:%M')

logger = logging.getLogger(__name__)


# Gathers command line args and prompts if any are missing
def create_parser():
    parser = PromptParser()
    parser.add_argument(
        '--server-url', '-s',
        dest='server_url',
        default=os.environ.get('BBMIGRATE_SERVER_URL'),
        help='URL of the Bitbucket Server')
    parser.add_argument(
        '--server-user', '-su',
        dest='server_user',
        default=os.environ.get('BBMIGRATE_SERVER_USER'),
        help='Bitbucket Server username')
    parser.add_argument(
        '--server-pass', '-sp',
        dest='server_pass',
        default=os.environ.get('BBMIGRATE_SERVER_PASS'),
        help='Bitbucket Server password',
        secure=True)
    parser.add_argument(
        '--workspace', '-w',
        dest='workspace',
        default=os.environ.get('BBMIGRATE_WORKSPACE'),
        help='Bitbucket Cloud workspace name')
    parser.add_argument(
        '--cloud-user', '-cu',
        dest='cloud_user',
        default=os.environ.get('BBMIGRATE_CLOUD_USER'),
        help='Bitbucket Cloud username (not e-mail)')
    parser.add_argument(
        '--cloud-pass', '-cp',
        dest='cloud_pass',
        default=os.environ.get('BBMIGRATE_CLOUD_PASS'),
        help='Bitbucket Cloud password',
        secure=True)
    parser.add_argument(
        '--no-remove-repos', '-norm',
        dest='no_remove_repos',
        default=os.environ.get('BBMIGRATE_NO_REMOVE_REPOS'),
        help='Do not remove locally-cloned repos (default: false)')
    return parser

def main():

    args = create_parser().parse_args()

    # setting up directory for repo clones
    dir_name = '/tmp/bbmigrate_' + str(datetime.now().strftime('%Y%m%d_%H%M%S'))
    clone_dir = dir_name
    try:
        os.mkdir(clone_dir)
    except OSError:
        logger.exception(f'Failed to create directory {clone_dir}')
        sys.exit(1)

    # initializing Bitbucket Server instance
    try:
        bitbucket_server = Bitbucket(
            url=args.server_url,
            username=args.server_user,
            password=args.server_pass)
    except Error:
        logger.exception(f'Unable to instantiate Bitbucker Server connection! One or more parameters may be missing or malformed.')
        sys.exit(1)

    try:
        projects = bitbucket_server.project_list()
    except Error:
        logger.exception(f'Failed to retrieve data from Bitbucket Server {args.server_url}')
        sys.exit(1)
    finally:
        logger.info(f'Retrieving projects from Bitbucket Server {args.server_url}')

    for project in projects:
        project_name = project['name']

        # Remove hyphens from project key as Bitbucket Cloud won't accept them
        new_project_key = project['key']
        new_project_key = new_project_key.replace("-", "")

        # Cloud API won't accept an empty description, so we have to "fill" it
        if bbcloud.check_description(project, 'description'):
            proj_desc = project['description']
        else:
            proj_desc = ""

        try:
            bbcloud.check_project_exists(args.cloud_user, args.cloud_pass, args.workspace, new_project_key)
        except Error:
            logger.exception(f'Unexpected error while locating project "{project_name}" in Bitbucket Cloud!')
            sys.exit(1)

        try:
            bbcloud.make_project(args.cloud_user, args.cloud_pass, args.workspace, new_project_key, proj_desc, project_name)
        except Error:
            logger.exception(f'Unexpected error while creating project "{project_name}" in Bitbucket Cloud!')
            sys.exit(1)

        try:
            repos = bitbucket_server.repo_list(project_key=project['key'])
        except Error:
            logger.exception(f'Failed to gather repository list from Bitbucket Server project "{project_name}".')
            sys.exit(1)
        finally:
            logger.info(f'Retrieving repositories from Bitbucket Server project "{project_name}".')

        for repo in repos:
            repo_name = repo['slug']
            new_repo_name = new_project_key.lower() + "." + repo['slug'].lower()
            repo_dir = clone_dir + "/" + new_project_key + "_" + repo['name']

            if "ssh://" in repo['links']['clone'][0]['href']:
                old_repo_git = (repo['links']['clone'][0]['href'])
            else:
                old_repo_git = (repo['links']['clone'][1]['href'])

            new_repo_git = "git@bitbucket.org:" + args.workspace + "/" + new_repo_name + ".git"

            # Cloud API won't accept an empty description, so we have to "fill" it
            if bbcloud.check_description(repo, 'description'):
                repo_desc = repo['description']
            else:
                repo_desc = ""
            try:
                bbcloud.check_repo_exists(args.cloud_user, args.cloud_pass, args.workspace, new_repo_name)
            except Error:
                logger.exception(f'Unexpected error while locating repo "{new_repo_name}" in Bitbucket Cloud!')
                sys.exit(1)

            try:
                bbcloud.make_repo(args.cloud_user, args.cloud_pass, args.workspace, new_repo_name, repo_desc, new_project_key)
            except:
                logger.exception(f'Unexpected error while creating repo "{new_repo_name}" in Bitbucket Cloud! Repo may not have been created.')
                sys.exit(1)

            logger.info(f'Cloning repository {repo_name} to {repo_dir}...')
            try:
                subprocess.run(['git', '-c', 'http.postbuffer=500M', '-c', 'http.maxrequestbuffer=100M', 'clone', '--bare', old_repo_git, repo_dir])
            except Error:
                logger.exception(f'Failed to clone repository "{repo_name}" from {old_repo_git}')
                sys.exit(1)

            logger.info(f'Mirroring repository "{repo_name}" to Bitbucket Cloud repository "{new_repo_name}"...')
            try:
                os.chdir(repo_dir)
            except OSError:
                logger.exception(f'Failed to change to directory {repo_dir}!')
                sys.exit(1)

            try:
                subprocess.run(['git', '-c', 'http.postbuffer=500M', '-c', 'http.maxrequestbuffer=100M', 'push', '--mirror', new_repo_git])
            except Error:
                logger.exception(f'Failed to mirror repository "{repo_name}" to {new_repo_git}')
                sys.exit(1)

            try:
                os.chdir(clone_dir)
            except Error:
                logger.exception(f'Failed to change to directory {clone_dir}!')
                sys.exit(1)

            if not args.no_remove_repos:
                logger.info(f'Removing local cloned repo for "{repo_name}" in {repo_dir}"...')
                try:
                    os_system_string = "rm -rf " + repo_dir
                    os.system(os_system_string)
                except OSError:
                    logger.exception(f'Failed to remove directory {repo_dir}')
                    sys.exit(1)

    # When it's all over, remove the tmp dir to keep things tidy
    try:
        os_system_string = "rm -rf " + clone_dir
        os.system(clone_dir)
    except OSError:
        logger.exception(f'Failed to remove temp directory {clone_dir}')
        sys.exit(1)
