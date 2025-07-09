"use client";

import React from 'react'
import { Paperclip, ArrowUp } from 'lucide-react'
import { useState, useRef } from 'react';
import { useUser } from '@clerk/nextjs';

const InputBox = () => {
  const { user } = useUser();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isSendActive, setIsSendActive] = useState(false);
  const [isMessageActive, setIsMessageActive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (file: File) => {
    if (!user?.id) {
      console.error('User not authenticated');
      return;
    }

    setIsUploading(true);
    
    try {
      // Generate a temporary message ID for now
      // TODO: Replace with actual message context when implemented
      const messageId = crypto.randomUUID();
      
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`http://${process.env.NEXT_PUBLIC_BACKEND_URL}/api/documents/upload?message_id=${messageId}&user_id=${user.id}`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        console.log('File uploaded successfully:', result);
        // TODO: Handle successful upload (e.g., show in chat, update UI)
      } else {
        const error = await response.text();
        console.error('Upload failed:', error);
        // TODO: Show error message to user
      }
    } catch (error) {
      console.error('Upload error:', error);
      // TODO: Show error message to user
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
    event.target.value = '';
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept=".pdf,.txt,.docx,.doc"
        style={{ display: 'none' }}
      />
      
      <div className="w-[90%] sm:w-[600px] md:w-[600px] lg:w-[700px] xl:w-[800px] 2xl:w-[1000px]">
        <div className="bg-input-area rounded-4xl border border-white/5 p-4">
          <input 
            type="text" 
            placeholder="Ask your document..." 
            className="w-full p-1 rounded-lg bg-input-area text-white placeholder-white/70 focus:outline-none"
          />
          
          <div className="flex justify-between gap-2 mt-3">
            <button
              onClick={handleUploadClick}
              disabled={isUploading}
              className={`w-10 h-10 flex items-center justify-center rounded-full focus:outline-none border-1 border-white/10 ${
                isUploading ? 'text-gray-600 cursor-not-allowed' : 'text-gray-500 hover:text-white'
              }`}
              aria-label="Attach File"
            >
              <Paperclip size={20} />
            </button>
            <button
              className="w-10 h-10 flex items-center justify-center bg-button text-white rounded-full hover:bg-button/80 focus:outline-none"
              disabled={!isSendActive || isUploading}
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