"use client";

import { useParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';
import axios from 'axios';
import Sidebar, { MainContent } from "@/components/Sidebar";
import MainChatArea from "@/app/components/ChatPage/MainChatArea";
import DocumentProcessing from "@/app/components/DocumentProcessing";

interface DocumentStatus {
  id: number;
  filename: string;
  processing_status: string;
  error_message: string | null;
  is_ready: boolean;
}

interface CombinedStatus {
  id: number;
  filename: string;
  processing_status: string;
  processing_step: string;
  error_message: string | null;
  is_ready: boolean;
}

export default function ChatPage() {
  const params = useParams();
  const threadId = params.id as string;
  const { user } = useUser();
  
  const [documents, setDocuments] = useState<DocumentStatus[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Status mapping from DB to UI
  const mapDbStatusToUi = (dbStatus: string): string => {
    switch (dbStatus) {
      case 'pending':
        return 'uploading';
      case 'uploaded':
      case 'extracting':
      case 'processing':
        return 'processing';
      case 'chunking':
        return 'chunking';
      case 'indexing':
        return 'indexing';
      case 'ready':
        return 'ready';
      case 'failed':
        return 'failed';
      default:
        return 'uploading';
    }
  };

  // Get status priority (lower number = earlier in process)
  const getStatusPriority = (status: string): number => {
    switch (status) {
      case 'uploading': return 1;
      case 'processing': return 2;
      case 'chunking': return 3;
      case 'indexing': return 4;
      case 'ready': return 5;
      case 'failed': return 0; // Failed has highest priority to show error
      default: return 1;
    }
  };

  // Get processing step description
  const getProcessingStep = (status: string, filename: string): string => {
    switch (status) {
      case 'uploading':
        return `Uploading ${filename}...`;
      case 'processing':
        return `Extracting text from ${filename}...`;
      case 'chunking':
        return `Breaking ${filename} into meaningful sections...`;
      case 'indexing':
        return `Generating embeddings for ${filename}...`;
      case 'ready':
        return `${filename} is ready for chat!`;
      case 'failed':
        return `Failed to process ${filename}`;
      default:
        return `Processing ${filename}...`;
    }
  };

  // Find the slowest document and create combined status
  const getCombinedStatus = (documents: DocumentStatus[]): CombinedStatus | null => {
    if (documents.length === 0) return null;

    // First check for failed documents
    const failedDoc = documents.find(doc => doc.processing_status === 'failed');
    if (failedDoc) {
      return {
        id: failedDoc.id,
        filename: failedDoc.filename,
        processing_status: 'failed',
        processing_step: getProcessingStep('failed', failedDoc.filename),
        error_message: failedDoc.error_message,
        is_ready: false
      };
    }

    // Find the document with the lowest status (furthest behind)
    let slowestDoc = documents[0];
    let lowestPriority = getStatusPriority(mapDbStatusToUi(slowestDoc.processing_status));

    for (const doc of documents) {
      const uiStatus = mapDbStatusToUi(doc.processing_status);
      const priority = getStatusPriority(uiStatus);
      
      if (priority < lowestPriority) {
        slowestDoc = doc;
        lowestPriority = priority;
      }
    }

    const uiStatus = mapDbStatusToUi(slowestDoc.processing_status);
    
    // Special handling for multiple documents
    let processingStep;
    if (documents.length > 1) {
      const completedCount = documents.filter(doc => doc.is_ready).length;
      const totalCount = documents.length;
      
      if (uiStatus === 'ready') {
        processingStep = `All ${totalCount} documents are ready for chat!`;
      } else {
        processingStep = `${getProcessingStep(uiStatus, slowestDoc.filename)} (${completedCount}/${totalCount} completed)`;
      }
    } else {
      processingStep = getProcessingStep(uiStatus, slowestDoc.filename);
    }

    return {
      id: slowestDoc.id,
      filename: documents.length > 1 ? `${documents.length} documents` : slowestDoc.filename,
      processing_status: uiStatus,
      processing_step: processingStep,
      error_message: slowestDoc.error_message,
      is_ready: documents.every(doc => doc.is_ready)
    };
  };

  useEffect(() => {
    let isMounted = true;
    let pollInterval: NodeJS.Timeout | null = null;
    
    // Clear documents if no user
    if (!user?.id) {
      setDocuments([]);
      setError(null);
      return;
    }
    
    const fetchDocuments = async () => {
      try {
        const response = await axios.get(
          `${process.env.NEXT_PUBLIC_API_URL}/api/documents/thread/${threadId}?user_id=${user.id}`
        );
        
        if (isMounted) {
          const newDocuments = response.data;
          setDocuments(newDocuments);
          setError(null);
          
          // Check if all documents are ready
          const allReady = newDocuments.length > 0 && newDocuments.every((doc: DocumentStatus) => doc.is_ready);
          
          // Clear interval if all documents are ready
          if (allReady && pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
            console.log('All documents are ready, stopped polling');
          }
        }
      } catch (err) {
        if (isMounted) {
          setError('Failed to fetch documents for this thread');
          setDocuments([]); // Clear on error
          // Clear polling on error
          if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
          }
        }
      }
    };

    fetchDocuments();
    pollInterval = setInterval(fetchDocuments, 500);

    return () => {
      isMounted = false;
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [threadId, user?.id]);

  // Show error state
  if (error) {
    return (
      <>
        <Sidebar />
        <MainContent>
          <div className="w-full h-screen bg-chat-area flex items-center justify-center">
            <div className="text-red-400">{error}</div>
          </div>
        </MainContent>
      </>
    );
  }
  
  const combinedStatus = getCombinedStatus(documents);

  // Show failed state
  if (combinedStatus?.processing_status === 'failed') {
    return (
      <>
        <Sidebar />
        <MainContent>
          <div className="w-full h-screen bg-chat-area flex items-center justify-center">
            <div className="text-center">
              <div className="text-red-400 mb-2">Document processing failed</div>
              {combinedStatus.error_message && (
                <div className="text-white/60 text-sm">
                  {combinedStatus.error_message}
                </div>
              )}
            </div>
          </div>
        </MainContent>
      </>
    );
  }

  // Show chat interface if all documents are ready OR if no combinedStatus
  if (combinedStatus?.is_ready || !combinedStatus) {
    return (
      <>
        <Sidebar />
        <MainContent>
          <MainChatArea />
        </MainContent>
      </>
    );
  }

  // Show processing state
  return (
    <>
      <Sidebar />
      <MainContent>
        <DocumentProcessing 
          documentId={combinedStatus.id}
          status={combinedStatus}
          onComplete={() => {
          }}
        />
      </MainContent>
    </>
  );
}
