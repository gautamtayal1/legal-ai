"use client";

import { SignedIn, SignedOut, SignInButton, SignOutButton, UserButton } from '@clerk/nextjs'
import { useUser } from '@clerk/nextjs'
import { useState, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Image from 'next/image'
import axios from 'axios'
import { MessageSquare, Plus, FileText } from 'lucide-react'

interface Thread {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export default function Sidebar() {
  const { user } = useUser();
  const router = useRouter();
  const pathname = usePathname();
  const [threads, setThreads] = useState<Thread[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchThreads = async () => {
      if (!user?.id) return;
      
      try {
        const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/threads`);
        setThreads(response.data);
      } catch (error) {
        console.error('Failed to fetch threads:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchThreads();
  }, [user?.id]);

  const handleNewChat = () => {
    router.push('/');
  };

  const handleThreadClick = (threadId: string) => {
    router.push(`/chat/${threadId}`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 24 * 7) {
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const getCurrentThreadId = () => {
    const match = pathname.match(/^\/chat\/(.+)$/);
    return match ? match[1] : null;
  };

  const currentThreadId = getCurrentThreadId();
  
  return (
    <div className="w-1/5 h-screen bg-sidebar flex flex-col border-r border-white/10">
      {/* Logo */}
      <div className="p-4">
        <div className="text-white font-bold">
          <Image src="/logo.jpg" alt="Logo" width={50} height={50} />
        </div>
      </div>
      
      {/* New Chat Button */}
      <div className="p-4">
        <button 
          onClick={handleNewChat}
          className="w-full py-3 px-4 text-white rounded-lg hover:bg-white/10 transition-colors flex items-center gap-2 font-medium"
        >
          <Plus size={18} />
          New Chat
        </button>
      </div>
      
      {/* Threads List */}
      <div className="flex-1 overflow-y-auto px-4">
        <div className="text-white/60 text-xs uppercase font-semibold mb-3 px-2">
          Recent Chats
        </div>
        
        {loading ? (
          <div className="text-white/40 text-sm px-2">Loading chats...</div>
        ) : threads.length === 0 ? (
          <div className="text-white/40 text-sm px-2">No chats yet</div>
        ) : (
          <div className="space-y-1">
            {threads.map((thread) => (
              <button
                key={thread.id}
                onClick={() => handleThreadClick(thread.id)}
                className={`w-full text-left p-2 rounded-lg transition-colors hover:bg-white/10 group ${
                  currentThreadId === thread.id ? 'bg-white/10' : ''
                }`}
              >
                <div className="flex items-start gap-2">
                  <div className={`mt-1 ${currentThreadId === thread.id ? 'text-button' : 'text-white/40 group-hover:text-white/60'}`}>
                    <MessageSquare size={14} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-medium truncate ${
                      currentThreadId === thread.id ? 'text-white' : 'text-white/80 group-hover:text-white'
                    }`}>
                      {thread.title || 'New Chat'}
                    </div>
                    <div className="text-xs text-white/40 mt-0.5">
                      {formatDate(thread.updated_at)}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* User Section */}
      <div className="p-4 border-t border-white/10">
        <SignedOut>
          <button className="w-full py-2 px-4 rounded-lg text-white hover:bg-white/10">
            <SignInButton />
          </button>
        </SignedOut>
        <SignedIn>
          <div className="flex items-center gap-3">
            <UserButton />
            <div className="flex-1 min-w-0">
              <div className="text-white text-sm font-medium truncate">
                {user?.fullName || user?.emailAddresses?.[0]?.emailAddress}
              </div>
            </div>
            <SignOutButton>
              <button className="text-white/60 hover:text-white text-xs px-2 py-1 rounded hover:bg-white/10">
                Sign Out
              </button>
            </SignOutButton>
          </div>
        </SignedIn>
      </div>
    </div>
  );
}