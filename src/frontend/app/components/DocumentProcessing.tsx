"use client";

import React from 'react';
import { FileText, Check, Loader2, Zap, Database, Brain } from 'lucide-react';

const DocumentProcessing = () => {
  const steps = [
    { icon: FileText, label: "Upload", status: "completed" },
    { icon: Zap, label: "Extract", status: "completed" },
    { icon: Database, label: "Chunk", status: "in-progress" },
    { icon: Brain, label: "Embed", status: "pending" },
    { icon: Check, label: "Ready", status: "pending" }
  ];

  return (
    <div className="w-4/5 h-screen bg-chat-area relative">
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center space-y-8">
          <div className="text-center mb-6">
            <h3 className="text-white text-xl mb-2">Processing your document</h3>
            <p className="text-white/60">contract_agreement.pdf</p>
          </div>
          
          <div className="flex items-center space-x-8">
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <div key={index} className="flex flex-col items-center">
                  <div className={`
                    w-16 h-16 rounded-full flex items-center justify-center border-2 mb-3
                    ${step.status === "completed" ? "bg-green-500/20 border-green-400 text-green-400" :
                      step.status === "in-progress" ? "bg-blue-500/20 border-blue-400 text-blue-400" :
                      "bg-gray-500/20 border-gray-500 text-gray-500"}
                  `}>
                    {step.status === "in-progress" ? (
                      <Loader2 className="w-6 h-6 animate-spin" />
                    ) : (
                      <Icon className="w-6 h-6" />
                    )}
                  </div>
                  <span className={`text-sm ${
                    step.status === "completed" ? "text-green-400" :
                    step.status === "in-progress" ? "text-blue-400" : "text-gray-500"
                  }`}>
                    {step.label}
                  </span>
                  
                  {/* Progress line */}
                  {index < steps.length - 1 && (
                    <div className={`absolute w-8 h-0.5 mt-8 ml-16 ${
                      step.status === "completed" ? "bg-green-400" : "bg-gray-500"
                    }`} />
                  )}
                </div>
              );
            })}
          </div>
          
          <div className="text-center">
            <div className="text-white/70 text-sm">Step 3 of 5</div>
            <div className="w-64 bg-gray-700 rounded-full h-2 mt-2">
              <div className="bg-blue-400 h-2 rounded-full w-3/5"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentProcessing; 