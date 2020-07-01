# -*- coding: utf-8 -*-
import base64
import copy
from time import sleep

from celery import task
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from blueking.component.shortcuts import get_client_by_request

# 开发框架中通过中间件默认是需要登录态的，如有不需要登录的，可添加装饰器login_exempt
# 装饰器引入 from blueapps.account.decorators import login_exempt
from home_application.models import BackUp


def home(request):
    """
    首页
    """

    return render(request, 'home_application/index.html')


def history(request):
    """
    记录查看
    """
    back_up_list = BackUp.objects.all()
    return render(request, 'home_application/history.html', {'data': back_up_list})


def dev_guide(request):
    """
    开发指引
    """
    return render(request, 'home_application/dev_guide.html')


def contact(request):
    """
    联系页
    """
    return render(request, 'home_application/contact.html')


def search_business(request):
    """
    查找业务
    """
    client = get_client_by_request(request)
    result = client.cc.search_business()

    biz = []
    if result.get('result', False):
        for info in result['data']['info']:
            biz.append({
                'id': info['bk_biz_id'] or info['bid'],
                'name': info['bk_biz_name']
            })

    return JsonResponse({"results": biz})


def search_host(request):
    """
    查找主机
    """
    client = get_client_by_request(request)
    bk_biz_id = request.POST.get("bk_biz_id")
    bk_inst_id = request.POST.get("bk_inst_id")
    kwargs = {'bk_biz_id': bk_biz_id}
    result = client.cc.search_biz_inst_topo(kwargs)

    # 通过实例id获取模型id和实例名称
    bk_obj_list = get_obj_id(result['data'], bk_inst_id)
    for bk_obj in bk_obj_list:
        bk_obj_id = bk_obj['bk_obj_id']
        bk_inst_name = bk_obj['bk_inst_name']

    if bk_inst_id != bk_biz_id:
        kwargs = {
            "bk_biz_id": bk_biz_id,
            "condition": [{
                "bk_obj_id": bk_obj_id,
                "fields": [],
                "condition": [
                    {
                        "field": "bk_" + bk_obj_id + "_name",
                        "operator": "$eq",
                        "value": bk_inst_name
                    }
                ]
            }]
        }
    else:
        kwargs = {
            "bk_biz_id": bk_biz_id
        }

    result = client.cc.search_host(kwargs)

    # 处理数据获取ip
    bk_host_innerips = []
    if result.get('result', False):
        for info in result['data']['info']:
            bk_host_innerips.append({"ip": info['host']['bk_host_innerip']})
    return JsonResponse({'results': bk_host_innerips})


def fast_execute_script(request):
    """
    快速执行脚本查找文件
    """

    # 处理前端参数符合接口参数
    tmp_list = str(request.POST.get("ip_list")).split("\n")
    ip_list = []
    for ip in tmp_list:
        if len(ip) > 0:
            ip_list.append({"bk_cloud_id": 0, "ip": ip})
    bk_biz_id = request.POST.get("bk_biz_id")
    module_name = request.POST.get("module_name")
    pattern = request.POST.get("pattern")

    # 脚本
    script = '''#!/bin/bash
cd {} || return
find  .  -name "{}" | sed "s;./;;g" | wc -l
find  . -name   "{}"| sed "s;./;;g"| xargs du -ck

    
    '''.format(module_name, pattern, pattern)
    encode_str = base64.b64encode(script.encode("utf-8"))
    script_content = str(encode_str, 'utf-8')

    # 参数
    kwargs = {
        "bk_biz_id": bk_biz_id,
        "script_content": script_content,
        "account": "root",
        "script_type": 1,
        "ip_list": ip_list
    }
    client = get_client_by_request(request)
    result = client.job.fast_execute_script(kwargs)

    execute_result_info = []

    if result.get('result', False):
        kwargs = {
            "bk_biz_id": bk_biz_id,
            "job_instance_id": result['data']['job_instance_id']
        }
    else:
        return JsonResponse({'results': execute_result_info})
    # 轮询获取日志信息
    result = client.job.get_job_instance_log(kwargs)
    flag = True
    while flag:
        for data in result['data']:
            if data['is_finished'] is not True:
                sleep(1)
                result = client.job.get_job_instance_log(kwargs)
            else:
                flag = False
                break

    # 处理数据
    for data in result['data']:
        for step_result in data['step_results']:
            tmp_dict = {}
            for ip_logs in step_result['ip_logs']:
                tmp_dict['ip'] = ip_logs['ip']
                strs = str(ip_logs['log_content']).split("\n")
                if strs[0] == '0':
                    break
                tmp_dict['number'] = strs[0]
                info_string = ''
                if len(strs) >= 2:
                    for cnt in range(1, len(strs) - 2):
                        info_string = info_string + ";" + strs[cnt].split()[1]
                    tmp_dict['file_list'] = info_string[1: len(info_string)]
                    tmp_dict['size'] = strs[len(strs) - 2].split()[0]
                    execute_result_info.append(copy.deepcopy(tmp_dict))
                    tmp_dict.clear()

    return JsonResponse({'results': execute_result_info})


