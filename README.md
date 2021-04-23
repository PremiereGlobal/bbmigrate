:sparkles:bbmigrate:sparkles:
========

A CLI for migrating projects and git repositories from Bitbucket Server to a given Bitbucket Cloud workspace.

## Requirements

1. Python >= 3.6
2. `git`
3. SSH access configured for Bitbucket Server and Bitbucket Cloud

`bbmigrate` uses `git clone` and `git push` commands to pull code from Bitbucket Server and push to Bitbucket Cloud and these commands use the SSH URL for the repos, hence the requirement for SSH access to be configured.

## Usage

`bbmigrate` just needs credentials to connect to both Bitbucket Server and Bitbucket Cloud, as well as the target workspace in Bitbucket Cloud where you want to put the migrated projects/repositories.

An example usage would be:

```
bbmigrate --server-url https://bitbucket.example.com --server-user john.doe --cloud-user johnnydoe123 --workspace mycompanyspace
```

### Arguments

`--server-url, -s`  
  - The URL for the Bitbucket Server instance (e.g. `-s https://bitbucket.mycompany.com`). Should include a port number if you're hosting on a port other than `80` or `443`.

`--server-user, -su`  
  - The username of a Bitbucket Server user with read access to all repositories in your instance.

`--server-pass, -sp`  
  - The password for the Bitbucket Server user.

`--workspace, -w`  
  - The name of the workspace in Bitbucket Cloud to migrate the projects and repositories to.

`--cloud-user, -cu`  
  - The username of a Bitbucket Cloud user with full read/write access to projects and repositories in the target workspace.

`--cloud-pass, -cp`  
  - The password for the Bitbucket Cloud user.
  - **NOTE**: it's recommended to create an ["App Password"](https://support.atlassian.com/bitbucket-cloud/docs/app-passwords/) in Bitbucket Cloud for this purpose.

All of the arguments are required, so `bbmigrate` will prompt you for values if you omit any. It won't display passwords typed into the `server-pass` or `cloud-pass` prompt, so it's advised to omit these flags from your command so as not to expose passwords in your shell or history.

If, however, you need to use the tool non-interactively `bbmigrate` will accept passwords via the `--server-pass` and `--cloud-pass` flags.

```
bbmigrate --server-url https://bitbucket.example.com --server-user john.doe --server-pass SuperS3cure123! --cloud-user johnnydoe123 --cloud-pass QeT5?JzY%T2N --workspace mycompanyspace
```

## Installation From Source

To install the package after you've cloned the repository, you'll want to run the following command from within the project directory:

```
$ pip install --user -e .
```

## Preparing for Development

Follow these steps to start developing with this project:

1. Ensure `pip` and `pipenv` are installed
2. Clone repository: `git clone git@github.com:PremiereGlobal/bbmigrate.git`
3. `cd` into the repository
4. Activate virtualenv: `pipenv shell`
5. Install dependencies: `pipenv install`