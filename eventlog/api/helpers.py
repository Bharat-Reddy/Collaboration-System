from . import settings
import datetime
import django
from . import exceptions
from .essearch import SearchElasticSearch
from .. import utils

LOG_CLASS = "API-HELPERS"
def extract_time_keys(request):
    delta = 10
    dic = {}
    tm = None
    bef_tm = None
    try:
        val = request.GET.__getitem__('before')
        tm = datetime.datetime.strptime(val, '%Y-%m-%dT%H:%M:%S')
        bef_tm = tm
        tm = tm.strftime('%Y-%m-%d %H:%M:%S')
    except KeyError as e:
        tm = datetime.datetime.now()
        bef_tm = tm
        tm = tm.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        raise exceptions.BadTimeFormat
    dic['before'] = tm
    tm = None
    utils.ilog(LOG_CLASS, "Before time is: {!s}".format(bef_tm), mode="DEBUG")
    try:
        val = request.GET.__getitem__('after')
        tm = datetime.datetime.strptime(val, '%Y-%m-%dT%H:%M:%S')
        tm = tm.strftime('%Y-%m-%d %H:%M:%S')
    except KeyError as e:
        tm = (bef_tm - datetime.timedelta(days = delta)).strftime('%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        raise exceptions.BadTimeFormat
    dic['after'] = tm
    return dic 

def extract_field_keys(request):
    dic = {'fields': []}
    to_check = settings.OUTTER_KEYS
    to_check.append('event')
    try:
        val = request.GET.__getitem__('fields')
        dic['fields'] = val
    except KeyError as e:
        for key in settings.OUTTER_KEYS:
            dic['fields'].append(key)
        dic['fields'].append('event')
    for key in dic['fields']:
        if key not in to_check:
            dic['fields'].remove(key)
    return dic

def extract_paging_keys(request):
    dic = {}
    try:
        val = int(request.GET.__getitem__('start'))
        dic['from'] = val
    except KeyError as e:
        dic['from'] = 0

    try:
        val = int(request.GET.__getitem__('limit'))
        dic['size'] = val
    except KeyError as e:
        dic['size'] = 5
    return dic

def extract_sorting_keys(request):
    dic= {
            'sort_keys': [
                    
                ]
        }
    try:
        val = request.GET.__getitem__('sorts')
        for i in range(len(val)):
            skey = val[i]
            skey = skey.strip()
            if skey[0] == '-':
                dic['sort_keys'].append({
                        '{!s}'.format(skey[1:]): 'desc'
                    })
            else:
                dic['sort_keys'].append({
                        '{!s}'.format(skey): 'asc'
                    })
    except KeyError as e:
        dic['sort_keys'].append({'timestamp': 'desc'})
    return  dic

def extract_filter_keys(request):
    dic = {
            'filter_keys':[]
          }
    for key in settings.OUTTER_KEYS:
        try:
            val = request.GET.__getitem__(key)
            dic['filter_keys'].append({
                key: val,
                })
        except KeyError as e:
            continue
    for key in settings.INNER_KEYS:
        try:
            val = request.GET.__getitem__(key)
            dic['filter_keys'].append({
                key: val
                })
        except:
            continue
    return dic

def extract_aggregate_key(request):
    dic = {
            "agg_keys": []
        }
    aggs_type = []
    aggs_field = []
    try:
        aggs_type = request.GET['agg_type']
        aggs_field = request.GET['agg_field']
    except KeyError as ve:
        pass
    if len(aggs_type) != len(aggs_field):
        raise IndexError
    for key1, key2 in zip(aggs_type, aggs_field):
        if key2 in settings.AGGREGATE_FUNCS:
            dic['agg_keys'].append({
                key1: key2
            })
    return dic

def make_request_body(request, data):
    final_dic = {}
    final_dic['request_keys'] = data

    # extracting the time stamps
    dic = extract_time_keys(request)
    final_dic['time_range'] = dic
    
    # extracting the paging keys
    dic = extract_paging_keys(request)
    final_dic['paging'] = dic
    
    # extracting the fields to include
    dic = extract_field_keys(request)
    final_dic['fields'] = dic['fields']

    # extracting the filters
    dic = extract_filter_keys(request)
    if dic['filter_keys']:
        final_dic['filters'] = dic['filter_keys']

    # extracrting the sort keys
    dic = extract_sorting_keys(request)
    if dic['sort_keys']:
        final_dic['sorts'] = dic['sort_keys']

    
    dic = extract_aggregate_key(request)
    if dic['agg_keys']:
        final_dic['agg_keys'] = dic['agg_keys']

    return final_dic

def append_pagination(request, resp, page_keys, total_hits):
    cur = final_dic['paging']['from']
    limit = final_dic['paging']['size']
    prev_link = int(cur) - int(limit)
    next_link = int(cur) + int(limit)
    if next_link >= total_hits:
        next_link = None
    if prev_link < 0:
        prev_link = 0
    if cur == 0:
        prev_link = None
    if prev_link:
        temp = request
        get = dict(temp.GET)
        get['start'] = prev_link
        get['limit'] = limit
        temp.GET = get
        resp['prev_link'] = temp.build_absolute_uri()
    if next_link:
        temp = request
        get = dict(temp.GET)
        get['start'] = next_link
        get['limit'] = limit
        temp.GET = get
        resp['next_link'] = temp.build_absolute_uri()
    return resp


def append_key_value(resp, key, value):
    resp[key] = value
    return resp

def append_error_key_value(resp, key, value):
    if len(resp.keys()):
        resp = {}
        resp['error'] = {}
    resp['error'][key] = value
    return resp

def handle_response(request, data):
    res = {}
    status_code = 200
    data = None
    try:
        data = make_request_body(request, data)
        utils.ilog(LOG_CLASS, "Returned data: {!s}".format(data), mode="DEBUG")
    except exceptions.BadTimeFormat as e:
        res = append_error_key_value(res, 'status code', 400)
        res = append_error_key_value(res, 'error msg', 'time not in format yyyy-mm-ddThh:mm:ss')
        status_code = 400
    except IndexError as e:
        res = append_error_key_value(res, 'status code', 400)
        res = append_error_key_value(res, 'error msg', 'aggregate type and aggregate fields are of different lengths')
        status_code = 400
    else:
        obj=SearchElasticSearch()
        result = obj.search_elasticsearch(data)
        if 'status' in result.keys():
            res = append_pagination(request, res, data['page_keys'], result['total_hits'])
            res = append_key_value(res, 'status code', 200)
            res = append_key_value(res, 'total hits', result['total_hits'])
            res = append_key_value(res, 'result', result['logs'])
            status_code = 200
        else:
            res = append_error_key_value(res, 'status code', 500)
            res = append_error_key_value(res, 'error msg', "Database Error")
            status_code = 500
    return (res, status_code)