def execute_job(request):
    """
    备份文件
    """

    client = get_client_by_request(request)
    bk_biz_id = request.POST.get("bk_biz_id")

    # 环境提供的备份作业ID
    bk_job_id = 11

    # 获取相关参数保存到DB中
    ip = request.POST.get("ip")
    file_list = request.POST.get("file_list")
    count = request.POST.get("count")
    size = request.POST.get("size")
    pattern = str(file_list).split(";")[0]
    pattern = "*" + pattern[pattern.index(".") + 1: len(pattern)]

    # 编写脚本内容，并进行base64编码
    script = ''' #! /bin/bash
    cd /data/logs || return 
    t=$(date +%Y%m%d%H%M%S)
    tar -zcf /data/backup/bkds$t.tar.gz  $1
    echo bkds$t.tar.gz 
        '''
    script = base64.b64encode(script.encode('utf-8'))
    script_content = str(script, 'utf-8')
    args = base64.b64encode(pattern.encode('utf-8'))
    param = str(args, 'utf-8')

    kwargs = {
        "bk_biz_id": bk_biz_id,
        "bk_job_id": bk_job_id,
        "steps": [
            {
                "account": "root",
                "script_content": script_content,
                "ip_list": [
                    {
                        "ip": ip,
                        "bk_cloud_id": 0
                    }
                ],
                "step_id": 15,
                "script_param": param,
                "type": 1,
                "order": 1,
                "script_type": 1
            }
        ]
    }

    # 将参数和client传递给task获取作业实例ID
    job_instance_id = task(kwargs, client)
    kwargs = {
        "bk_biz_id": bk_biz_id,
        "job_instance_id": job_instance_id
    }
    result = client.job.get_job_instance_log(kwargs)

    flag = True
    while flag:
        for data in result['data']:
            if data['is_finished'] is not True:
                sleep(1)
                result = client.job.get_job_instance_log(kwargs)
            else:
                flag = False
                break

    back_time = ''
    if result.get('result', False):
        for data in result['data']:
            for step_result in data['step_results']:
                for ip_log in step_result['ip_logs']:
                    back_time = ip_log['start_time']
    else:
        return HttpResponse("Error")
    back_time = back_time.split(' ')[0] + ' ' + back_time.split(' ')[1]

    # 获取用户信息
    bk_username = request.user.username

    # 保存记录到DB
    back_unit = BackUp(
        ip=ip,
        file=file_list,
        count=count,
        size=size,
        back_time=back_time,
        user_name=bk_username
    )
    back_unit.save()

    return JsonResponse({'results': str('后台已经开始备份，请关闭弹窗后耐心等待。')})


@task
def task(kwargs, client):
    result = client.job.execute_job(kwargs)
    return result['data']['job_instance_id']


def search_biz_inst_topo(request):
    """
    查找拓扑
    """

    bk_biz_id = request.POST.get("bk_biz_id")
    client = get_client_by_request(request)
    kwargs = {"bk_biz_id": bk_biz_id}
    result = client.cc.search_biz_inst_topo(kwargs)

    # 数据处理
    bk_biz = []
    if result.get('result', False):
        bk_biz = get_node(result['data'])
    string = str(bk_biz)
    string = string.replace("}, {\'c", ",\'c")

    return JsonResponse({"results": string.replace("\'", "\"")})


def get_node(result):
    """
    获取节点信息
    """

    bk_biz_child = []
    for data in result:
        bk_biz_child.append({
            "id": data['bk_inst_id'],
            "text": data['bk_inst_name']
        })
        bk_biz_child.append({"children": get_node(data['child'])})

    return bk_biz_child


def get_obj_id(result, bk_inst_id):
    """
    通过实例id获取模型id和实例名称
    """

    bk_biz_child = []
    for data in result:
        if data['bk_inst_id'] == int(bk_inst_id):
            bk_biz_child.append({
                "bk_obj_id": data['bk_obj_id'],
                "bk_inst_name": data['bk_inst_name']
            })
            break
        bk_biz_child = get_obj_id(data['child'], bk_inst_id)

    return bk_biz_child
