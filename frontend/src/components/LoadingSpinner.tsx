import styles from "../App.module.css";

// Loading component
export default function LoadingSpinner() {
  return (
    <div className={`${styles.message} ${styles.aiMessage} ${styles.loading}`}>
      🤖 AI is thinking...
    </div>
  );
}
