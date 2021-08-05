from copy import Error
from argparse_prompt import PromptParser
import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from atlassian import Bitbucket
from . import bbcloud
from . import git
import threadly
import time
import urllib


# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s [%(levelname)s]: %(message)s",
    stream=sys.stdout,
    datefmt='%m-%d %H:%M')

logger = logging.getLogger(__name__)

def env_or(envvar, other):
    e = os.environ.get(envvar)
    if e is not None and e != "":
      return e
    else:
      return other


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
        '--threads', '-t',
        dest='threads',
        default=env_or('BBMIGRATE_THREADS', "5"),
        help='Number of threads to use (default: 5)')
    parser.add_argument(
        '--cloud-pass', '-cp',
        dest='cloud_pass',
        default=os.environ.get('BBMIGRATE_CLOUD_PASS'),
        help='Bitbucket Cloud password',
        secure=True)
    parser.add_argument(
        '--no-remove-repos', '-norm',
        dest='no_remove_repos',
        default=env_or('BBMIGRATE_NO_REMOVE_REPOS', "False"),
        help='Do not remove locally-cloned repos (default: false)')
    parser.add_argument(
        '--repo-path', '-rp',
        dest='repo_path',
        default=env_or('BBMIGRATE_REPO_PATH', "/tmp/bbmigrate"),
        help='base path to output the projects/repos (default: /tmp/bbmigrate')

    return parser

def main():

    args = create_parser().parse_args()
    threads = int(args.threads)
    EXEC = threadly.Scheduler(threads)

    server_domain = args.server_url
    if args.server_url[:8] == "https://":
        server_domain = args.server_url[8:]
    elif args.server_url[:7] == "http://":
        server_domain = args.server_url[7:]

    if os.environ.get('BBMIGRATE_IN_DOCKER') == "true":
        open("{}/.gitconfig".format(str(Path.home())), "w").write("[credential]\n	helper = store\n")
        open("{}/.git-credentials".format(str(Path.home())), "w").write("https://{}:{}@{}\nhttps://{}:{}@{}\n".format(args.server_user, urllib.parse.quote(args.server_pass), server_domain, args.cloud_user, urllib.parse.quote(args.cloud_pass), "bitbucket.org"))

    # setting up directory for repo clones
    dir_name = os.path.abspath(args.repo_path)
    clone_dir = dir_name
    try:
        if not os.path.isdir(clone_dir):
            os.mkdir(clone_dir)
    except OSError:
        logger.exception(f'Failed to create directory {clone_dir}')
        sys.exit(1)
    logger.info("Saving repos to path:{}".format(clone_dir))

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
        projects_gen = bitbucket_server.project_list()
    except Error:
        logger.exception(f'Failed to retrieve data from Bitbucket Server {args.server_url}')
        sys.exit(1)

    projects=[]
    logger.info(f'Retrieving projects and repos from Bitbucket Server {args.server_url}')
    for p in projects_gen:
        new_project_key = p['key'].replace("-", "")
        project_dir = os.path.join(clone_dir, new_project_key)
        p['project_dir']=project_dir
        p['new_project_key']=new_project_key
        projects.append(p)
        try:
            repos = bitbucket_server.repo_list(project_key=p['key'])
        except Error:
            logger.exception("Failed to gather repository list from Bitbucket Server project {}".format(p['name']))
            sys.exit(1)
        logger.info("Retrieving repositories from Bitbucket Server project {}".format(p['name']))
        p['repos']=[]
        for r in repos:
            new_repo_name = new_project_key.lower() + "." + r['slug'].lower()
            repo_dir = os.path.join(project_dir,r['slug'])
            new_repo_git = "https://bitbucket.org/" + args.workspace + "/" + new_repo_name + ".git"
            old_repo_git = ""
            for href in r['links']['clone']:
                if href['href'][:8] == "https://":
                    old_repo_git = href['href']
                    break
            r['old_repo_git']=old_repo_git
            r['new_repo_git']=new_repo_git
            r['new_repo_name']=new_repo_name
            r['repo_dir']=repo_dir
            p['repos'].append(r)
        p['repos']=sorted(p['repos'], key=lambda k: k['slug'])

    projects = sorted(projects, key=lambda k: k['key']) 

    processing = []
    logger.info("Duplicating projects on BBCloud")
    for p in projects:
        proj=p
        f = EXEC.schedule_with_future(bbcloud.duplicate_project, args=(args.cloud_user, args.cloud_pass, args.workspace, proj))
        processing.append(f)

    for lf in processing:
        lf.get()

    processing = []
    logger.info("Duplicating repos and cloning them on BBCloud")
    for project in projects:
        project_name = project['name']
        project_dir = project['project_dir']
        try:
            os.mkdir(project_dir)
        except:
            pass
        for repo in project['repos']:
            p = project
            r = repo
            f = EXEC.schedule_with_future(git.backupRepo, args=(args.cloud_user, args.cloud_pass, args.workspace, p, r, clone_dir, args.no_remove_repos))
            processing.append(f)
            if len(processing) > 10:
                for lf in processing:
                    lf.get()
                processing=[]
    for lf in processing:
        lf.get()

    # When it's all over, remove the tmp dir to keep things tidy
    if not args.no_remove_repos:
        try:
            os_system_string = "rm -rf " + clone_dir
            os.system(os_system_string)
        except OSError:
            logger.exception(f'Failed to remove temp directory {clone_dir}')
            sys.exit(1)
