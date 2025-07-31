from flask import Flask, render_template_string, request, jsonify
from markupsafe import Markup
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv
import markdown
import json

# 预定义的提示词模板
PROMPT_TEMPLATES = {
    "summarize": "请总结以下内容：\n{input}",
    "translate": "请将以下内容翻译成{target_language}：\n{input}",
    "code": "请生成{language}代码实现以下功能：\n{input}",
    "explain": "请用通俗易懂的语言解释：\n{input}"
}

# AI 工具定义
AI_TOOLS = {
    "summarize": "生成文本摘要",
    "translate": "多语言翻译",
    "code": "代码生成",
    "explain": "概念解释"
}

app = Flask(__name__)

# 存储对话历史
conversation_history = []

# 自动加载 .env 文件
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
client = InferenceClient(
    provider="hf-inference",
    api_key=HF_API_KEY,
)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>AI 助手</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        #chat { width: 100%; max-width: 800px; margin: auto; }
        .msg { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user { color: blue; background: #f0f0f0; }
        .ai { color: green; background: #f8f8f8; }
        #toolbar { margin: 10px 0; }
        .tool-btn { margin: 0 5px; padding: 5px 10px; }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown.min.css">
</head>
<body>
    <div id="chat">
        <h2>AI 助手</h2>
        <div id="toolbar">
            工具：
            <select id="tool">
                <option value="">普通对话</option>
                <option value="summarize">文本摘要</option>
                <option value="translate">多语言翻译</option>
                <option value="code">代码生成</option>
                <option value="explain">概念解释</option>
            </select>
            <select id="language" style="display:none;">
                <option value="中文">中文</option>
                <option value="英文">英文</option>
                <option value="日文">日文</option>
            </select>
            <select id="code_language" style="display:none;">
                <option value="Python">Python</option>
                <option value="JavaScript">JavaScript</option>
                <option value="Java">Java</option>
            </select>
        </div>
        <div id="messages" class="markdown-body"></div>
        <textarea id="input" placeholder="请输入内容..." style="width:80%; height:100px;"></textarea>
        <button onclick="send()">发送</button>
    </div>
    <script>
        const toolSelect = document.getElementById('tool');
        const langSelect = document.getElementById('language');
        const codeLangSelect = document.getElementById('code_language');
        
        toolSelect.onchange = function() {
            langSelect.style.display = this.value === 'translate' ? 'inline' : 'none';
            codeLangSelect.style.display = this.value === 'code' ? 'inline' : 'none';
        };

        async function send() {
            const input = document.getElementById('input');
            const messages = document.getElementById('messages');
            const tool = toolSelect.value;
            const text = input.value;
            
            if (!text) return;
            
            messages.innerHTML += `<div class="msg user">你: ${text}</div>`;
            input.value = '';
            
            const params = {
                message: text,
                tool: tool
            };
            
            if (tool === 'translate') {
                params.target_language = langSelect.value;
            } else if (tool === 'code') {
                params.language = codeLangSelect.value;
            }
            
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });
            
            const data = await response.json();
            messages.innerHTML += `<div class="msg ai">AI: ${data.reply}</div>`;
            messages.scrollTop = messages.scrollHeight;
        }
    </script>
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_msg = data.get("message", "")
    tool = data.get("tool", "")
    
    if not user_msg:
        return jsonify({"reply": "请输入内容。"})
        
    try:
        # 根据选择的工具构建提示词
        if tool:
            if tool == "translate":
                prompt = PROMPT_TEMPLATES[tool].format(
                    target_language=data.get("target_language", "中文"),
                    input=user_msg
                )
            elif tool == "code":
                prompt = PROMPT_TEMPLATES[tool].format(
                    language=data.get("language", "Python"),
                    input=user_msg
                )
            else:
                prompt = PROMPT_TEMPLATES[tool].format(input=user_msg)
        else:
            prompt = user_msg
            
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
