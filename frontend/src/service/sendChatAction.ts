export interface ChatParams {
  message: string;
  tool: string;
  target_language?: string;
  language?: string;
  session_id?: string;
}

// 模拟 Server Action 的 API 调用
export async function sendChatAction(
  params: ChatParams
): Promise<{ reply: string; session_id: string }> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}
