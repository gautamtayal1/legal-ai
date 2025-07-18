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
      <div className="w-full h-screen bg-chat-area relative flex flex-col">
        <div className="flex-1 overflow-y-auto pb-6">
          <div className="max-w-[90%] sm:max-w-[600px] md:max-w-[600px] lg:max-w-[700px] xl:max-w-[800px] 2xl:max-w-[1000px] mx-auto pt-6">
            {messages.map((message) => (
              <div key={message.id} className={`mb-4 p-4 rounded-lg ${
                message.role === 'user' 
                  ? 'bg-input-area text-white ml-auto max-w-xs rounded-4xl' 
                  : 'text-white mr-auto max-w-full'
              }`}>
                <div className="whitespace-pre-wrap">
                  {message.content}
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="flex-shrink-0 h-[10vh] flex items-center">
          <InputBox handleSubmit={handleSubmit} input={input} handleInputChange={handleInputChange} isLoading={isLoading} />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen bg-chat-area relative flex flex-col">
      <div className="flex-1 flex flex-col items-center justify-center">
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
      <div className="flex-shrink-0 h-[10vh] flex items-center">
        <InputBox handleSubmit={handleSubmit} input={input} handleInputChange={handleInputChange} isLoading={isLoading} />
      </div>
    </div>
  );
}