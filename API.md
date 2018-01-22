===========================
Report API doc
===========================


1. 获取所有报表描述
===============

url: GET /report_builder/api/report
----------

描述: 获取所有可用的报表
----------

方法: GET
----------

参数: 无
----------

返回:
----------
```
[
    {
        id: 报表id
        created_on: 创建时间
        changed_on: 修改时间
        user_id: 创建者id
        db_id: database id
        label: 报表简名
        schema: database schema
        sql: sql
        description: 报表参数。见接口2
    }
]
```



2. 报表内容接口API
===============

url: POST /report_builder/api/report/<id>
----------

描述: 获取报表的返回内容
----------

方法: GET
----------

参数(GET): 
----------
获取报表接口内容; ajax GET query string --- page: current page, results_per_page: per page, `q`:
```
{
    restless style: https://flask-restless.readthedocs.io/en/stable/searchformat.html#attribute-between-two-values
}

```

返回(headers):
----------
x-total-count 总条数


返回(POST):
----------
```
{
    'data': 报表返回的数据, 列表
        [
            {
                field1: value1 字段一，值1 
                field2: value2 字段二，值2
                ... 
            },
            ... ...
        ]
    'id': 报表id
    'label': 报名名称
    'query_id': 查询id
    'limit': 最多返回数据条数
    'limit_reached': 有没有到达最多返回数据数
    'page': 当前页码
    'per_page':p 每页条数
    'pages': 总页数
    'total': 总条数
    'rows': 当前页条数
    'changed_on': 更新时间
    'displayfield_set': 返回的列名元信息
    'report_file': 下载链接, 指定参数t，返回csv或者xlsx
    'status': 成功返回'success'，失败返回其它
}
```


3. 报表内容下载接口API
===============

url: GET /report_builder/api/report/<id>/download/<query_id>
----------

描述: 获取报表的返回内容，可选下载为csv或xlsx，默认csv
----------

方法: GET
----------

参数(GET): 
----------
获取该报表接口描述
```
t 返回类型 csv/xlsx，不传t参数默认返回csv
```


返回(GET):
----------
csv或者xlsx文件



0. 其它未定或未实现事项
===============

国际化
----------

多租户
----------

权限认证
----------

部署更新
----------

ETL与多维数据分析
----------