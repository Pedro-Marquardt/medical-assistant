import { useState, useCallback } from 'react';
import type { Message } from '../types/chat';
import { generateUUID, sendStreamingMessage } from '../utils/api';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState(() => generateUUID());

  const addMessage = useCallback((content: string, type: 'user' | 'assistant', isStreaming = false) => {
    const message: Message = {
      id: generateUUID(),
      content,
      type,
      timestamp: new Date(),
      isStreaming
    };
    
    setMessages(prev => [...prev, message]);
    return message.id;
  }, []);

  const updateMessage = useCallback((messageId: string, content: string) => {
    setMessages(prev => 
      prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, content, isStreaming: false }
          : msg
      )
    );
  }, []);

  const appendToMessage = useCallback((messageId: string, chunk: string) => {
    setMessages(prev => 
      prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, content: msg.content + chunk }
          : msg
      )
    );
  }, []);

  const sendMessage = useCallback(async (query: string) => {
    if (!query.trim() || isLoading) return;

    setIsLoading(true);

    // Adiciona mensagem do usuário
    addMessage(query, 'user');

    // Adiciona mensagem do assistente (vazia, para streaming)
    const assistantMessageId = addMessage('', 'assistant', true);

    try {
      await sendStreamingMessage(
        query,
        userId,
        // onChunk
        (chunk: string) => {
          appendToMessage(assistantMessageId, chunk);
        },
        // onComplete
        () => {
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, isStreaming: false }
                : msg
            )
          );
          setIsLoading(false);
        },
        // onError
        (error: string) => {
          updateMessage(assistantMessageId, `❌ Erro: ${error}`);
          setIsLoading(false);
        }
      );
    } catch (error) {
      updateMessage(assistantMessageId, `❌ Erro: ${error}`);
      setIsLoading(false);
    }
  }, [userId, isLoading, addMessage, updateMessage, appendToMessage]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    userId,
    sendMessage,
    clearMessages
  };
}