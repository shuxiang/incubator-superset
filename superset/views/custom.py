#coding=utf8

from datetime import datetime
import functools
import json
import logging
import traceback
import uuid
from pprint import pprint
import csv
import StringIO
import xlsxwriter

from flask import abort, flash, g, get_flashed_messages, redirect, Response
from flask import jsonify, request, url_for, make_response, send_file


from superset import (
    app, appbuilder, cache, db, results_backend, security, sm, sql_lab, utils,
    viz,
)
from superset.models.sql_lab import Query, SavedQuery
import superset.models.core as models
from superset.utils import has_access, merge_extra_filters, QueryStatus
from flask_appbuilder.models.sqla.interface import SQLAInterface

#Get all reports:
#/report_builder/api/report GET
@app.route('/report_builder/api/report', methods=('GET', 'OPTIONS'))
def get_all_report():
    #sq = SavedQuery.query.all()
    dm = SQLAInterface(SavedQuery)
    #sq = dm.query.all()
    sq = db.session.query(SavedQuery).all()
    data = []
    for o in sq:
        desc = {}
        try:
            desc = json.loads(o.description)
        except ValueError:
            pass
        data.append({'id':o.id, 
            'created_on':o.created_on.strftime('%Y-%m-%d'), 
            'changed_on':o.changed_on.strftime('%Y-%m-%d'),
            'user_id':o.user_id or '',
            'db_id':o.db_id or '',
            'label':o.label or '',
            'schema':o.schema or '',
            'sql':o.sql or '',
            'description':desc,
            })

    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = "*"
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Headers'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = '*'
    return resp

# created_on, changed_on, id, user_id, db_id, label, schema, sql, description, 
# displayfield_set
# filterfield_set

