from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from markupsafe import Markup
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv
import markdown
import uuid
from datetime import datetime, timedelta

# Predefined prompt templates
PROMPT_TEMPLATES = {
    "summarize": "Please summarize the following content:\n{input}",
    "translate": "Please translate the following content to {target_language}:\n{input}",
    "code": "Please generate {language} code to implement the following functionality:\n{input}",
    "explain": "Please explain in simple terms:\n{input}"
}

app = Flask(__name__)
# 为生产环境配置 CORS
CORS(app, 
     origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174", "https://*.vercel.app"],
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"])  # 启用 CORS

# 存储多个会话的对话历史 - 使用字典按会话ID管理
conversation_sessions = {}

# 清理过期会话（超过1小时的会话）
def cleanup_expired_sessions():
    current_time = datetime.now()
    expired_sessions = []
    for session_id, session_data in conversation_sessions.items():
        if current_time - session_data['last_activity'] > timedelta(hours=1):
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del conversation_sessions[session_id]

# 自动加载 .env 文件
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
client = InferenceClient(
    provider="hf-inference",
    api_key=HF_API_KEY,
)

@app.route('/api/')
def api_index():
    return jsonify({"message": "AI Assistant API is running"})

@app.route('/api/<path:path>')
def api_static(path):
    return jsonify({"error": "API endpoint not found"}), 404

@app.route("/api/chat", methods=["POST"])
def chat():
    # 清理过期会话
    cleanup_expired_sessions()
    
    data = request.json
    user_msg = data.get("message", "")
    tool = data.get("tool", "")
    session_id = data.get("session_id", "")
    
    # 如果没有提供会话ID，创建新的会话
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # 初始化会话（如果不存在）
    if session_id not in conversation_sessions:
        conversation_sessions[session_id] = {
            'history': [],
            'last_activity': datetime.now()
        }
    
    # 更新会话活动时间
    conversation_sessions[session_id]['last_activity'] = datetime.now()
    conversation_history = conversation_sessions[session_id]['history']
    
    if not user_msg:
        return jsonify({"reply": "Please enter a message.", "session_id": session_id})
        
    try:
        # Build prompt
        prompt = PROMPT_TEMPLATES.get(tool, "{input}").format(
            target_language=data.get("target_language", "Chinese"),
            language=data.get("language", "Python"),
            input=user_msg
        ) if tool else user_msg
            
        # 添加对话历史上下文
        messages = [{"role": "system", "content": "你是一个有用的 AI 助手。"}]
        for msg in conversation_history[-5:]:  # 保留最近5轮对话
            messages.append(msg)
        messages.append({"role": "user", "content": prompt})
        
        completion = client.chat.completions.create(
            model="HuggingFaceTB/SmolLM3-3B",
            messages=messages
        )
        
        reply = completion.choices[0].message.content.strip()
        
        # 将回复转换为 Markdown 并保存对话记录
        reply_html = Markup(markdown.markdown(reply))
        conversation_history.append({"role": "user", "content": user_msg})
        conversation_history.append({"role": "assistant", "content": reply})
        
        return jsonify({"reply": reply_html, "session_id": session_id})
    except Exception as e:
        return jsonify({"reply": f"出错了: {e}", "session_id": session_id})

@app.route("/api/session/<session_id>/history", methods=["GET"])
def get_session_history(session_id):
    """获取指定会话的历史记录"""
    if session_id not in conversation_sessions:
        return jsonify({"history": [], "session_id": session_id})
    
    history = conversation_sessions[session_id]['history']
    # 转换为前端需要的格式
    messages = []
    for msg in history:
        if msg['role'] == 'user':
            messages.append({"type": "user", "content": msg['content']})
        elif msg['role'] == 'assistant':
            messages.append({"type": "ai", "content": msg['content']})
    
    return jsonify({"history": messages, "session_id": session_id})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
