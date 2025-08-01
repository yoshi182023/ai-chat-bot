import type { Message } from "../components/ChatMessage";

// Session history loader
export async function loadSessionHistoryAction(
  sessionId: string
): Promise<Message[]> {
  const response = await fetch(`/api/session/${sessionId}/history`);
  if (!response.ok) {
    throw new Error("Failed to load session history");
  }
  const data = await response.json();
  return data.history || [];
}
