import React, { useState, useRef, useEffect } from 'react';
import { 
  Container, 
  Paper, 
  Title, 
  Text, 
  Stack, 
  Group, 
  TextInput, 
  ActionIcon, 
  ScrollArea, 
  Center,
  List
} from '@mantine/core';
import { IconSend, IconStethoscope } from '@tabler/icons-react';
import { MessageBubble } from './MessageBubble';
import { useChat } from '../hooks/useChat';

export function ChatInterface() {
  const [inputMessage, setInputMessage] = useState('');
  const { messages, isLoading, sendMessage } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const viewport = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    await sendMessage(inputMessage);
    setInputMessage('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <Container size="xl" h="100vh" p={0} style={{ maxWidth: '90%', backgroundColor: '#1a1b1e' }}>
      <Stack h="100vh" gap={0} style={{ backgroundColor: '#1a1b1e' }}>
        {/* Header */}
        <Paper p="md" style={{ borderRadius: 0, backgroundColor: '#2f9e44', border: 'none' }}>
          <Group gap="sm">
            <IconStethoscope size={24} color="white" />
            <Title order={3} style={{ color: 'white' }}>Assistente Médico</Title>
          </Group>
        </Paper>

        {/* Messages Area */}
        <ScrollArea flex={1} viewportRef={viewport} p="md" style={{ backgroundColor: '#1a1b1e' }}>
          {messages.length === 0 ? (
            <Center h={400} style={{ backgroundColor: '#1a1b1e' }}>
              <Stack align="center" gap="md">
                <IconStethoscope size={48} style={{ color: '#51cf66' }} />
                <Title order={2} ta="center" style={{ color: '#c1c2c5' }}>Olá! 👋</Title>
                <Text ta="center" style={{ color: '#868e96' }}>
                  Sou seu assistente médico. Como posso ajudá-lo hoje?
                </Text>
                <Paper withBorder p="md" maw={400} radius="md" style={{ backgroundColor: '#2c2e33', borderColor: '#373a40' }}>
                  <Text size="sm" fw={500} mb="xs" style={{ color: '#c1c2c5' }}>Exemplos de perguntas:</Text>
                  <List size="sm" spacing={4} style={{ color: '#a6a7ab' }}>
                    <List.Item>Quais são os sintomas de asma?</List.Item>
                    <List.Item>Protocolo para dor torácica</List.Item>
                    <List.Item>Dados do paciente com CPF 12345678901</List.Item>
                  </List>
                </Paper>
              </Stack>
            </Center>
          ) : (
            <Stack gap="xl" align="stretch" w="100%" maw="800px" mx="auto">
              {messages.map(message => (
                <MessageBubble key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </Stack>
          )}
        </ScrollArea>

        {/* Input Area */}
        <Paper p="md" style={{ borderRadius: 0, backgroundColor: '#1a1b1e', border: 'none' }}>
          <form onSubmit={handleSubmit}>
              <TextInput
                flex={1}
                placeholder={isLoading ? "Aguarde a resposta..." : "Digite sua pergunta médica..."}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.currentTarget.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
                radius="md"
                size="md"
                styles={{
                  input: {
                    backgroundColor: '#2c2e33',
                    borderColor: '#373a40',
                    color: '#ffffff',
                    '&::placeholder': {
                      color: '#909296'
                    }
                  }
                }}
                rightSection={
                  <ActionIcon
                    type="submit"
                    disabled={isLoading || !inputMessage.trim()}
                    variant="transparent"
                    size="sm"
                    radius="md"
                    style={{ 
                      backgroundColor: 'transparent',
                      color: '#ffffff',
                      '&:hover': {
                        backgroundColor: 'rgba(255, 255, 255, 0.1)'
                      }
                    }}
                  >
                    <IconSend size={20} stroke={2} style={{ color: '#ffffff' }} />
                  </ActionIcon>
                }
              />
            </form>
        </Paper>
      </Stack>
    </Container>
  );
}