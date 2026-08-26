const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export async function triggerHealAgent(eventId: string, targetAgent: string) {
  const response = await fetch(`${API_BASE_URL}/api/v1/agents/heal`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event_id: eventId, target_agent: targetAgent }),
  });
  if (!response.ok) throw new Error("Healing request failed");
  return response.json();
}

export function subscribeMetricsStream(onData: (data: any) => void) {
  const eventSource = new EventSource(`${API_BASE_URL}/api/v1/stream/metrics`);

  eventSource.onmessage = (event) => {
    try {
      const parsedData = JSON.parse(event.data);
      onData(parsedData);
    } catch (err) {
      console.error("SSE Parsing Error:", err);
    }
  };

  eventSource.onerror = (err) => {
    console.error("SSE Connection Error:", err);
    eventSource.close();
  };

  return () => eventSource.close();
}
