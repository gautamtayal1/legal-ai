"use client";

import React from 'react';
import { Brain } from 'lucide-react';

interface DocumentProcessingProps {
  documentId: number;
  status: ProcessingStatus | null;
  onComplete?: () => void;
}

interface ProcessingStatus {
  id: number;
  filename?: string;
  processing_status: string;
  processing_step?: string | null;
  processing_progress?: number;
  error_message?: string | null;
  is_ready: boolean;
}

const DocumentProcessing = ({ status }: DocumentProcessingProps) => {
  const currentStatus = status || {
    id: 0,
    filename: 'Processing documents...',
    processing_status: 'uploading',
    processing_step: 'uploading',
    is_ready: false
  };

  return (
    <div className="w-full h-screen bg-chat-area relative flex flex-col overflow-hidden">
      
      <div className="flex-1 flex items-center justify-center relative z-10">
        <div className="text-center">
          {/* Quantum processing orb - enhanced */}
          <div className="mb-12 relative">
            <div className="w-48 h-48 mx-auto relative">
              {/* Outer quantum ring with multiple layers */}
              <div className="absolute inset-0 border-2 border-button/40 rounded-full animate-spin" style={{ animationDuration: '8s' }}>
                <div className="w-4 h-4 bg-gradient-to-r from-button to-purple-400 rounded-full absolute -top-2 left-1/2 transform -translate-x-1/2 animate-pulse shadow-lg">
                  <div className="absolute inset-0 bg-gradient-to-r from-button to-purple-400 rounded-full animate-ping opacity-75"></div>
                </div>
                <div className="w-4 h-4 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full absolute top-1/2 -right-2 transform -translate-y-1/2 animate-pulse shadow-lg">
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full animate-ping opacity-75"></div>
                </div>
                <div className="w-4 h-4 bg-gradient-to-r from-pink-400 to-button rounded-full absolute -bottom-2 left-1/2 transform -translate-x-1/2 animate-pulse shadow-lg">
                  <div className="absolute inset-0 bg-gradient-to-r from-pink-400 to-button rounded-full animate-ping opacity-75"></div>
                </div>
                <div className="w-4 h-4 bg-gradient-to-r from-button to-purple-400 rounded-full absolute top-1/2 -left-2 transform -translate-y-1/2 animate-pulse shadow-lg">
                  <div className="absolute inset-0 bg-gradient-to-r from-button to-purple-400 rounded-full animate-ping opacity-75"></div>
                </div>
              </div>
              
              {/* Secondary orbital ring */}
              <div className="absolute inset-4 border border-purple-400/50 rounded-full animate-spin" style={{ animationDuration: '5s', animationDirection: 'reverse' }}>
                <div className="w-3 h-3 bg-purple-400 rounded-full absolute -top-1.5 left-1/2 transform -translate-x-1/2 animate-bounce"></div>
                <div className="w-3 h-3 bg-pink-400 rounded-full absolute -bottom-1.5 left-1/2 transform -translate-x-1/2 animate-bounce" style={{ animationDelay: '0.7s' }}></div>
                <div className="w-3 h-3 bg-button rounded-full absolute top-1/2 -right-1.5 transform -translate-y-1/2 animate-bounce" style={{ animationDelay: '1.4s' }}></div>
                <div className="w-3 h-3 bg-purple-400 rounded-full absolute top-1/2 -left-1.5 transform -translate-y-1/2 animate-bounce" style={{ animationDelay: '2.1s' }}></div>
              </div>
              
              {/* Middle energy ring */}
              <div className="absolute inset-8 border border-button/60 rounded-full animate-spin" style={{ animationDuration: '3s' }}>
                <div className="w-2 h-2 bg-button rounded-full absolute -top-1 left-1/2 transform -translate-x-1/2 animate-bounce"></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full absolute -bottom-1 left-1/2 transform -translate-x-1/2 animate-bounce" style={{ animationDelay: '0.5s' }}></div>
                <div className="w-2 h-2 bg-pink-400 rounded-full absolute top-1/2 -right-1 transform -translate-y-1/2 animate-bounce" style={{ animationDelay: '1s' }}></div>
                <div className="w-2 h-2 bg-button rounded-full absolute top-1/2 -left-1 transform -translate-y-1/2 animate-bounce" style={{ animationDelay: '1.5s' }}></div>
              </div>
              
              {/* Inner core with enhanced effects */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-24 h-24 bg-gradient-to-br from-button/40 via-purple-400/40 to-pink-400/40 rounded-full flex items-center justify-center animate-pulse shadow-2xl relative">
                  <div className="absolute inset-0 bg-gradient-to-br from-button/20 via-purple-400/20 to-pink-400/20 rounded-full animate-ping"></div>
                  <Brain className="w-12 h-12 text-button animate-pulse relative z-10" />
                </div>
              </div>
              
              {/* Enhanced energy waves */}
              <div className="absolute inset-0 border border-button/30 rounded-full animate-ping"></div>
              <div className="absolute inset-2 border border-purple-400/25 rounded-full animate-ping" style={{ animationDelay: '0.8s' }}></div>
              <div className="absolute inset-4 border border-pink-400/20 rounded-full animate-ping" style={{ animationDelay: '1.6s' }}></div>
              <div className="absolute inset-6 border border-button/15 rounded-full animate-ping" style={{ animationDelay: '2.4s' }}></div>
            </div>
          </div>
          
          {/* Holographic title with enhanced effects */}
          <h2 className="text-white text-5xl font-light mb-8 relative">
            <span className="relative z-10 bg-gradient-to-r from-button via-purple-400 to-pink-400 bg-clip-text text-transparent animate-pulse">
              🧠AI Processing
            </span>
            <div className="absolute inset-0 text-button/30 blur-sm animate-pulse">🧠AI Processing</div>
            <div className="absolute inset-0 text-purple-400/20 blur-lg animate-pulse">🧠AI Processing</div>
            <div className="absolute inset-0 text-pink-400/10 blur-xl animate-pulse">🧠AI Processing</div>
            
            {/* Scanning line effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-button/30 to-transparent animate-pulse" style={{animationDuration: '3s'}}></div>
          </h2>
          
          {/* Status with typewriter effect */}
          <div className="mb-8 h-16 flex items-center justify-center">
            <p className="text-white/80 text-lg font-mono">
              {currentStatus.filename && currentStatus.filename !== 'Processing documents...' 
                ? `Analyzing: ${currentStatus.filename}`
                : 'Extracting knowledge patterns...'
              }
            </p>
          </div>
          
          {/* Quantum progress */}
          <div className="w-80 h-2 bg-black/30 rounded-full mx-auto mb-6 overflow-hidden border border-white/10">
            <div className="h-full bg-gradient-to-r from-button via-purple-400 to-pink-400 rounded-full animate-pulse relative">
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentProcessing; 