"use client";

import { MessageSquare } from "lucide-react";
import InputBox from "../InputBox";
import { useChatSSE } from "@/app/hooks/useChatSSE";

// interface Message {
//   id: string;
//   content: string;
//   role: 'user' | 'assistant';
//   created_at: string;
// }

export default function MainChatArea() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChatSSE();

  const hasMessages = messages.length > 0;

  if (hasMessages) {
    return (
      <div className="w-full h-screen bg-chat-area relative">
        <div className="flex-1 overflow-y-auto">
          {messages.map((message) => (
            <div key={message.id} className={`mb-4 p-4 rounded-lg ${
              message.role === 'user' 
                ? 'bg-blue-600 text-white ml-auto max-w-xs' 
                : 'bg-gray-700 text-white mr-auto max-w-2xl'
            }`}>
              <div className="text-sm font-medium mb-1">
                {message.role === 'user' ? 'You' : 'Assistant'}
              </div>
              <div className="whitespace-pre-wrap">
                {message.content}
              </div>
            </div>
          ))}
        </div>
        <InputBox handleSubmit={handleSubmit} input={input} handleInputChange={handleInputChange} isLoading={isLoading} />
      </div>
    );
  }

  return (
    <div className="w-full h-screen bg-chat-area relative">
      <div className="flex flex-col items-center justify-center h-full">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-button/20 rounded-xl flex items-center justify-center mx-auto mb-6">
            <MessageSquare className="w-8 h-8 text-button" />
          </div>
          <h1 className="text-white text-2xl font-light mb-3">
            Ready to chat
          </h1>
          <p className="text-white/60">
            Ask me anything about your documents
          </p>
        </div>
      </div>      
      <InputBox handleSubmit={handleSubmit} input={input} handleInputChange={handleInputChange} isLoading={isLoading} />
    </div>
  );
}