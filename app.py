from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from markupsafe import Markup
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv
import markdown

# Predefined prompt templates
PROMPT_TEMPLATES = {
    "summarize": "Please summarize the following content:\n{input}",
    "translate": "Please translate the following content to {target_language}:\n{input}",
    "code": "Please generate {language} code to implement the following functionality:\n{input}",
    "explain": "Please explain in simple terms:\n{input}"
}

app = Flask(__name__)
CORS(app)  # 启用 CORS

# 存储对话历史
conversation_history = []

# 自动加载 .env 文件
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
client = InferenceClient(
    provider="hf-inference",
    api_key=HF_API_KEY,
)

@app.route('/')
def serve_index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend', path)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_msg = data.get("message", "")
    tool = data.get("tool", "")
    
    if not user_msg:
        return jsonify({"reply": "Please enter a message."})
        
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
        
        return jsonify({"reply": reply_html})
    except Exception as e:
        return jsonify({"reply": f"出错了: {e}"})

if __name__ == "__main__":
    app.run(debug=True)
