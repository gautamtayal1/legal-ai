"use client";

import React from 'react';
import { FileText, Check, Loader2, Zap, Database, Brain } from 'lucide-react';

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

const DocumentProcessing = ({ documentId, status, onComplete }: DocumentProcessingProps) => {
  const steps = [
    { key: 'uploading', icon: FileText, label: "Upload" },
    { key: 'processing', icon: Zap, label: "Extract" },
    { key: 'chunking', icon: Database, label: "Chunk" },
    { key: 'indexing', icon: Brain, label: "Embed" },
    { key: 'ready', icon: Check, label: "Ready" }
  ];

  if (!status) {
    return (
      <div className="w-full h-screen bg-chat-area relative overflow-y-auto">
        <div className="flex items-center justify-center min-h-full">
          <Loader2 className="w-8 h-8 text-white animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen bg-chat-area relative overflow-y-auto">
      <div className="flex flex-col items-center justify-center min-h-full px-8 py-16">
        <div className="w-full max-w-2xl">
          
          {/* Header */}
          <div className="text-center mb-12">
            <h2 className="text-white text-2xl font-light mb-3">Processing Documents</h2>
            <p className="text-white/60">{status.filename || `Document ${documentId}`}</p>
          </div>
          
          {/* Vertical Timeline */}
          <div className="relative">
            {steps.map((step, index) => {
              // Check if this step is completed (current status is at this step or beyond)
              const currentStepIndex = steps.findIndex(s => s.key === status.processing_status);
              const isCompleted = currentStepIndex > index || (currentStepIndex === index && status.processing_status === 'ready');
              const isActive = step.key === status.processing_status;
              const isLastStep = index === steps.length - 1;
              
              return (
                <div key={step.key} className="relative flex items-start mb-8 last:mb-0">
                  
                  {/* Connector Line */}
                  {!isLastStep && (
                    <div 
                      className={`absolute left-6 top-12 w-0.5 h-8 transition-colors duration-500 ${
                        isCompleted
                          ? "bg-button" 
                          : "bg-white/20"
                      }`}
                    />
                  )}
                  
                  {/* Icon Circle */}
                  <div 
                    className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-500 ${
                      isCompleted 
                        ? "bg-button border-button text-black" 
                        : isActive 
                          ? "bg-chat-area border-button text-button animate-pulse" 
                          : "bg-chat-area border-white/20 text-white/40"
                    }`}
                  >
                    {isActive && !isCompleted ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <step.icon className="w-5 h-5" />
                    )}
                  </div>
                  
                  {/* Content */}
                  <div className="flex-1 h-full flex flex-col justify-start pt-2 ml-6">
                    <div className="flex items-center justify-between mb-1">
                      <h3 
                        className={`font-medium transition-colors duration-300 ${
                          isCompleted 
                            ? "text-button" 
                            : isActive 
                              ? "text-white" 
                              : "text-white/40"
                        }`}
                      >
                        {step.label === "Upload" ? "Document Upload" :
                         step.label === "Extract" ? "Text Extraction" :
                         step.label === "Chunk" ? "Content Analysis" :
                         step.label === "Embed" ? "Vector Processing" :
                         "Ready for Chat"}
                      </h3>
                      {isCompleted && (
                        <span className="text-button text-sm">✓</span>
                      )}
                    </div>
                    
                    <div className="h-6 flex items-start">
                      {isActive && status.processing_step && (
                        <p className="text-white/70 text-sm animate-pulse">
                          {status.processing_step}
                        </p>
                      )}
                      
                      {isCompleted && !isActive && (
                        <p className="text-white/50 text-sm">Complete</p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          
        </div>
      </div>
    </div>
  );
};

export default DocumentProcessing; 