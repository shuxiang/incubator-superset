#coding=utf8

import requests

r = requests.get('http://101.37.70.166:9013/report_builder/api/report_map/test-api', params={'company':'test'})
print r.content


r = requests.post('http://101.37.70.166:9013/report_builder/api/report_map/ACTION', json={'company':'test', 'api_name':'test1', 'report_id':1})
print r.content

r = requests.put('http://101.37.70.166:9013/report_builder/api/report_map/ACTION', json={'company':'test', 'api_name':'test1', 'report_id':1})
print r.content

r = requests.options('http://101.37.70.166:9013/report_builder/api/report_map/ACTION')
print r.content


# gunicorn superset restart

# mysql -hrm-bp1cjf58s56qf66o7.mysql.rds.aliyuncs.com --port 3306 -uroot -pVwms123404

# http://101.37.70.166:9013/savedqueryview/list/?_flt_0_user=1