import { useChat } from '@ai-sdk/react';
import { useParams } from 'next/navigation';
import { useUser } from '@clerk/nextjs';
import { useEffect, useState } from 'react';
import axios from 'axios';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  created_at: string;
}

export const useChatSSE = () => {
  const params = useParams();
  const threadId = params.id as string;
  const { user } = useUser();
  const [initialMessages, setInitialMessages] = useState<Message[]>([]);
  const [isLoadingMessages, setIsLoadingMessages] = useState(true);
  
  useEffect(() => {
    const loadMessages = async () => {
      if (!user?.id || !threadId) return;
      
      try {
        setIsLoadingMessages(true);
        const response = await axios.get(
          `${process.env.NEXT_PUBLIC_API_URL}/api/messages/thread/${threadId}?user_id=${user.id}`
        );
        
        const transformedMessages = response.data.map((msg: Message) => ({
          id: msg.id,
          content: msg.content,
          role: msg.role,
          createdAt: new Date(msg.created_at)
        }));
        
        setInitialMessages(transformedMessages);
      } catch (error) {
        console.error('Failed to load messages:', error);
        setInitialMessages([]);
      } finally {
        setIsLoadingMessages(false);
      }
    };
    
    loadMessages();
  }, [user?.id, threadId]);
  
  const chat = useChat({
    api: `${process.env.NEXT_PUBLIC_API_URL}/api/query/stream`,
    streamProtocol: 'text',
    body: {
      thread_id: threadId,
      user_id: user?.id
    },
    initialMessages: initialMessages
  });
  
  return {
    ...chat,
    isLoadingMessages
  };
};
