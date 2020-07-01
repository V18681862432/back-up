import copy

result = {'message': 'success', 'code': 0, 'data': [{'status': 2, 'step_results': [{'tag': '', 'ip_logs': [{'total_time': 0.0, 'ip': '10.0.2.13', 'log_content': '', 'exit_code': 0, 'bk_cloud_id': 0, 'retry_count': 0, 'error_code': 0}], 'ip_status': 5}], 'is_finished': False, 'step_instance_id': 3263, 'name': 'search_id.sh'}], 'result': True, 'request_id': '8def0759138a4fb0b953b314ffbf86b0'}

for re in result['data']:
    print(re['is_finished'] is not True)

