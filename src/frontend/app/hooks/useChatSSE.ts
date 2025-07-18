import { useChat } from '@ai-sdk/react';
import { useParams } from 'next/navigation';

export const useChatSSE = () => {
  const params = useParams();
  const threadId = params.id as string;
  
  return useChat({
    api: `${process.env.NEXT_PUBLIC_API_URL}/api/query/stream`,
    streamProtocol: 'text',
    body: {
      thread_id: threadId
    }
  });
};