#Get report:
#/report_builder/api/report/<id> GET
@app.route('/report_builder/api/report/<int:id>', methods=('GET', 'POST', 'OPTIONS'))
def get_one_report(id):
    o = db.session.query(SavedQuery).filter_by(id=id).first()
    desc = {}
    try:
        desc = json.loads(o.description)
    except ValueError:
        pass

    if request.method == 'GET':
        resp = jsonify({'id':o.id, 
            'created_on':o.created_on.strftime('%Y-%m-%d'), 
            'changed_on':o.changed_on.strftime('%Y-%m-%d'),
            'user_id':o.user_id or '',
            'db_id':o.db_id or '',
            'label':o.label or '',
            'schema':o.schema or '',
            'sql':o.sql or '',
            'description':desc,
            })
        resp.headers['Access-Control-Allow-Origin'] = "*"
        resp.headers['Access-Control-Allow-Credentials'] = 'true'
        resp.headers['Access-Control-Allow-Headers'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = '*'
        return resp
    
    elif request.method == 'POST':
        qjson = request.json

        sql = o.sql
        database_id = o.db_id
        schema = o.schema
        label = o.label

        session = db.session()
        mydb = session.query(models.Database).filter_by(id=database_id).first()

        # paginate
        page = qjson.get('page', 1) 
        per_page = qjson.get('per_page', app.config['REPORT_PER_PAGE']) 
        

        hkey = get_hash_key()

        # # parse config; filters and fields and sorts
        # qsort = ["ds","desc"]
        qsort = qjson.get('sort',[])
        sort = " order by _.%s %s"%(qsort[0], qsort[1]) if qsort else ""
        # date transfer problem solve after
        #filters = [ {"field":"ds", "type":"range", "value1":"2016-01-01", "value2":"2017-01-03", "help":u"date字段"} ]
        filters = qjson.get('filterfield_set', [])

        fs = []
        for f in filters:
            if f['type'] == 'range':
                fs.append("(_.%(field)s >= '%(value1)s' and _.%(field)s < '%(value2)s')"%f)
            elif f['type'] == 'like':
                fs.append("_.%(field)s like '%%%(value1)s%%'"%f)
            else:
                fs.append("_.%(field)s %(type)s '%(value1)s'")

        where = " where "+(" and ".join(fs)) if fs else ""

        # count_sql = "SELECT count(1) as num FROM (%s) _"%sql
        # sql = "SELECT * FROM (%s) _ LIMIT %s,%s"%(sql, (page-1)*per_page, per_page) 
        # # sql can't end with `;` , complicated sql use select .. as ..

        count_sql = "SELECT count(1) as num FROM (%s) _ %s"%(sql,where)
        sql = "SELECT * FROM (%s) _ %s %s LIMIT %s,%s"%(sql, where, sort, (page-1)*per_page, per_page) 

        if True:
            query = Query(
                database_id=int(database_id),
                limit=1000000,#int(app.config.get('SQL_MAX_ROW', None)),
                sql=sql,
                schema=schema,
                select_as_cta=False,
                start_time=utils.now_as_float(),
                tab_name=label,
                status=QueryStatus.RUNNING,
                sql_editor_id=hkey[0]+hkey[1],
                tmp_table_name='',
                user_id=int(g.user.get_id()),
                client_id=hkey[2]+hkey[3],
            )
            session.add(query)

            cquery = Query(
                database_id=int(database_id),
                limit=1000000,#int(app.config.get('SQL_MAX_ROW', None)),
                sql=count_sql,
                schema=schema,
                select_as_cta=False,
                start_time=utils.now_as_float(),
                tab_name=label,
                status=QueryStatus.RUNNING,
                sql_editor_id=hkey[0]+hkey[1],
                tmp_table_name='',
                user_id=int(g.user.get_id()),
                client_id=hkey[0]+hkey[1],
            )
            session.add(cquery)

            session.flush()
            db.session.commit()
            query_id = query.id
            cquery_id =cquery.id


            data = sql_lab.get_sql_results(
                        query_id=query_id, return_results=True,
                        template_params={})

            cdata = sql_lab.get_sql_results(
                        query_id=cquery_id, return_results=True,
                        template_params={})

            resp = jsonify({
                    'data':data['data'],
                    'id':id,
                    'label':label,
                    'query_id':data['query_id'],
                    'limit':data['query']['limit'],
                    'limit_reached':False,
                    'page':page,
                    'per_page':per_page,
                    'pages': get_pages(cdata['data'][0]['num'], per_page),
                    'total':cdata['data'][0]['num'],
                    'rows':data['query']['rows'],
                    'sort':qsort,
                    'changed_on':data['query']['changed_on'],
                    'displayfield_set': desc['displayfield_set'],
                    'report_file': url_for('download_one_report', id=id, query_id=data['query_id']),
                    'status': 'success',
                })

            resp.headers['Access-Control-Allow-Origin'] = "*"
            resp.headers['Access-Control-Allow-Credentials'] = 'true'
            resp.headers['Access-Control-Allow-Headers'] = '*'
            resp.headers['Access-Control-Allow-Methods'] = '*'
            return resp
    

    resp = Response('OK')
    resp.headers['Access-Control-Allow-Origin'] = "*"
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Headers'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = '*'
    return resp


# Exporting using xlsx
# GET request on /report_builder/report/<id>/download_xlsx/
@app.route('/report_builder/api/report/<int:id>/download/<int:query_id>' method=('GET', 'OPTIONS'))
def download_one_report(id, query_id):
    o = db.session.query(SavedQuery).filter_by(id=id).first()
    desc = {}
    try:
        desc = json.loads(o.description)
    except ValueError:
        pass

    data = sql_lab.get_sql_results(
                        query_id=query_id, return_results=True,
                        template_params={})


    field = [t['field'] for t in desc['displayfield_set']]
    title = [t['help'] for t in desc['displayfield_set']]#help, undefined
    table = [[d[f] for f in field] for d in data['data']]

    filetype = request.args.get('t', 'csv')
    if filetype == 'csv':
        ret = gen_csv(title, table, o.label)
    elif filetype == 'xlsx':
        ret = gen_xlsx(title, table, o.label)
    #else:
    #    ret = jsonify({'displayfield_set': desc['displayfield_set'], 'data': data['data']})

    resp = ret
    resp.headers['Access-Control-Allow-Origin'] = "*"
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Headers'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = '*'
    return resp

#================= utils =====================
code_map = ( 
      'a' , 'b' , 'c' , 'd' , 'e' , 'f' , 'g' , 'h' , 
      'i' , 'j' , 'k' , 'l' , 'm' , 'n' , 'o' , 'p' , 
      'q' , 'r' , 's' , 't' , 'u' , 'v' , 'w' , 'x' , 
      'y' , 'z' , '0' , '1' , '2' , '3' , '4' , '5' , 
      '6' , '7' , '8' , '9' , 'A' , 'B' , 'C' , 'D' , 
      'E' , 'F' , 'G' , 'H' , 'I' , 'J' , 'K' , 'L' , 
      'M' , 'N' , 'O' , 'P' , 'Q' , 'R' , 'S' , 'T' , 
      'U' , 'V' , 'W' , 'X' , 'Y' , 'Z'
      ) 
def get_hash_key():
    hkeys = [] 
    hex = str(uuid.uuid4()).replace('-','')
    for i in xrange(0, 4): 
        n = int(hex[i*8:(i+1)*8], 16) 
        v = [] 
        e = 0
        for j in xrange(0, 4): 
            x = 0x0000003D & n 
            e |= ((0x00000002 & n ) >> 1) << j 
            v.insert(0, code_map[x]) 
            n = n >> 5
        e |= n << 4
        v.insert(0, code_map[e & 0x0000003D]) 
        hkeys.append(''.join(v)) 
    return hkeys 

get_pages = lambda x,p:x/p+1 if x%p > 0 else x/p

def gen_csv(title, table, fname):
    si = StringIO.StringIO()
    cw = csv.writer(si)
    # type transfer problem, correct it after
    data = [[c.encode('utf8') if type(c) is unicode else c for c in r] for r in [title]+table]
    cw.writerows(data)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=%s.csv"%fname
    output.headers["Content-type"] = "text/csv"
    return output

def gen_xlsx(title, table, fname):
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    
    row = 0
    col = 0
    for arow in [title]+table:
        for c, colm in enumerate(arow):
            # type transfer problem, correct it after
            worksheet.write(row, col+c, unicode(colm))
        row += 1


    workbook.close()
    output.seek(0)
    
    return send_file(output, 
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        as_attachment=True, attachment_filename='%s.xlsx'%fname)