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
from functools import wraps

from flask import abort, flash, g, get_flashed_messages, redirect, Response
from flask import jsonify, request, url_for, make_response, send_file

from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from superset import (
    app, appbuilder, cache, db, results_backend, security, sm, sql_lab, utils,
    viz,
)
from .base import (
    api, BaseSupersetView, CsvResponse, DeleteMixin,
    generate_download_headers, get_error_msg, get_user_roles,
    json_error_response, SupersetFilter, SupersetModelView, YamlExportMixin,
)
from superset.models.sql_lab import Query, SavedQuery
import superset.models.core as models
from superset.utils import has_access, merge_extra_filters, QueryStatus
from flask_appbuilder.models.sqla.interface import SQLAInterface

from superset.models.custom_models import CompanyReportMap


CROS_HEADERS = {
    'Access-Control-Allow-Origin': "*",
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': '*'
    }

def cros_decorater(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        ret = func(*args, **kwargs)
        ret.headers.extend(CROS_HEADERS)
        return ret
    return decorated_view


#Get all reports:
#/report_builder/api/report GET
@app.route('/superset/report_builder/api/report', methods=('GET', 'OPTIONS'))
@cros_decorater
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
            #'sql':o.sql or '',
            'description':desc,
            })

    resp = jsonify(data)
    return resp

# created_on, changed_on, id, user_id, db_id, label, schema, sql, description, 
# displayfield_set
# filterfield_set

#Get report:
#/report_builder/api/report/<id> GET
@app.route('/superset/report_builder/api/report/<int:id>', methods=('GET', 'POST', 'OPTIONS'))
@cros_decorater
def get_one_report(id):
    return _get_one_report(id)

def _get_one_report(id):
    o = db.session.query(SavedQuery).filter_by(id=id).first()
    desc = {}
    try:
        desc = json.loads(o.description.encode('utf8'))
    except ValueError as e:
        print(e)

    if request.method == 'GET':
    #     resp = jsonify({'id':o.id, 
    #         'created_on':o.created_on.strftime('%Y-%m-%d'), 
    #         'changed_on':o.changed_on.strftime('%Y-%m-%d'),
    #         'user_id':o.user_id or '',
    #         'db_id':o.db_id or '',
    #         'label':o.label or '',
    #         'schema':o.schema or '',
    #         #'sql':o.sql or '',
    #         'description':desc,
    #         })
    #     return resp
    
    # elif request.method == 'POST':
        # qjson = request.json or {}
        # print request.json
        _q = json.loads(request.args.get('q', "{}"))
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('results_per_page', app.config.get('REPORT_PER_PAGE', 50)))


        _filters = _q.get('filters', [])
        _order_by = _q.get('order_by', [])
        _group_by = _q.get('group_by', [])
        _single = _q.get('single', False)

        sql = o.sql
        database_id = o.db_id
        schema = o.schema
        label = o.label

        session = db.session()
        mydb = session.query(models.Database).filter_by(id=database_id).first()


        hkey = get_hash_key()
        # # parse config; filters and fields and sorts
        # # order by [{"field": <fieldname>, "direction": <directionname>}]
        qsort = ", ".join(["_.%s %s"%(ob['field'], ob['direction']) for ob in _order_by])
        sort = (" order by " + qsort) if qsort else ""
        # [{"name": <fieldname>, "op": <operatorname>, "val": <argument>}]

        fs = []
        for f in _filters:
            if  'and' in f:
                _where = " and ".join([gen_where_filter(subf) for subf in f['and']])
                fs.append("( %s )"%_where)
            elif 'or' in f:
                _where = " or ".join([gen_where_filter(subf) for subf in f['or']])
                fs.append("( %s )"%_where)
            else:
                fs.append(gen_where_filter(f))

        where = " where "+(" and ".join(fs)) if fs else ""

        # # sql can't end with `;` , complicated sql use select .. as ..

        count_sql = "SELECT count(1) as num FROM (%s) _ %s"%(sql,where)
        sql = "SELECT * FROM (%s) _ %s %s LIMIT %s,%s"%(sql, where, sort, (page-1)*per_page, per_page) 

        print sql, '============='

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
                user_id=1, #int(g.user.get_id()),
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
                user_id=1, #int(g.user.get_id()),
                client_id=hkey[0]+hkey[1],
            )
            session.add(cquery)

            session.flush()
            session.commit()
            query_id = query.id
            cquery_id =cquery.id

            data = sql_lab.get_sql_results(
                        query_id=query_id, return_results=True,
                        template_params={})

            cdata = sql_lab.get_sql_results(
                        query_id=cquery_id, return_results=True,
                        template_params={})

            if data['status'] == 'failed':
                resp = jsonify(data)
                resp.headers['x-total-count'] = '0'
                return resp

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
                    'sort':_order_by,
                    'changed_on':data['query']['changed_on'],
                    'displayfield_set': desc['displayfield_set'],
                    'q': _q,
                    'report_file': url_for('download_one_report', id=id, query_id=data['query_id']),
                    'status': 'success',
                })

            resp.headers['x-total-count'] = str(cdata['data'][0]['num'])
            return resp
    

    resp = Response('OK')
    return resp

