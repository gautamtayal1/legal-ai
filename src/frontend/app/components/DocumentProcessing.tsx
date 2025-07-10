"use client";

import React, { useState, useEffect } from 'react';
import { FileText, Check, Loader2, Zap, Database, Brain } from 'lucide-react';

interface DocumentProcessingProps {
  documentId: number;
  onComplete?: () => void;
}

interface ProcessingStatus {
  id: number;
  filename: string;
  processing_status: string;
  processing_step: string | null;
  processing_progress: number;
  error_message: string | null;
  is_ready: boolean;
}

const DocumentProcessing = ({ documentId, onComplete }: DocumentProcessingProps) => {
  const [status, setStatus] = useState<ProcessingStatus | null>(null);

  // TEMPORARY: Change status for demonstration
  useEffect(() => {
    // Simulate status changes for demonstration purposes
    let isMounted = true;
    const timeouts: NodeJS.Timeout[] = [];

    // Example sequence of fake status updates
    const fakeStatuses: ProcessingStatus[] = [
      {
        id: documentId,
        filename: "example.pdf",
        processing_status: "processing",
        processing_step: "Initializing document processing...",
        processing_progress: 10,
        error_message: null,
        is_ready: false,
      },
      {
        id: documentId,
        filename: "example.pdf",
        processing_status: "extracting",
        processing_step: "Extracting text from document...",
        processing_progress: 30,
        error_message: null,
        is_ready: false,
      },
      {
        id: documentId,
        filename: "example.pdf",
        processing_status: "chunking",
        processing_step: "Breaking document into meaningful sections...",
        processing_progress: 60,
        error_message: null,
        is_ready: false,
      },
      {
        id: documentId,
        filename: "example.pdf",
        processing_status: "embedding",
        processing_step: "Generating embeddings for search...",
        processing_progress: 85,
        error_message: null,
        is_ready: false,
      },
      {
        id: documentId,
        filename: "example.pdf",
        processing_status: "ready",
        processing_step: "Document ready for chat!",
        processing_progress: 100,
        error_message: null,
        is_ready: true,
      },
    ];

    // Simulate the status changes over time
    fakeStatuses.forEach((fakeStatus, idx) => {
      const timeout = setTimeout(() => {
        if (isMounted) {
          setStatus(fakeStatus);
          // Call onComplete when ready
          if (fakeStatus.is_ready && onComplete) {
            onComplete();
          }
        }
      }, idx * 1500);
      timeouts.push(timeout);
    });

    return () => {
      isMounted = false;
      timeouts.forEach(clearTimeout);
    };
  }, [documentId, onComplete]);

  const getStepStatus = (stepName: string, currentStatus: string, currentStep: string | null) => {
    const steps = ['pending', 'processing', 'extracting', 'chunking', 'embedding', 'ready'];
    const currentIndex = steps.indexOf(currentStatus);
    const stepIndex = steps.indexOf(stepName);
    
    if (currentStatus === 'failed') return 'error';
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex || (stepName === 'processing' && currentStep)) return 'in-progress';
    return 'pending';
  };

  const steps = [
    { key: 'processing', icon: FileText, label: "Upload" },
    { key: 'extracting', icon: Zap, label: "Extract" },
    { key: 'chunking', icon: Database, label: "Chunk" },
    { key: 'embedding', icon: Brain, label: "Embed" },
    { key: 'ready', icon: Check, label: "Ready" }
  ];

  if (!status) {
    return (
      <div className="w-4/5 h-screen bg-chat-area relative overflow-y-auto">
        <div className="flex items-center justify-center min-h-full">
          <Loader2 className="w-8 h-8 text-white animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-4/5 h-screen bg-chat-area relative overflow-y-auto">
      <div className="flex flex-col items-center justify-center min-h-full px-8 py-16">
        <div className="w-full max-w-2xl">
          
          {/* Header */}
          <div className="text-center mb-12">
            <h2 className="text-white text-2xl font-light mb-3">Processing Document</h2>
            <p className="text-white/60">{status.filename}</p>
          </div>
          
          {/* Vertical Timeline */}
          <div className="space-y-0 mb-12">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const stepStatus = getStepStatus(step.key, status.processing_status, status.processing_step);
              const isActive = stepStatus === "in-progress";
              const isCompleted = stepStatus === "completed";
              
              return (
                <div key={index} className="flex items-start space-x-4 relative h-24">
                  {/* Timeline dot and connecting line */}
                  <div className="flex flex-col items-center relative z-10">
                    <div 
                      className={`w-10 h-10 rounded-full flex items-center justify-center border transition-all duration-300 ${
                        isCompleted 
                          ? "bg-button border-button" 
                          : isActive 
                            ? "bg-button/20 border-button" 
                            : "bg-input-area border-white/20"
                      }`}
                    >
                      {isActive ? (
                        <Loader2 className="w-5 h-5 text-button animate-spin" />
                      ) : isCompleted ? (
                        <Check className="w-5 h-5 text-white" />
                      ) : (
                        <Icon className="w-5 h-5 text-white/40" />
                      )}
                    </div>
                    
                    {/* Connecting line to next step */}
                    {index < steps.length - 1 && (
                      <div 
                        className={`w-0.5 h-14 transition-colors duration-300 ${
                          isCompleted ? "bg-button" : "bg-white/10"
                        }`}
                      />
                    )}
                  </div>
                  
                  {/* Content */}
                  <div className="flex-1 h-full flex flex-col justify-start pt-2">
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
                      
                      {isCompleted && (
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