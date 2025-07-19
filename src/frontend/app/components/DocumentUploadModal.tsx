"use client";

import React, { useState, useRef, useCallback } from 'react';
import { X, Upload, FileText, Trash2, ArrowRight } from 'lucide-react';

interface UploadedFile {
  id: string;
  file: File;
  name: string;
  size: string;
  type: string;
}

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (files: UploadedFile[]) => void;
}

const DocumentUploadModal = ({ isOpen, onClose, onSubmit }: DocumentUploadModalProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileType = (file: File): string => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf': return 'PDF';
      case 'doc': case 'docx': return 'Word';
      case 'txt': return 'Text';
      default: return 'Document';
    }
  };

  const addFiles = (files: FileList) => {
    const newFiles: UploadedFile[] = [];
    
    Array.from(files).forEach((file) => {
      const allowedTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'];
      if (!allowedTypes.includes(file.type)) {
        alert(`File type ${file.type} not supported`);
        return;
      }
      
      if (file.size > 10 * 1024 * 1024) {
        alert(`File ${file.name} exceeds 10MB limit`);
        return;
      }

      const uploadedFile: UploadedFile = {
        id: crypto.randomUUID(),
        file,
        name: file.name,
        size: formatFileSize(file.size),
        type: getFileType(file)
      };
      
      newFiles.push(uploadedFile);
    });

    setUploadedFiles(prev => [...prev, ...newFiles]);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      addFiles(files);
    }
    event.target.value = '';
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files) {
      addFiles(files);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const removeFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== id));
  };

  const handleSubmit = async () => {
    if (uploadedFiles.length === 0) {
      alert('Please upload at least one document');
      return;
        
    }
    setIsSubmitting(true);
    try {
      await onSubmit(uploadedFiles);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-chat-area rounded-2xl border border-white/10 w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="p-6 border-b border-white/10 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-white text-xl font-semibold">Upload Your Documents</h2>
              <p className="text-white/60 text-sm mt-1">
                Upload all documents you want to analyze in this conversation
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white/70 hover:text-white p-1"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`
              border-2 border-dashed rounded-xl p-8 text-center transition-colors
              ${isDragOver 
                ? 'border-button bg-button/10' 
                : 'border-white/20 hover:border-white/30'
              }
            `}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              multiple
              accept=".pdf,.txt,.docx,.doc"
              className="hidden"
            />
            
            <Upload className="w-12 h-12 text-white/40 mx-auto mb-4" />
            <p className="text-white text-lg mb-2">
              Drop your documents here
            </p>
            <p className="text-white/60 text-sm mb-4">
              or click to browse files
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="bg-input-area hover:bg-white/10 text-white px-4 py-2 rounded-lg border border-white/10 transition-colors"
            >
              Choose Files
            </button>
            <p className="text-white/40 text-xs mt-3">
              Supports PDF, Word, and Text files (max 10MB each)
            </p>
          </div>

          {uploadedFiles.length > 0 && (
            <div className="mt-6">
              <h3 className="text-white font-medium mb-3">
                Uploaded Documents ({uploadedFiles.length})
              </h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {uploadedFiles.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-3 bg-input-area rounded-lg border border-white/5"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-button/20 rounded-lg flex items-center justify-center">
                        <FileText className="w-5 h-5 text-button" />
                      </div>
                      <div>
                        <p className="text-white text-sm font-medium">{file.name}</p>
                        <p className="text-white/60 text-xs">{file.type} • {file.size}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(file.id)}
                      className="text-white/40 hover:text-red-400 p-1 transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-white/10 bg-chat-area/50 flex-shrink-0">
          <div className="flex items-center justify-between">
            <p className="text-white/60 text-sm">
              Once you start the conversation, you cannot add more documents
            </p>
            <div className="flex space-x-3">
              <button
                onClick={handleSubmit}
                disabled={uploadedFiles.length === 0 || isSubmitting}
                className="bg-button hover:bg-button/80 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg transition-colors flex items-center space-x-2"
              >
                {isSubmitting ? (
                  <span>Processing...</span>
                ) : (
                  <>
                    <span>Start Analysis</span>
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentUploadModal; 