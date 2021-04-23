from setuptools import setup, find_packages

with open('README.md', encoding='UTF-8') as f:
    readme = f.read()

setup(
    name='bbmigrate',
    version='1.0.0',
    description='A utility for migrating projects and repos from Bitbucket Server to Bitbucket Cloud.',
    long_description=readme,
    author='Michael Davis',
    author_email="michael.davis1@pgi.com",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    python_requires='>=3.6',
    install_requires=[
        'argparse-prompt',
        'atlassian-python-api'
    ],
    entry_points={
        'console_scripts': [
            'bbmigrate=bbmigrate.cli:main'
        ]
    }
)