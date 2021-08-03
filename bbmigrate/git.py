import os, sys, subprocess
import logging
from . import bbcloud
import time, random

logger = logging.getLogger(__name__)

def backupRepo(username, password, workspace, project, repo, clone_dir, no_remove_repos):
    repo_name = repo['slug']
    new_repo_name = repo['new_repo_name']
    repo_dir = repo['repo_dir']
    old_repo_git = repo['old_repo_git']
    new_repo_git = repo['new_repo_git']

    cloneRepo(project, repo)
    bbcloud.duplicate_repo(username, password, workspace, project, repo)

    pushMirror(project, repo)

    if not no_remove_repos:
        logger.info(f'Removing local cloned repo for "{repo_name}" in {repo_dir}"...')
        try:
            os_system_string = "cd {} && rm -rf {}".format(clone_dir, repo_dir)
            os.system(os_system_string)
        except OSError:
            logger.exception(f'Failed to remove directory {repo_dir}')
            sys.exit(1)


def doGitCMD(name, cmd):
    while True:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        if out.find(b"fatal: unable to get credential ") == -1:
            return
        else:
            logger.info("Waiting for access to creds for:{}".format(name))
            time.sleep(random.randrange(0,1))




def cloneRepo(project, repo):
    repo_name = repo['slug']
    new_repo_name = repo['new_repo_name']
    repo_dir = repo['repo_dir']
    old_repo_git = repo['old_repo_git']
    new_repo_git = repo['new_repo_git']
    logger.info(f'Cloning repository {repo_name} to {repo_dir}...')
    try:
        if os.path.isdir(repo_dir):
            cmd = "cd {} && git -c http.postbuffer=500M -c http.maxrequestbuffer=100M fetch origin '*:*'".format(repo_dir)
            doGitCMD(new_repo_name, cmd)
        else:
            doGitCMD(new_repo_name, "cd {} && git -c http.postbuffer=500M -c http.maxrequestbuffer=100M clone --bare {} {}".format(project['project_dir'], old_repo_git, repo_dir))
    except Exception as e:
        logger.exception(f'Failed to clone repository "{repo_name}" from {old_repo_git}')

def pushMirror(project, repo):
    repo_name = repo['slug']
    new_repo_name = repo['new_repo_name']
    repo_dir = repo['repo_dir']
    old_repo_git = repo['old_repo_git']
    new_repo_git = repo['new_repo_git']
    logger.info(f'Mirroring repository "{repo_name}" to Bitbucket Cloud repository "{new_repo_name}"...')
    if not os.path.isfile("{}/packed-refs".format(repo_dir)):
        logger.info("Looks like an empty repo, skipping push...")
    else:
        try:
            doGitCMD(new_repo_name, "cd {} && git -c http.postbuffer=500M -c http.maxrequestbuffer=100M push --mirror {}".format(repo_dir, new_repo_git))
        except Exception as e:
            logger.exception(f'Failed to mirror repository "{repo_name}" to {new_repo_git}')




