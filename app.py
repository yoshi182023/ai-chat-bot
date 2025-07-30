from flask import Flask, render_template_string, request, jsonify
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

app = Flask(__name__)

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
    <title>OpenAI 聊天机器人</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        #chat { width: 100%; max-width: 600px; margin: auto; }
        .msg { margin: 10px 0; }
        .user { color: blue; }
        .ai { color: green; }
    </style>
</head>
<body>
    <div id="chat">
        <h2>OpenAI 聊天机器人</h2>
        <div id="messages"></div>
        <input type="text" id="input" placeholder="请输入问题..." style="width:80%;">
        <button onclick="send()">发送</button>
    </div>
    <script>
        function send() {
            var input = document.getElementById('input').value;
            if (!input) return;
            var messages = document.getElementById('messages');
            messages.innerHTML += '<div class="msg user">你: ' + input + '</div>';
            document.getElementById('input').value = '';
            fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: input })
            })
            .then(res => res.json())
            .then(data => {
                messages.innerHTML += '<div class="msg ai">AI: ' + data.reply + '</div>';
            });
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
    user_msg = request.json.get("message", "")
    if not user_msg:
        return jsonify({"reply": "请输入内容。"})
    try:
        completion = client.chat.completions.create(
            model="HuggingFaceTB/SmolLM3-3B",
            messages=[
                {"role": "user", "content": user_msg}
            ],
        )
        reply = completion.choices[0].message.content.strip()
    except Exception as e:
        reply = f"出错了: {e}"
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
