import json
import os
import uuid
from datetime import datetime, timedelta
from huggingface_hub import InferenceClient

# 初始化HuggingFace客户端
client = InferenceClient(
    model="microsoft/DialoGPT-medium",
    token=os.environ.get("HF_API_KEY")
)

# 内存存储（生产环境建议使用DynamoDB）
conversations = {}

# 预定义提示模板
PROMPT_TEMPLATES = {
    "flirt": "Reply flirtatiously to: {input}",
    "translate": "请帮我把以下内容翻译成{target_language}，要自然流畅：\n{input}",
    "funny": "请帮我用搞笑幽默的方式回复对方，让对话更有趣。对方说：{input}",
    "explain": "请帮我用简单易懂的方式解释：\n{input}"
}

def lambda_handler(event, context):
    """AWS Lambda处理函数"""
    
    # 处理CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    }
    
    # 处理OPTIONS请求
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'CORS preflight'})
        }
    
    # 解析路径
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    
    try:
        # API根路径
        if path == '/api' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'AI Assistant API is running'})
            }
        
        # 聊天API
        elif path == '/api/chat' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            return handle_chat(body, headers)
        
        # 会话历史API
        elif path.startswith('/api/session/') and path.endswith('/history') and method == 'GET':
            session_id = path.split('/')[-2]
            return get_session_history(session_id, headers)
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_chat(data, headers):
    """处理聊天请求"""
    user_msg = data.get("message", "")
    tool = data.get("tool", "")
    session_id = data.get("session_id", str(uuid.uuid4()))
    
    if not user_msg:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'Message is required'})
        }
    
    # 获取或创建会话
    if session_id not in conversations:
        conversations[session_id] = []
    
    conversation_history = conversations[session_id]
    
    # 构建提示
    if tool:
        prompt = PROMPT_TEMPLATES.get(tool, "{input}").format(
            target_language=data.get("target_language", "Chinese"),
            language=data.get("language", "Python"),
            input=user_msg
        )
    else:
        # 普通聊天模式
        prompt = f"请帮我回复对方，让对话更有趣。对方说：{user_msg}"
    
    # 构建消息
    messages = [{"role": "system", "content": "你是一个专业的调情助手。请直接生成用户可以直接发送给对方的内容，不要解释你的回复过程，不要重复指令内容。只输出回复内容本身。"}]
    
    # 添加对话历史
    for msg in conversation_history[-5:]:
        messages.append(msg)
    
    messages.append({"role": "user", "content": prompt})
    
    # 调用AI
    try:
        completion = client.chat.completions.create(
            model="microsoft/DialoGPT-medium",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = completion.choices[0].message.content
        
        # 保存对话
        conversation_history.append({"role": "user", "content": user_msg})
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': ai_response,
                'session_id': session_id
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'AI request failed: {str(e)}'})
        }

def get_session_history(session_id, headers):
    """获取会话历史"""
    if session_id not in conversations:
        conversations[session_id] = []
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'session_id': session_id,
            'history': conversations[session_id]
        })
    }