import styles from "../App.module.css";

export interface Message {
  type: "user" | "ai";
  content: string;
  id?: string;
  timestamp?: number;
}

// Message component with React 19 optimizations
export default function ChatMessage({
  message,
  index,
}: {
  message: Message;
  index: number;
}) {
  return (
    <div
      key={message.id || index}
      className={`${styles.message} ${
        message.type === "user" ? styles.userMessage : styles.aiMessage
      }`}
      dangerouslySetInnerHTML={{
        __html:
          message.type === "user"
            ? "You: " + message.content
            : "AI: " + message.content,
      }}
    />
  );
}
