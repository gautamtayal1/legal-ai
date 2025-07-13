"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, Brain, Search } from "lucide-react";
import DocumentUploadModal from "../DocumentUploadModal";
import { useUser } from "@clerk/nextjs";
import axios from "axios";

interface UploadedFile {
  id: string;
  file: File;
  name: string;
  size: string;
  type: string;
}

export default function HomeChatArea() {
  const { user } = useUser();
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleUploadClick = () => {
    setIsModalOpen(true);
  };

  const handleModalSubmit = async (files: UploadedFile[]) => {
    try {
      console.log('Uploading files:', files);
      
      const uploadedDocs = [];
      const newChatId = crypto.randomUUID();

      const thread = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/threads`, {
        id: newChatId,
        user_id: user?.id || '',
        title: 'New Chat',
      });

      if (thread.status === 200) {
        router.push(`/chat/${newChatId}`);
      } else {
        throw new Error('Failed to create thread');
      }
      
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file.file);
        formData.append('user_id', user?.id || '');
        formData.append('thread_id', newChatId);
        
        const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/documents/upload/`, formData);
        
        if (response.status !== 200) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }

        const result = response.data;
        uploadedDocs.push(result);
      }
      
      // Close modal
      setIsModalOpen(false);
      
      
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
  };

  const features = [
    {
      icon: Search,
      title: "Multi-Round Retrieval",
      description: "Automatically fetches related clauses for complete context"
    },
    {
      icon: FileText,
      title: "Definition Resolution",
      description: "Automatically finds and applies defined terms from your documents"
    },
    {
      icon: Brain,
      title: "Obligation Analysis",
      description: "Identifies who must do what, when, and under which conditions"
    }
  ];

  return (
    <>
      <div className="w-4/5 h-screen bg-chat-area relative overflow-y-auto">
        <div className="flex flex-col items-center justify-center min-h-full px-8">
          
          {/* Hero Section */}
          <div className="text-center mb-12 w-full max-w-3xl">
            <div className="mb-8">
              <div className="w-16 h-16 bg-button/20 rounded-xl flex items-center justify-center mx-auto mb-6">
                <FileText className="w-8 h-8 text-button" />
              </div>
              
              <h1 className="text-white text-3xl lg:text-4xl font-light mb-4 leading-tight">
                How can I help you crack legal codes?
              </h1>
              
              <p className="text-white/60 text-base max-w-xl mx-auto leading-relaxed mb-8">
                Upload your legal documents and get instant AI-powered insights
              </p>
            
              <button
                onClick={handleUploadClick}
                className="bg-button hover:bg-button/80 text-white px-8 py-3 rounded-xl transition-all duration-200 flex items-center space-x-2 font-medium mx-auto shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                <Upload size={20} />
                <span>Upload Documents</span>
              </button>
            </div>
          </div>

          {/* Features Grid */}
          <div className="w-full max-w-4xl">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {features.map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <div key={index} className="bg-input-area/40 rounded-xl p-6 border border-white/10 hover:border-white/20 transition-all duration-300 text-center hover:transform hover:scale-105">
                    <div className="w-12 h-12 bg-button/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                      <Icon className="w-6 h-6 text-button" />
                    </div>
                    <h3 className="text-white text-base font-semibold mb-2">{feature.title}</h3>
                    <p className="text-white/60 text-sm leading-relaxed">{feature.description}</p>
                  </div>
                );
              })}
            </div>
          </div>

        </div>
      </div>
      
      <DocumentUploadModal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        onSubmit={handleModalSubmit}
      />
    </>
  );
} 