def gen_where_filter(f):

    # ==, eq, equals, equals_to
    # !=, neq, does_not_equal, not_equal_to
    # >, gt, <, lt
    # >=, ge, gte, geq, <=, le, lte, leq
    # in, not_in
    # is_null, is_not_null
    # like
    # has
    # any
    op = f['op']
    name = f['name']
    val = f['val']

    ret = ''
    if op == 'like':
        #ret = "_.%(name)s like '%%%(val)s%%'"%f
        ret = "_.%(name)s like '%(val)s'"%f
    elif op in ('==', 'eq', 'equals', 'equals_to', '='):
        ret = "_.%(name)s = '%(val)s'" %f
    elif op in ('!=', 'neq', 'does_not_equal', 'not_equal_to'):
        ret = "_.%(name)s != '%(val)s'" %f
    elif op in ('>=', 'ge', 'gte', 'geq'):
        ret = "_.%(name)s >= '%(val)s'" %f
    elif op in ('>', 'gt'):
        ret = "_.%(name)s > '%(val)s'" %f
    elif op in ('<=', 'le', 'lte', 'leq'):
        ret = "_.%(name)s <= '%(val)s'" %f
    elif op in ('<', 'lt'):
        ret = "_.%(name)s < '%(val)s'" %f
    elif op == 'in':
        ret = "_.%(name)s in %(val)s" %f
    elif op == 'not_in':
        ret = "_.%(name)s not in %(val)s" %f
    elif op == 'is_null':
        ret = "_.%(name)s is null" %f
    elif op == 'is_not_null':
        ret = "_.%(name)s is not null" %f
    # has any not support
    return ret

# Exporting using xlsx
# GET request on /report_builder/report/<id>/download_xlsx/
@app.route('/superset/report_builder/api/report/<int:id>/download/<int:query_id>', methods=('GET', 'OPTIONS'))
@cros_decorater
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

    return ret


# New Style Report
@app.route('/superset/report_builder/api/report_map/<name>', methods=('GET', 'OPTIONS', 'POST', 'PUT'))
@cros_decorater
def report_map_api(name='ACTION'):
    if request.method == 'POST':
        req = request.json
        company = req['company']
        api_name = req['api_name']

        if db.session.query(CompanyReportMap).filter_by(company=company, api_name=api_name).count() > 0:
            resp = Response('exist report of company: %s , api name: %s '%(company, api_name))
            resp.status_code = 422
            return resp

        crm = CompanyReportMap()
        crm.company = company
        crm.api_name = api_name
        crm.remark = req.get('remark', '')
        crm.report_id = req['report_id']

        db.session.add(crm)
        db.session.commit()

        return jsonify(req)

    elif request.method == 'PUT':
        req = request.json
        company = req['company']
        api_name = req['api_name']

        crm = db.session.query(CompanyReportMap).filter_by(company=company, api_name=api_name).first()
        if not crm:
            esp = Response('Not Found')
            resp.status_code = 404
            return resp
        else:
            crm.report_id = req['report_id']
            crm.remark = req.get('remark', crm.remark)
        db.session.commit()

        return jsonify(req)

    elif request.method == 'OPTIONS':
        res = [{'company':c.company, 'api_name':c.api_name, 'report_id':c.report_id, 'remark':c.remark} for c in db.session.query(CompanyReportMap).all()]
        return jsonify(res)
    # GET
    company = request.args.get('company', '') or request.args.get('company_id', '')
    o = db.session.query(CompanyReportMap).filter_by(company=company, api_name=name).first()
    if not o:
        resp = Response('Not Found')
        resp.status_code = 404
        return resp

    return _get_one_report(o.report_id)



# custom model view
class CompanyReportMapView(SupersetModelView, DeleteMixin):  # noqa
    datamodel = SQLAInterface(CompanyReportMap)

    list_title = _('List CompanyReportMap')
    show_title = _('Show CompanyReportMap')
    add_title = _('Add CompanyReportMap')
    edit_title = _('Edit CompanyReportMap')

    list_columns = ['id', 'company', 'api_name', 'report_id', 'remark']
    order_columns = [
        'company', 'api_name', 'report_id']
    search_exclude_columns = (
        'company', 'api_name', 'report_id',)
    add_columns = ['company', 'api_name', 'report_id', 'remark']
    edit_columns = add_columns
    show_columns = list_columns

appbuilder.add_view(
    CompanyReportMapView,
    'CompanyReportMap',
    label=__('CompanyReportMapView'),
    icon='fa-database',
    category='Sources',
    category_label=__('Sources'),
    category_icon='fa-database',)
# end custom model view


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


# # SELECT[ALL|DISTINCT|DISTINCTROW|TOP]
#     {*|talbe.*|[table.]field1[AS alias1][,[table.]field2[AS alias2][,…]]}
#     FROM tableexpression[,…][IN externaldatabase]
#     [WHERE…]
#     [GROUP BY…]
#     [HAVING…]
#     [ORDER BY…]


# SELECT [ ALL | DISTINCT [ ON ( expression [, ...] ) ] ]
#     * | expression [ AS output_name ] [, ...]
#     [ FROM from_item [, ...] ]
#     [ WHERE condition ]
#     [ GROUP BY expression [, ...] ]
#     [ HAVING condition [, ...] ]
#     [ { UNION | INTERSECT | EXCEPT } [ ALL ] select ]
#     [ ORDER BY expression [ ASC | DESC | USING operator ] [, ...] ]
#     [ FOR UPDATE [ OF tablename [, ...] ] ]
#     [ LIMIT { count | ALL } ]
#     [ OFFSET start ]