import re
# from this import s
from django.shortcuts import render
import os
import datetime
import json
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.views.decorators.http import require_http_methods

# 导入difyClient
from .difyClient import connectDify

# Dify 接口访问地址 
DIFY_BASE_URL = "http://127.0.0.1/v1"

# Dify 合同审查工作流配置
DIFY_check_API_KEY = "app-Zv1BZsNrFKSp5aHBGIhid39S"
# DIFY_check_USER_ID = "abc-1234"
DIFY_check_WORKFLOW_ID = "ab1242-f0ba-4bf6-b86b-bbdf9a5d6c76"

# 创建connectDify实例:
dify_check_client = connectDify(
    api_key=DIFY_check_API_KEY,
    base_url=DIFY_BASE_URL,
    # user_id=DIFY_check_USER_ID,
    workflow_id=DIFY_check_WORKFLOW_ID
)



# Dify合同审查工作流业务流程函数
def generate_dify_response(file_path, apart, workfield, bizId):
    # dify 工作流响应函数
    
    # 上传文档到Dify获取文档ID
    document_response = dify_check_client.upload_file(file_path=file_path)
    if document_response["statue"] == "error":
        result = {
            "statue": False,
            "error": document_response["message"],
            "answer": ""
        }
        return result
    
    document_id = document_response["fileId"]
    
    # Dify 合同审核工作流
    dify_chatflow_response = dify_check_client.send_chat_message_to_check_contract(
            file_id = document_id,
            apart = apart,
            workfield = workfield,
            bizId = bizId,
            query = "审查",
            response_mode = "streaming"
        )
    if dify_chatflow_response["statue"] == False:
        result = {
            "statue": False,
            "error": dify_chatflow_response["error"],
            "answer": ""
        }
        return result

    
    result = {
        "statue": True,
        "answer": dify_chatflow_response["answer"]
    }
    return result


# Dify合同审查工作流接口
@csrf_exempt
@require_http_methods(["POST"])
def upload_document_review(request):
    """
    处理文档上传的接口
    """
    try:
        print(request.POST)

        # 检查是否有文件上传
        if 'document' in request.FILES:
            uploaded_file = request.FILES['document']
            # print(request.POST)
            # 获取文件信息
            file_name = uploaded_file.name
            # file_size = uploaded_file.size
            content_type = uploaded_file.content_type
            


            # 获取其他表单参数
            apart = request.POST.get('apart', '')  # 甲方/乙方...
            workfield = request.POST.get('workfield', '')  # 领域
            bizId = request.POST.get('bizId', '')  # 业务ID
            # userID = request.POST.get('userID', '')  # 用户ID
            
            

            # 验证必填参数
            if not all([apart, workfield, bizId]):
                return JsonResponse({
                    'status': 'error',
                    'message': '缺少必填参数:apart, workfield, bizId'
                }, status=400)
            
            # 确保上传目录存在
            upload_dir = 'uploads'
            os.makedirs(upload_dir, exist_ok=True)
            
            # 生成带时间戳的文件名
            file_base_name, file_extension = os.path.splitext(file_name)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            new_file_name = f"{file_base_name}_{timestamp}{file_extension}"
            
            # 保存文件到uploads目录
            save_path = os.path.join(upload_dir, new_file_name)
            # absolute_path = os.path.abspath(save_path)
            
            with open(save_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            dify_workflow_response = generate_dify_response(
                file_path = save_path,
                apart = apart,
                workfield = workfield,
                bizId = bizId,
            )

            if dify_workflow_response["statue"] == False:
                return JsonResponse({
                    'status': 'error',
                    'message': dify_workflow_response["error"],
                }, status=400)


            # 返回成功响应
            response_data = {
                'status': 'success',
                'message': '文档上传成功',
                'answer': dify_workflow_response["answer"]
            }
            return JsonResponse(response_data, status=200)
        
        else:
            # 没有上传文件
            return JsonResponse({
                'status': 'error',
                'message': '请上传文档文件'
            }, status=400)
            
    except Exception as e:
        # 处理异常情况
        return JsonResponse({
            'status': 'error',
            'message': f'处理文档时发生错误: {str(e)}'
        }, status=500)
