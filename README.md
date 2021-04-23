bbmigrate
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

All of the arguments are required, so `bbmigrate` will prompt you for values if you omit any of them. `bbmigrate` will not display passwords typed into its prompt, so it's advised to use the above method and type your creds in at the prompt!
If you need to use the tool non-interactively, however, `bbmigrate` will accept passwords via the `--server-pass` and `--cloud-pass` arguments if you want to pass them in.

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