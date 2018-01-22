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


2. 报表描述接口API
===============

url: GET /report_builder/api/report/<id>
----------

描述: 获取报表的描述
----------

方法: GET, POST
----------

参数(GET): 
----------
获取该报表接口描述
```
id 报表id 必须
```

返回(GET):
----------
```
{
    id: 报表id
    created_on: 创建时间
    changed_on: 修改时间
    user_id: 创建者id
    db_id: database id
    label: 报表简名
    schema: database schema
    sql: sql
    description: 报表参数
        "displayfield_set":[  # 要显示的字段元信息
            {"field":"字段名", "type":"类型，目前暂时有int float str date 四种", "help":"字段中文名"},
            ...
        ],
        "filterfield_set":[  #过滤器集合，即可以在每个报名里使用多个过滤器
            {"field":"字段名", "type":"操作类型，有 > < <= >= = like range 等这几种", "value1":"值1", "help":"帮助文字如：请输入货品代码/条码查询"},
            {"field":"created_at", "type":"range", "value1":"2017-09-26", "value2":"2017-09-27", "help":"库存时间: "} # 例子二
        ]
}

```

说明：
----------
displayfield_set 字段数据类型，暂定: int float str date
filerfield_set   过滤器操作类型，暂定: > < <= >= = like range, 其中range接受两个值


3. 报表内容接口API
===============

url: POST /report_builder/api/report/<id>
----------

描述: 获取报表的返回内容
----------

方法: POST
----------

参数(GET): 
----------
获取该报表接口描述
```
id 报表id 必须
_start query string 查询页，默认1
_limit query string 每页数量，默认暂定50
```

参数(POST): 
----------
获取报表接口内容; ajax post json; post也需要传递GET参数
```
{
    page: 查询页，默认1
    per_page: 每页数量，默认暂定50
    sort: [field, asc/desc], 默认为[]; [字段, 排序方向]
    filterfield_set: 过滤字段, 列表，支持多个
        [
            {
                field: 字段名
                type: 过滤类型
                value1: 参数1
                value2: 参数2
            }
        ]
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
    'sort': 排序
        [field, asc/desc]: [字段，排序方向]
    'changed_on': 更新时间
    'displayfield_set': 返回的列名元信息
    'report_file': 下载链接, 指定参数t，返回csv或者xlsx
    'status': 成功返回'success'，失败返回其它
}
```


4. 报表内容下载接口API
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