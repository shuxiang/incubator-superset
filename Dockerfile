FROM ubuntu:latest
MAINTAINER Shengjiu Liu <shliu@vwms.cn>

# install tools
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y libmysqld-dev
RUN apt-get install -y mysql-client

# install nodejs yarn npm
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.8/install.sh | bash
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash
RUN apt-get install -y nodejs
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg |  apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" |  tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update 
RUN apt-get install -y yarn

# install python packages
RUN curl -o- https://bootstrap.pypa.io/get-pip.py | python
RUN pip install --upgrade pip
RUN pip install Flask
RUN pip install Flask-Login
RUN pip install Flask-SQLALchemy
RUN pip install Flask-Script
RUN pip install PyMySQL
RUN pip install Flask-Migrate
RUN pip install Flask-RESTful
RUN pip install Flask-Cache
RUN pip install Flask-Principal
RUN pip install requests
RUN pip install xmltodict
RUN pip install xlsxwriter

# install relative modules
RUN apt-get install -y build-essential 
RUN apt-get install -y libssl-dev 
RUN apt-get install -y libffi-dev 
RUN apt-get install -y python-dev 
RUN apt-get install -y libsasl2-dev 
RUN apt-get install -y libldap2-dev
RUN pip install superset==0.22.1
RUN pip uninstall -y superset


RUN mkdir -p /opt/superset
COPY . /opt/superset/
WORKDIR /opt/superset/superset/assets
RUN yarn
RUN yarn run build


# install gunicorn
RUN pip install greenlet
RUN pip install eventlet
RUN pip install gevent
RUN pip install gunicorn

#CMD
WORKDIR /opt/superset
#ENTRYPOINT python /opt/superset/manage.py
ENTRYPOINT gunicorn manage:app -c gun.conf

# port
EXPOSE 5000
EXPOSE 8088


## Create an admin user (you will be prompted to set username, first and last name before setting a password)
#fabmanager create-admin --app superset
## Initialize the database
#superset db upgrade
## Load some data to play with
#superset load_examples
## Create default roles and permissions
#superset init