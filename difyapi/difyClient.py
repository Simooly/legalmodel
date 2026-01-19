import os
import requests
import json



class connectDify:
    def __init__(self, api_key, base_url, workflow_id):
        self.api_key = api_key
        self.base_url = base_url
        # self.user_id = user_id
        self.workflow_id = workflow_id
        
        # 定义请求头
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def upload_file(self, file_path):
        """
            上传文件到Dify
            :param file_path: 文件路径
            :return: 文件上传结果,包含文件ID或错误信息
        """
        upload_url = f"{self.base_url}/files/upload"
        
        # 改进：自动识别常见的文档MIME类型,对于.docx等格式很重要
        file_ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }
        content_type = mime_types.get(file_ext, 'application/octet-stream')

        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, content_type)}
            data = {'user': self.user_id}
            
            headers = {'Authorization': f'Bearer {self.api_key}'}
            # 增加超时时间,上传大文件时很有用
            response = requests.post(upload_url, headers=headers, files=files, data=data, timeout=120)

            if response.status_code not in [200, 201]:
            # print(f"文件上传失败: {response.status_code} - {response.text}")
                upload_file_result = {
                    'statue': 'error',
                    'message': f'文件上传失败: {response.status_code} - {response.text}'
                }

            if 'id' in response.json():
                upload_file_result = {
                    'statue': 'success',
                    'fileId': response.json()['id']
                }
            else:
                upload_file_result = {
                    'statue': 'error',
                    'message': '未获取到文件ID'
                }
                
        return upload_file_result

    
    def send_chat_message_to_check_contract(self, file_id, apart, workfield, bizId, contractServerIp="localhost", contractServerPort="1", query="审查", response_mode="streaming"):
        """
        发送对话消息到Dify工作流,并根据指定模式处理响应。

        :param response_mode: 响应模式,可选 'streaming' 或 'blocking'
        :return: 包含处理结果的字典
        """
        chat_url = f"{self.base_url}/chat-messages"
        
        inputs = {
            "contract":{
                "type": "document",
                "transfer_method": "local_file",
                "upload_file_id": file_id
            },
            "apart": apart,
            "workfield": workfield,
            "bizId": bizId,
            "contractServerIp": contractServerIp,
            "contractServerPort": contractServerPort,
            "workflow_id": "ab1242-f0ba-4bf6-b86b-bbdf9a5d6c76"
        }
        
        
        payload = {
            "inputs": inputs,
            "query": query,
            "response_mode": response_mode,  # 使用传入的模式
            "conversation_id": "",
            "user": self.user_id
        }
        
        # 根据模式决定是否使用流式请求
        stream = (response_mode == "streaming")
        
        try:
            response = requests.post(chat_url, headers=self.headers, json=payload, timeout=120, stream=stream)
            response.raise_for_status()  # 如果请求失败 (如 4xx, 5xx),则会抛出异常

            full_answer = ""
            raw_response_data = None # 用于存储原始响应对象

            if response_mode == "streaming":
                print("--- 进入流式响应处理模式 ---")
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:].strip()
                            if data_str == '[DONE]': # 结束符
                                break
                            try:
                                data = json.loads(data_str)
                                # 流式响应的结构可能在 'answer' 字段或 'data' 字段中
                                if 'answer' in data:
                                    # print(f"[流式接收] {data['answer']}", end='')
                                    full_answer += data['answer']
                                # 有些流式响应会把最终结果放在 'event' 为 'message' 的数据中
                                elif data.get('event') == 'message' and 'data' in data and 'answer' in data['data']:
                                    #  print(f"[流式接收] {data['data']['answer']}", end='')
                                     full_answer += data['data']['answer']
                            except json.JSONDecodeError:
                                print(f"[警告] 无法解析流式数据: {data_str}")
                # print("\n--- 流式响应处理结束 ---")
                raw_response_data = "Streaming response processed."

            elif response_mode == "blocking":
                print("--- 进入阻塞响应处理模式 ---")
                raw_response_data = response.json()
                print(f"[阻塞接收] 完整响应: {json.dumps(raw_response_data, indent=2)}")
                # 阻塞响应的 'answer' 通常在返回的JSON顶层
                if 'answer' in raw_response_data:
                    full_answer = raw_response_data['answer']
                # 也可能嵌套在 'data' 字段里
                elif 'data' in raw_response_data and 'answer' in raw_response_data['data']:
                    full_answer = raw_response_data['data']['answer']
            
            return {
                "statue": True,
                "answer": full_answer.strip(),
                "raw_response": raw_response_data
            }

        except requests.exceptions.RequestException as e:
            print(f"[错误] 发送请求时出错: {e}")
            return {
                "statue": False,
                "error": str(e),
                "answer": "",
                "raw_response": None
            }
        
