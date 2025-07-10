"use client";

import { useSearchParams } from 'next/navigation';
import { useState } from 'react';
import Sidebar from "@/components/Sidebar";
import MainChatArea from "@/app/components/ChatPage/MainChatArea";
import DocumentProcessing from "@/app/components/DocumentProcessing";

export default function ChatPage() {
  const searchParams = useSearchParams();
  const processingDocId = searchParams.get('processing');
  const filename = searchParams.get('filename');
  const [isProcessingComplete, setIsProcessingComplete] = useState(false);

  const handleProcessingComplete = () => {
    setIsProcessingComplete(true);
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      {processingDocId && !isProcessingComplete ? (
        <DocumentProcessing 
          documentId={parseInt(processingDocId)} 
          onComplete={handleProcessingComplete}
        />
      ) : (
        <DocumentProcessing 
          documentId={123}
          onComplete={handleProcessingComplete}
        />
      )}
    </div>
  );
}
