#coding=utf8

from superset.cli import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', threaded=True)