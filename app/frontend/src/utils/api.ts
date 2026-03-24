import { v4 as uuidv4 } from 'uuid';

export function generateUUID(): string {
  return uuidv4();
}

export async function sendStreamingMessage(
  query: string, 
  userId: string, 
  onChunk: (chunk: string) => void,
  onComplete: () => void,
  onError: (error: string) => void
): Promise<void> {
  const backendHost = import.meta.env.VITE_BACKEND_HOST || 'http://localhost:3030';
  
  try {
    const response = await fetch(`${backendHost}/medical/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        user_id: userId
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('ReadableStream not supported');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      
      if (done) {
        onComplete();
        break;
      }

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.trim() && line.startsWith('data: ')) {
          const data = line.slice(6); // Remove "data: "
          if (data.trim()) {
            onChunk(data);
          }
        }
      }
    }
  } catch (error) {
    onError(error instanceof Error ? error.message : 'Erro desconhecido');
  }
}