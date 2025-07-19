"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, Brain, Search, Sparkles, Zap, Shield, ArrowRight } from "lucide-react";
import DocumentUploadModal from "../DocumentUploadModal";
import { useUser } from "@clerk/nextjs";
import { useSidebar } from "../Sidebar";
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
  const { threads, setThreads } = useSidebar();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [currentFeature, setCurrentFeature] = useState(0);

  useEffect(() => {
    setIsVisible(true);
    const interval = setInterval(() => {
      setCurrentFeature(prev => (prev + 1) % 3);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

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
        // Add the new thread to sidebar immediately
        const newThread = {
          id: newChatId,
          title: 'New Chat',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        const updatedThreads = [newThread, ...threads].sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setThreads(updatedThreads);
        
        router.push(`/chat/${newChatId}?uploading=true`);
      } else {
        throw new Error('Failed to create thread');
      }
      
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file.file);
        formData.append('user_id', user?.id || '');
        formData.append('thread_id', newChatId);
        
        const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/documents/upload`, formData);
        
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
      description: "Automatically fetches related clauses for complete context",
      color: "from-blue-500 to-cyan-500"
    },
    {
      icon: FileText,
      title: "Definition Resolution",
      description: "Automatically finds and applies defined terms from your documents",
      color: "from-purple-500 to-pink-500"
    },
    {
      icon: Brain,
      title: "Obligation Analysis",
      description: "Identifies who must do what, when, and under which conditions",
      color: "from-orange-500 to-red-500"
    }
  ];

  return (
    <>
      <div className="w-full h-screen bg-chat-area relative">
        {/* Subtle background accent */}
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-button/5 rounded-full blur-3xl"></div>
        <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl"></div>
        
        <div className="flex flex-col items-center justify-center h-full px-6 lg:px-12 max-w-6xl mx-auto relative z-10">
          
          {/* Hero Section */}
          <div className={`text-center mb-16 transition-all duration-1000 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}`}>
            
            {/* Animated title with gradient and glow */}
            <div className="relative mb-6">
              <h1 className="text-transparent bg-clip-text bg-gradient-to-r from-white via-button to-purple-300 text-4xl lg:text-6xl font-bold leading-tight animate-pulse">
                Inquire
              </h1>
              <div className="absolute inset-0 text-white text-4xl lg:text-6xl font-bold leading-tight blur-sm opacity-30 animate-pulse">
                Inquire
              </div>
            </div>
            
            {/* Animated subtitle with typewriter effect */}
            <div className="relative mb-8">
              <p className="text-white/80 text-lg lg:text-xl max-w-2xl mx-auto">
                Your legal AI assistant
              </p>
              <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-24 h-0.5 bg-gradient-to-r from-transparent via-button to-transparent animate-pulse"></div>
            </div>
          
            {/* Enhanced button with more animations */}
            <div className="relative group">
              <button
                onClick={handleUploadClick}
                className="relative bg-gradient-to-r from-button to-purple-600 hover:from-button/90 hover:to-purple-500 text-white px-8 py-4 rounded-xl font-medium transition-all duration-300 shadow-lg hover:shadow-2xl hover:shadow-button/25 hover:scale-105 overflow-hidden"
              >
                <span className="relative z-10 flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  Upload Documents
                  <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-1" />
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
              </button>
              
            </div>
            
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-4xl">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div key={index} className="group bg-input-area/50 backdrop-blur-sm rounded-xl p-6 text-center border border-white/5 hover:border-white/10 transition-all duration-300 hover:scale-105">
                  <div className="relative">
                    <div className={`w-12 h-12 bg-gradient-to-br ${feature.color} rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                    <div className="absolute -top-1 -right-1 w-2 h-2 bg-button/60 rounded-full animate-ping opacity-0 group-hover:opacity-100"></div>
                  </div>
                  <h3 className="text-white text-lg font-semibold mb-2 group-hover:text-button transition-colors duration-300">
                    {feature.title}
                  </h3>
                  <p className="text-white/70 text-sm group-hover:text-white/90 transition-colors duration-300">
                    {feature.description}
                  </p>
                </div>
              );
            })}
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