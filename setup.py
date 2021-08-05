from setuptools import setup, find_packages

readme = open('README.md', encoding='UTF-8').read()

setup(
    name='bbmigrate',
    version='2.0.0',
    description='A utility for migrating projects and repos from Bitbucket Server to Bitbucket Cloud.',
    long_description=readme,
    author='Michael Davis',
    author_email="michael.davis1@pgi.com",
    packages=['bbmigrate'],
    python_requires='>=3.6',
    install_requires=[
        'threadly',
        'argparse-prompt',
        'atlassian-python-api'
    ],
    entry_points={
        'console_scripts': [
            'bbmigrate=bbmigrate.main:main'
        ]
    }
)
