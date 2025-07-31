import { useState, useRef, useEffect, useCallback, useTransition } from "react";
import styles from "./App.module.css";

interface Message {
  type: "user" | "ai";
  content: string;
}

interface ChatParams {
  message: string;
  tool: string;
  target_language?: string;
  language?: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [selectedTool, setSelectedTool] = useState("");
  const [targetLanguage, setTargetLanguage] = useState("Chinese");
  const [codeLanguage, setCodeLanguage] = useState("Python");
  const [isLoading, setIsLoading] = useState(false);
  const [isPending, startTransition] = useTransition();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    if (!isPending) {
      startTransition(() => {
        scrollToBottom();
      });
    }
  }, [messages, isPending, scrollToBottom]);

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.ctrlKey && e.key === "Enter") {
      sendMessage();
    }
  };

  const sendMessage = async () => {
    if (!inputText) return;

    setIsLoading(true);

    // 添加用户消息
    setMessages((prev) => [
      ...prev,
      {
        type: "user",
        content: inputText,
      },
    ]);

    const params: ChatParams = {
      message: inputText,
      tool: selectedTool,
    };

    if (selectedTool === "translate") {
      params.target_language = targetLanguage;
    } else if (selectedTool === "code") {
      params.language = codeLanguage;
    }

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });

      const data = await response.json();

      startTransition(() => {
        // 添加 AI 回复
        setMessages((prev) => [
          ...prev,
          {
            type: "ai",
            content: data.reply,
          },
        ]);

        // 清空输入
        setInputText("");
        setIsLoading(false);
      });
    } catch (error) {
      console.error("Error:", error);
      startTransition(() => {
        setMessages((prev) => [
          ...prev,
          {
            type: "ai",
            content: `出错了: ${
              error instanceof Error ? error.message : "未知错误"
            }`,
          },
        ]);
        setIsLoading(false);
      });
    }
  };

  return (
    <div className={styles.container}>
      <h2>AI Assistant</h2>

      <div className={styles.toolbar}>
        Tools:
        <select
          value={selectedTool}
          onChange={(e) => setSelectedTool(e.target.value)}
          className={styles.select}
        >
          <option value="">General Chat</option>
          <option value="summarize">Text Summary</option>
          <option value="translate">Translation</option>
          <option value="code">Code Generation</option>
          <option value="explain">Explanation</option>
        </select>
        {selectedTool === "translate" && (
          <select
            value={targetLanguage}
            onChange={(e) => setTargetLanguage(e.target.value)}
            className={styles.select}
          >
            <option value="Chinese">Chinese</option>
            <option value="English">English</option>
            <option value="Japanese">Japanese</option>
          </select>
        )}
        {selectedTool === "code" && (
          <select
            value={codeLanguage}
            onChange={(e) => setCodeLanguage(e.target.value)}
            className={styles.select}
          >
            <option value="Python">Python</option>
            <option value="JavaScript">JavaScript</option>
            <option value="Java">Java</option>
          </select>
        )}
      </div>

      <div className={`${styles.messages} markdown-body`}>
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`${styles.message} ${
              msg.type === "user" ? styles.userMessage : styles.aiMessage
            }`}
            dangerouslySetInnerHTML={{
              __html:
                msg.type === "user"
                  ? "You: " + msg.content
                  : "AI: " + msg.content,
            }}
          />
        ))}
        {isLoading && (
          <div
            className={`${styles.message} ${styles.aiMessage} ${styles.loading}`}
          >
            AI is thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className={styles.inputArea}>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Enter your message... (Ctrl + Enter to send)"
          className={styles.textarea}
          disabled={isLoading}
        />
        <br />
        <button
          onClick={sendMessage}
          className={styles.button}
          disabled={isLoading}
        >
          {isLoading ? "Thinking..." : "Send"}
        </button>
      </div>
    </div>
  );
}

export default App;
