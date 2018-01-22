#coding=utf8
import os


#---------------------------------------------------------
# Superset specific config
#---------------------------------------------------------
ROW_LIMIT = 5000
SUPERSET_WORKERS = 4

SUPERSET_WEBSERVER_PORT = 8088
#---------------------------------------------------------

#---------------------------------------------------------
# Flask App Builder configuration
#---------------------------------------------------------
# Your App secret key
SECRET_KEY = '\2\1thisismyscretkey\1\2\e\y\y\h'

# The SQLAlchemy connection string to your database backend
# This connection defines the path to the database that stores your
# superset metadata (slices, connections, tables, dashboards, ...).
# Note that the connection information to connect to the datasources
# you want to explore are managed directly in the web UI
##SQLALCHEMY_DATABASE_URI = 'sqlite:////path/to/superset.db'
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
if os.environ.get('SQLALCHEMY_DATABASE_URI', ''):
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', '')
else: # local
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:870129@localhost:3306/superset?charset=utf8'

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = False
# Add endpoints that need to be exempt from CSRF protection
WTF_CSRF_EXEMPT_LIST = []

# Set this API key to enable Mapbox visualizations
MAPBOX_API_KEY = ''

REPORT_PER_PAGE = 50

# from mods.simple_mod import simple_page
# BLUEPRINTS = [simple_page]