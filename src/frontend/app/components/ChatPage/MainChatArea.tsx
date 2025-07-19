"use client";

import { MessageSquare } from "lucide-react";
import InputBox from "../InputBox";
import { useChatSSE } from "@/app/hooks/useChatSSE";
import MessageFormatter from "./MessageFormatter";

export default function MainChatArea() {
  const { messages, input, handleInputChange, handleSubmit, isLoading, isLoadingMessages } = useChatSSE();

  const hasMessages = messages.length > 0;

  // Show blank screen while loading messages
  if (isLoadingMessages) {
    return (
      <>
        <div className="fixed inset-0 bg-chat-area"></div>
        <div className="w-full h-screen relative flex flex-col">
          <div className="flex-1"></div>
        </div>
      </>
    );
  }

  if (hasMessages) {
    return (
      <>
        <div className="fixed inset-0 bg-chat-area"></div>
        <div className="w-full h-screen relative flex flex-col">
          <div className="flex-1 overflow-y-auto pb-6">
            <div className="max-w-[90%] sm:max-w-[600px] md:max-w-[600px] lg:max-w-[700px] xl:max-w-[800px] 2xl:max-w-[1000px] mx-auto pt-6">
              {messages.map((message) => (
                <div key={message.id} className={`mb-4 flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}>
                  <div className={`p-4 rounded-2xl ${
                    message.role === 'user' 
                      ? 'bg-input-area text-gray-100 max-w-[70%] text-[17px]' 
                      : 'text-gray-100 max-w-full text-[17px]'
                  }`}>
                    <MessageFormatter content={message.content} role={message.role as 'user' | 'assistant'} />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="flex-shrink-0 h-[10vh] flex items-center">
            <InputBox handleSubmit={handleSubmit} input={input} handleInputChange={handleInputChange} isLoading={isLoading} />
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="fixed inset-0 bg-chat-area"></div>
      <div className="w-full h-screen relative flex flex-col overflow-hidden">
        
        <div className="flex-1 flex items-center justify-center relative z-10">
          <div className="text-center">
            {/* Enhanced harmonious chat orb */}
            <div className="mb-12 relative">
              <div className="w-44 h-44 mx-auto relative">
                {/* Outer harmony ring with enhanced effects */}
                <div className="absolute inset-0 border-2 border-button/40 rounded-full animate-spin" style={{ animationDuration: '25s' }}>
                  <div className="w-3 h-3 bg-gradient-to-r from-button to-purple-400 rounded-full absolute -top-1.5 left-1/2 transform -translate-x-1/2 animate-pulse shadow-lg">
                    <div className="absolute inset-0 bg-gradient-to-r from-button to-purple-400 rounded-full animate-ping opacity-60"></div>
                  </div>
                  <div className="w-3 h-3 bg-gradient-to-r from-purple-400 to-button rounded-full absolute -bottom-1.5 left-1/2 transform -translate-x-1/2 animate-pulse shadow-lg">
                    <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-button rounded-full animate-ping opacity-60"></div>
                  </div>
                  <div className="w-3 h-3 bg-gradient-to-r from-button to-purple-400 rounded-full absolute top-1/2 -right-1.5 transform -translate-y-1/2 animate-pulse shadow-lg">
                    <div className="absolute inset-0 bg-gradient-to-r from-button to-purple-400 rounded-full animate-ping opacity-60"></div>
                  </div>
                  <div className="w-3 h-3 bg-gradient-to-r from-purple-400 to-button rounded-full absolute top-1/2 -left-1.5 transform -translate-y-1/2 animate-pulse shadow-lg">
                    <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-button rounded-full animate-ping opacity-60"></div>
                  </div>
                </div>
                
                {/* Middle harmony ring */}
                <div className="absolute inset-6 border border-button/50 rounded-full animate-spin" style={{ animationDuration: '15s', animationDirection: 'reverse' }}>
                  <div className="w-2 h-2 bg-button/70 rounded-full absolute -top-1 left-1/2 transform -translate-x-1/2 animate-bounce"></div>
                  <div className="w-2 h-2 bg-purple-400/70 rounded-full absolute -bottom-1 left-1/2 transform -translate-x-1/2 animate-bounce" style={{ animationDelay: '0.5s' }}></div>
                  <div className="w-2 h-2 bg-button/70 rounded-full absolute top-1/2 -right-1 transform -translate-y-1/2 animate-bounce" style={{ animationDelay: '1s' }}></div>
                  <div className="w-2 h-2 bg-purple-400/70 rounded-full absolute top-1/2 -left-1 transform -translate-y-1/2 animate-bounce" style={{ animationDelay: '1.5s' }}></div>
                </div>
                
                {/* Inner glow ring */}
                <div className="absolute inset-8 border border-purple-400/40 rounded-full animate-spin" style={{ animationDuration: '8s' }}>
                  <div className="w-1.5 h-1.5 bg-button/80 rounded-full absolute -top-0.5 left-1/2 transform -translate-x-1/2 animate-pulse"></div>
                  <div className="w-1.5 h-1.5 bg-purple-400/80 rounded-full absolute -bottom-0.5 left-1/2 transform -translate-x-1/2 animate-pulse"></div>
                  <div className="w-1.5 h-1.5 bg-button/80 rounded-full absolute top-1/2 -right-0.5 transform -translate-y-1/2 animate-pulse"></div>
                  <div className="w-1.5 h-1.5 bg-purple-400/80 rounded-full absolute top-1/2 -left-0.5 transform -translate-y-1/2 animate-pulse"></div>
                </div>
                
                {/* Central ready icon with enhanced glow */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-24 h-24 bg-gradient-to-br from-button/40 via-purple-400/40 to-button/40 rounded-full flex items-center justify-center shadow-2xl relative">
                    <div className="absolute inset-0 bg-gradient-to-br from-button/20 via-purple-400/20 to-button/20 rounded-full animate-ping"></div>
                    <MessageSquare className="w-12 h-12 text-button relative z-10 animate-pulse" />
                  </div>
                </div>
                
              </div>
            </div>
            
            {/* Enhanced holographic ready title */}
            <h1 className="text-white text-5xl font-light mb-8 relative">
              <span className="relative z-10 bg-gradient-to-r from-button via-purple-400 to-button bg-clip-text text-transparent animate-pulse">
                Ready to Chat
              </span>
              <div className="absolute inset-0 text-button/30 blur-sm animate-pulse">Ready to Chat</div>
              <div className="absolute inset-0 text-purple-400/20 blur-lg animate-pulse">Ready to Chat</div>
              <div className="absolute inset-0 text-button/10 blur-xl animate-pulse">✨ Ready to Chat</div>
              
              {/* Scanning line effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-button/20 to-transparent animate-pulse" style={{animationDuration: '4s'}}></div>
            </h1>
            
            {/* Enhanced system status */}
            <div className="flex items-center justify-center space-x-6">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-button rounded-full animate-pulse relative">
                  <div className="absolute inset-0 bg-button rounded-full animate-ping opacity-60"></div>
                </div>
                <span className="text-button/90 text-sm font-mono">Knowledge Base Ready</span>
              </div>   
            </div>
          </div>
        </div>      
        
        <div className="flex-shrink-0 h-[10vh] flex items-center">
          <InputBox handleSubmit={handleSubmit} input={input} handleInputChange={handleInputChange} isLoading={isLoading} />
        </div>
      </div>
    </>
  );
}