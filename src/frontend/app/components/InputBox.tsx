"use client";

import React from 'react'
import { ArrowUp } from 'lucide-react'
import { useState } from 'react';
import axios from 'axios';

const InputBox = () => {
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);

  const handleSend = async () => {
    if (message.trim() === '') return;
    
    setIsSending(true);

    console.log('Sending message:', message);
    const response = await axios.post('/api/query', { query: message });
    console.log('Response:', response);

    setMessage('');
    setIsSending(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div>
      <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 w-[90%] sm:w-[600px] md:w-[600px] lg:w-[700px] xl:w-[800px] 2xl:w-[1000px]">
        <div className="bg-input-area rounded-2xl border border-white/5 p-3">
          <div className="flex items-center gap-3">
            <input 
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask your document..." 
              className="flex-1 p-2 rounded-lg bg-input-area text-white placeholder-white/70 focus:outline-none"
              disabled={isSending}
            />
            
            <button
              onClick={handleSend}
              disabled={message.trim() === '' || isSending}
              className="w-10 h-10 flex items-center justify-center bg-button text-white rounded-full hover:bg-button/80 focus:outline-none disabled:bg-gray-600 disabled:cursor-not-allowed flex-shrink-0"
              aria-label="Send Message"
            >
              <ArrowUp size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InputBox