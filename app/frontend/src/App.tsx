import { MantineProvider } from '@mantine/core';
import '@mantine/core/styles.css';
import { ChatInterface } from './components/ChatInterface';
import './chat.css';

function App() {
  return (
    <MantineProvider>
      <div style={{ backgroundColor: '#1a1b1e', minHeight: '100vh', margin: 0, padding: 0 }}>
        <ChatInterface />
      </div>
    </MantineProvider>
  );
}

export default App;
