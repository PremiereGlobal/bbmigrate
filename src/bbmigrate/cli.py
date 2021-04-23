from argparse_prompt import PromptParser

def create_parser():
    parser = PromptParser()
    parser.add_argument(
        '--server-url', '-s',
        dest='server_url',
        help='URL of the Bitbucket Server'
    )
    parser.add_argument(
        '--server-user', '-su',
        dest='server_user',
        help='Bitbucket Server username'
    )
    parser.add_argument(
        '--server-pass', '-sp',
        dest='server_pass',
        help='Bitbucket Server password',
        secure=True
    )
    parser.add_argument(
        '--workspace', '-w',
        dest='workspace',
        help='Bitbucket Cloud workspace name'
    )
    parser.add_argument(
        '--cloud-user', '-cu',
        dest='cloud_user',
        help='Bitbucket Cloud username (not e-mail)'
    )
    parser.add_argument(
        '--cloud-pass', '-cp',
        dest='cloud_pass',
        help='Bitbucket Cloud password',
        secure=True
    )
    return parser

def main():
    import os
    import time
    import subprocess
    from datetime import datetime
    from atlassian import Bitbucket
    from bbmigrate import bbcloud

    args = create_parser().parse_args()

    # setting up directory for repo clones
    dir_name = '/tmp/bbmigrate_' + str(datetime.now().strftime('%Y%m%d_%H%M%S'))
    clone_dir = dir_name
    os.mkdir(clone_dir)

    # initializing Bitbucket Server instance
    bitbucket_server = Bitbucket(
        url = args.server_url,
        username = args.server_user,
        password = args.server_pass
    )

    print(f'Retrieving projects from Bitbucket Server {args.server_url}')
    projects = bitbucket_server.project_list()


    for project in projects:

        # Remove hyphens from project key as Bitbucket Cloud won't accept them
        new_project_key = project['key']
        new_project_key = new_project_key.replace("-", "")
        
        # Cloud API won't accept an empty description, so we have to "fill" it
        if bbcloud.check_description(project, 'description'):
            proj_desc = project['description']
        else:
            proj_desc = ""

        if bbcloud.check_project_exists(args.cloud_user, args.cloud_pass, args.workspace, new_project_key) == False:
            print(f'Creating project {project["name"]} in Bitbucket Cloud...')
        else:
            print(f'Project {project["name"]} already exists in Bitbucket Cloud. Updating...')
        
        bbcloud.make_project(args.cloud_user, args.cloud_pass, args.workspace, new_project_key, proj_desc, project['name'])

        print(f'Retrieving repositories from Bitbucket Server project {project["name"]}')
        repos = bitbucket_server.repo_list(project_key=project['key'])

        for repo in repos:
            new_repo_name = new_project_key.lower() + "." + repo['slug'].lower()

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

            if bbcloud.check_repo_exists(args.cloud_user, args.cloud_pass, args.workspace, new_repo_name) == False:
                print(f'Creating repository {new_repo_name} in Bitbucket Cloud...')
            else:
                print(f'Repository {new_repo_name} already exists in Bitbucket Cloud. Updating...')

            bbcloud.make_repo(args.cloud_user, args.cloud_pass, args.workspace, new_repo_name, repo_desc, new_project_key)

            repo_dir = clone_dir + "/" + new_project_key + "_" + repo['name']
            print(repo_dir)

            print(f'Cloning repository {repo["slug"]}...')
            subprocess.run(['git', '-c', 'http.postbuffer=500M', '-c', 'http.maxrequestbuffer=100M', 'clone', '--bare', old_repo_git, repo_dir])

            print(f'Mirroring repository {repo["slug"]} to Bitbucket Cloud...')
            os.chdir(repo_dir)
            subprocess.run(['git', '-c', 'http.postbuffer=500M', '-c', 'http.maxrequestbuffer=100M', 'push', '--mirror', new_repo_git])
            os.chdir(clone_dir)

            print(f'Removing local repo for {repo["slug"]}...')
            os_system_string = "rm -rf " + repo_dir
            os.system(os_system_string)

    # When it's all over, remove the tmp dir
    os_system_string = "rm -rf " + clone_dir
    os.system(clone_dir)