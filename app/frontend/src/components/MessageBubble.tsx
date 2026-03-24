import { Paper, Text, Group, Avatar, Loader, Box } from '@mantine/core';
import { IconUser, IconRobot } from '@tabler/icons-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import './markdown.css';
import type { Message } from '../types/chat';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.type === 'user';

  return (
    <Box w="100%">
      <Group
        gap="sm"
        align="flex-start"
        justify={isUser ? 'flex-end' : 'flex-start'}
      >
        {!isUser && (
          <Avatar 
            size="md" 
            radius="xl"
            style={{
              backgroundColor: '#2f9e44',
              color: 'white'
            }}
          >
            <IconRobot size={24} color="white" />
          </Avatar>
        )}
        
        <Box maw="60%">
          <Paper
            p="md"
            radius="lg"
            withBorder
            style={{
              backgroundColor: isUser ? '#2b8a3e' : '#2c2e33',
              color: isUser ? '#ffffff' : '#c1c2c5',
              borderColor: isUser ? '#51cf66' : '#373a40'
            }}
          >
            {message.content ? (
              <Box className="markdown-content">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkBreaks]}
                >
                  {message.content}
                </ReactMarkdown>
              </Box>
            ) : (
              message.isStreaming ? (
                <Box>
                  <Group gap="xs">
                    <Loader size="xs" />
                    <Box component="span" style={{ color: '#868e96', fontSize: '14px' }}>Digitando...</Box>
                  </Group>
                </Box>
              ) : null
            )}
          </Paper>
          
          <Text 
            size="xs" 
            ta={isUser ? 'right' : 'left'}
            mt={4}
            style={{ color: '#868e96' }}
          >
            {message.timestamp.toLocaleTimeString()}
          </Text>
        </Box>

        {isUser && (
          <Avatar 
            size="md" 
            radius="xl"
            style={{
              backgroundColor: '#51cf66',
              color: 'white'
            }}
          >
            <IconUser size={20} color="white" />
          </Avatar>
        )}
      </Group>
    </Box>
  );
}