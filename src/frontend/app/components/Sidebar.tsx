"use client";

import { SignedIn, SignedOut, SignInButton, SignOutButton, UserButton } from '@clerk/nextjs'
import { useUser } from '@clerk/nextjs'
import { useState, useEffect, createContext, useContext } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Image from 'next/image'
import axios from 'axios'
import { Plus, Menu, Trash2 } from 'lucide-react'

interface Thread {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface SidebarContextType {
  isOpen: boolean;
  toggleSidebar: () => void;
  threads: Thread[];
  setThreads: (threads: Thread[]) => void;
  deleteThread: (threadId: string) => void;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (context === undefined) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return context;
};

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(true);
  const [threads, setThreads] = useState<Thread[]>([]);
  const { user } = useUser();

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };


  const deleteThread = async (threadId: string) => {
    if (!user?.id) return;
    
    try {
      await axios.delete(
        `${process.env.NEXT_PUBLIC_API_URL}/api/threads/${threadId}?user_id=${user.id}`
      );
      
      setThreads(threads.filter(thread => thread.id !== threadId));
      
      if (window.location.pathname.includes(threadId)) {
        window.location.href = '/';
      }
    } catch (error) {
      console.error('Failed to delete thread:', error);
    }
  };

  useEffect(() => {
    const fetchThreads = async () => {
      if (!user?.id) return;
      
      try {
        const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/threads/${user.id}`);
        const sortedThreads = response.data.sort((a: Thread, b: Thread) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setThreads(sortedThreads);
      } catch (error) {
        console.error('Failed to fetch threads:', error);
        setThreads([]);
      }
    };

    fetchThreads();
  }, [user?.id]);

  return (
    <SidebarContext.Provider value={{ 
      isOpen, 
      toggleSidebar, 
      threads, 
      setThreads, 
      deleteThread 
    }}>
      {children}
    </SidebarContext.Provider>
  );
}

export default function Sidebar() {
  const { user } = useUser();
  const router = useRouter();
  const pathname = usePathname();
  const { 
    isOpen, 
    toggleSidebar, 
    threads, 
    deleteThread 
  } = useSidebar();

  const handleNewChat = () => {
    router.push('/');
  };

  const handleThreadClick = (threadId: string) => {
    router.push(`/chat/${threadId}`);
  };

  const getCurrentThreadId = () => {
    const match = pathname.match(/^\/chat\/(.+)$/);
    return match ? match[1] : null;
  };

  const currentThreadId = getCurrentThreadId();
  
  return (
    <>
      <button
        onClick={toggleSidebar}
        className={`fixed top-4 left-4 z-50 w-10 h-10 bg-sidebar border border-white/10 flex items-center justify-center text-white hover:bg-white/10 transition-all duration-300 ${
          isOpen ? 'rounded-lg' : 'rounded-l-lg rounded-r-none border-r-0'
        }`}
        aria-label={isOpen ? "Close sidebar" : "Open sidebar"}
      >
        <Menu size={18} />
      </button>
      <button
        onClick={handleNewChat}
        className={`fixed top-4 z-50 w-10 h-10 bg-button border border-white/10 border-l-0 rounded-r-lg flex items-center justify-center text-white hover:bg-button/80 transition-all duration-300 ease-out ${
          isOpen 
            ? 'left-4 opacity-0 scale-0 pointer-events-none' 
            : 'left-14 opacity-100 scale-100 pointer-events-auto'
        }`}
        style={{ 
          transformOrigin: 'left center'
        }}
        aria-label="New Chat"
      >
        <Plus size={18} />
      </button>

      <div 
        className={`fixed left-0 top-0 h-screen bg-sidebar border-r border-white/10 z-40 transition-transform duration-300 ease-in-out flex flex-col ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ width: '20%' }}
      >
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 text-white font-bold">
          <Image src="/logo.jpg" alt="Logo" width={40} height={40} />
        </div>

        <div className="p-3 pt-16 flex-shrink-0">
          <button 
            onClick={handleNewChat}
            className="w-full p-1.5 my-5 text-white bg-button hover:bg-button/80 rounded-xl transition-colors gap-2 font-medium flex justify-center items-center"
          >
            <Plus size={18} />
            New Chat
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto px-4 min-h-0">
          <div className="text-white/60 text-xs uppercase font-semibold mb-3 px-2">
            Recent Chats
          </div>
          
          <div className="space-y-1">
            {threads.map((thread) => (
              <div
                key={thread.id}
                onClick={() => handleThreadClick(thread.id)}
                className={`w-full rounded-4xl transition-colors hover:bg-white/10 group cursor-pointer ${
                  currentThreadId === thread.id ? 'bg-white/10' : ''
                }`}
              >
                <div className="flex items-center gap-2 p-2.5">
                  <div className="flex-1 min-w-0">
                    <div
                      className={`text-sm font-medium truncate ${
                        currentThreadId === thread.id ? 'text-white' : 'text-white/80 group-hover:text-white'
                      }`}
                    >
                      {(thread.title || 'New Chat').replace(/^"|"$/g, '')}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity thread-actions">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteThread(thread.id);
                      }}
                      className="p-1 hover:bg-white/20 rounded text-red-400 hover:text-red-300"
                      aria-label="Delete"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-4 border-t border-white/10 flex-shrink-0">
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

      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/20 z-30 lg:hidden"
          onClick={() => toggleSidebar()}
        />
      )}
    </>
  );
}

export function MainContent({ children }: { children: React.ReactNode }) {
  const { isOpen } = useSidebar();
  
  return (
    <div 
      className={`transition-all duration-300 ease-in-out h-screen ${
        isOpen ? 'ml-[20%]' : 'ml-0'
      }`}
    >
      {children}
    </div>
  );
}