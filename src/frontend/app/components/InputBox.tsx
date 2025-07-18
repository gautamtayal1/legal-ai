"use client";

import React from 'react'
import { ArrowUp } from 'lucide-react'

interface InputBoxProps {
  input: string;
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: (e: React.FormEvent) => void;
  isLoading?: boolean;
}

const InputBox: React.FC<InputBoxProps> = ({ input, handleInputChange, handleSubmit, isLoading }) => {
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="w-full flex justify-center px-4 pb-6">
      <div className="w-full max-w-[90%] sm:max-w-[600px] md:max-w-[600px] lg:max-w-[700px] xl:max-w-[800px] 2xl:max-w-[1000px]">
        <div className="bg-input-area rounded-2xl border border-white/5 p-3">
          <form onSubmit={handleSubmit} className="flex items-center gap-3">
            <input 
              type="text"
              value={input}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder="Ask your document..." 
              className="flex-1 p-2 rounded-lg bg-input-area text-white placeholder-white/70 focus:outline-none"
              disabled={isLoading}
            />
            
            <button
              type="submit"
              disabled={input.trim() === '' || isLoading}
              className="w-10 h-10 flex items-center justify-center bg-button text-white rounded-full hover:bg-button/80 focus:outline-none disabled:bg-gray-600 disabled:cursor-not-allowed flex-shrink-0"
              aria-label="Send Message"
            >
              <ArrowUp size={20} />
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default InputBox