FROM python:3.8

RUN mkdir -m 700 /root/.ssh
RUN ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts

ADD . /bbmigrate
WORKDIR /bbmigrate
RUN pip install .

CMD /bbmigrate/forever.sh
