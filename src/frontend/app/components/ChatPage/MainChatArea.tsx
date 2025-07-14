"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { MessageSquare } from "lucide-react";
import InputBox from "../InputBox";

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  created_at: string;
}

export default function MainChatArea() {
  const [messages, setMessages] = useState<Message[]>([]);

  // TODO: Fetch messages for this thread when messages API is implemented
  const hasMessages = messages.length > 0;

  // If there are messages, show the chat interface
  if (hasMessages) {
    return (
      <div className="w-full h-screen bg-chat-area relative">
        <div className="flex-1 overflow-y-auto">
          {/* Message list will go here */}
        </div>
        <InputBox />
      </div>
    );
  }

  // Show simple ready state when no messages
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
      
      <InputBox />
    </div>
  );
} 