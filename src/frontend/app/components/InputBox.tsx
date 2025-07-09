"use client";

import React from 'react'
import { ArrowUp } from 'lucide-react'
import { useState } from 'react';

const InputBox = () => {
  const [isSendActive, setIsSendActive] = useState(false);
  const [isMessageActive, setIsMessageActive] = useState(false);

  return (
    <div>
      <div className="w-[90%] sm:w-[600px] md:w-[600px] lg:w-[700px] xl:w-[800px] 2xl:w-[1000px]">
        <div className="bg-input-area rounded-4xl border border-white/5 p-4">
          <input 
            type="text" 
            placeholder="Ask your document..." 
            className="w-full p-1 rounded-lg bg-input-area text-white placeholder-white/70 focus:outline-none"
          />
          
          <div className="flex justify-end gap-2 mt-3">
            <button
              className="w-10 h-10 flex items-center justify-center bg-button text-white rounded-full hover:bg-button/80 focus:outline-none"
              disabled={!isSendActive}
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