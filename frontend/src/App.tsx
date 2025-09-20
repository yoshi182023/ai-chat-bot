import { useState, useRef, useEffect, useOptimistic, Suspense } from "react";
import styles from "./App.module.css";
import LoadingSpinner from "./components/LoadingSpinner";
import type { Message } from "./components/ChatMessage";
import ChatMessage from "./components/ChatMessage";
import { loadSessionHistoryAction } from "./service/loadSessionHistoryAction";
import { sendChatAction, type ChatParams } from "./service/sendChatAction";

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [optimisticMessages, addOptimisticMessage] = useOptimistic(
    messages,
    (currentMessages: Message[], newMessage: Message) => [
      ...currentMessages,
      newMessage,
    ]
  );

  const [inputText, setInputText] = useState("");
  const [selectedTool, setSelectedTool] = useState("");
  const [targetLanguage, setTargetLanguage] = useState("Chinese");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");

  const messagesEndRef = useRef<HTMLDivElement>(null);

  function scrollToBottom() {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  // 使用 React 19 的并发特性
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      scrollToBottom();
    }, 0);

    return () => clearTimeout(timeoutId);
  }, [optimisticMessages]);

  // Session restoration with error handling
  useEffect(() => {
    async function restoreSession() {
      const savedSessionId = localStorage.getItem("chatSessionId");
      if (savedSessionId) {
        setSessionId(savedSessionId);
        try {
          const history = await loadSessionHistoryAction(savedSessionId);
          setMessages(history);
        } catch (error) {
          console.error("Failed to restore session:", error);
          localStorage.removeItem("chatSessionId");
        }
      }
    }

    restoreSession();
  }, []);

  // Auto-save session ID
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem("chatSessionId", sessionId);
    }
  }, [sessionId]);

  // Enhanced new session function
  function startNewSession() {
    setSessionId("");
    setMessages([]);
    localStorage.removeItem("chatSessionId");
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.ctrlKey && e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  };

  // Enhanced message sending with optimistic updates
  async function sendMessage() {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      type: "user",
      content: inputText.trim(),
      id: Date.now().toString(),
      timestamp: Date.now(),
    };

    // Optimistic update
    addOptimisticMessage(userMessage);

    setIsLoading(true);
    const currentInput = inputText.trim();
    setInputText("");

    const params: ChatParams = {
      message: currentInput,
      tool: selectedTool,
      session_id: sessionId,
    };

    if (selectedTool === "translate") {
      params.target_language = targetLanguage;
    }

    try {
      const data = await sendChatAction(params);

      // Update session ID if new session
      if (data.session_id && data.session_id !== sessionId) {
        setSessionId(data.session_id);
      }

      const aiMessage: Message = {
        type: "ai",
        content: data.reply,
        id: (Date.now() + 1).toString(),
        timestamp: Date.now(),
      };

      // Update actual state
      setMessages((prev) => [...prev, userMessage, aiMessage]);
    } catch (error) {
      console.error("Error:", error);
      const errorMessage: Message = {
        type: "ai",
        content: `出错了: ${
          error instanceof Error ? error.message : "未知错误"
        }`,
        id: (Date.now() + 1).toString(),
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMessage, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  // React 19 form handling with actions
  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await sendMessage();
  }

  return (
    <div className={styles.container}>
      <header>
        <h2>💕 短信聊天助手</h2>
        <p className={styles.subtitle}>让你的聊天更有趣</p>
      </header>

      <div className={styles.toolbar}>
        <button
          onClick={startNewSession}
          className={styles.button}
          style={{ marginRight: "10px" }}
          type="button"
        >
          💬 新对话
        </button>

        <label className={styles.label}>
          回复风格:
          <select
            value={selectedTool}
            onChange={(e) => setSelectedTool(e.target.value)}
            className={styles.select}
          >
            <option value="">💬 普通聊天</option>
            <option value="flirt">💋 调情回复</option>
            <option value="translate">🌍 翻译回复</option>
            <option value="funny">😄 幽默回复</option>
            <option value="explain">💭 解释说明</option>
          </select>
        </label>

        {selectedTool === "translate" && (
          <label className={styles.label}>
            目标语言:
            <select
              value={targetLanguage}
              onChange={(e) => setTargetLanguage(e.target.value)}
              className={styles.select}
            >
              <option value="Chinese">🇨🇳 Chinese</option>
              <option value="English">🇺🇸 English</option>
              <option value="Japanese">🇯🇵 Japanese</option>
            </select>
          </label>
        )}

      </div>

      <div className={`${styles.messages} markdown-body`}>
        <Suspense fallback={<LoadingSpinner />}>
          {optimisticMessages.map((msg, index) => (
            <ChatMessage key={msg.id || index} message={msg} index={index} />
          ))}
        </Suspense>

        {isLoading && <LoadingSpinner />}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className={styles.inputArea}>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="💭 输入对方说的话，我来帮你回复... (Ctrl + Enter 发送)"
          className={styles.textarea}
          disabled={isLoading}
          rows={3}
          aria-label="Chat message input"
        />

        <div className={styles.buttonGroup}>
          <button
            type="submit"
            className={styles.button}
            disabled={isLoading || !inputText.trim()}
            aria-label="Send message"
          >
            {isLoading ? "🤔 思考中..." : "💕 帮我回复"}
          </button>

          {sessionId && (
            <span className={styles.sessionInfo}>
              Session: {sessionId.slice(0, 8)}...
            </span>
          )}
        </div>
      </form>
    </div>
  );
}

export default App;
