"use client";

import React from 'react'
import { Paperclip, ArrowUp } from 'lucide-react'
import { useState } from 'react';

const InputBox = () => {

  const [isSendActive, setIsSendActive] = useState(false);
  const [isMessageActive, setIsMessageActive] = useState(false);

  return (
    <div>
      <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 w-[70%]">
        <div className="bg-input-area rounded-3xl border border-white/5 p-4">
          <input 
            type="text" 
            placeholder="Ask you document..." 
            className="w-full p-1 rounded-lg bg-input-area text-white placeholder-white/70 focus:outline-none  "
          />
          
          {/* Buttons container */}
          <div className="flex justify-between gap-2 mt-3">
            <button
              className="w-10 h-10 flex items-center justify-center rounded-full focus:outline-none border-1 border-white/10 text-gray-500"
              aria-label="Attach File"
            >
              <Paperclip size={20} />
            </button>
            <button
              className="w-10 h-10 flex items-center justify-center bg-button text-white rounded-full hover:bg-button/80 focus:outline-none"
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