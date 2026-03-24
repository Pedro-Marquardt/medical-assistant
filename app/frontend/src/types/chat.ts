export type Message = {
  id: string;
  content: string;
  type: 'user' | 'assistant';
  timestamp: Date;
  isStreaming?: boolean;
};

export type ChatRequest = {
  query: string;
  user_id: string;
};