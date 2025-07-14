"use client";

import { SignedIn, SignedOut, SignInButton, SignOutButton, UserButton } from '@clerk/nextjs'
import { useUser } from '@clerk/nextjs'
import { useState, useEffect, createContext, useContext } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Image from 'next/image'
import axios from 'axios'
import { MessageSquare, Plus, Menu, X } from 'lucide-react'

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

  // Fetch threads once and cache them
  useEffect(() => {
    const fetchThreads = async () => {
      if (!user?.id) return;
      
      try {
        const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/threads`);
        setThreads(response.data);
      } catch (error) {
        console.error('Failed to fetch threads:', error);
      }
    };

    fetchThreads();
  }, [user?.id]);

  return (
    <SidebarContext.Provider value={{ isOpen, toggleSidebar, threads, setThreads }}>
      {children}
    </SidebarContext.Provider>
  );
}

export default function Sidebar() {
  const { user } = useUser();
  const router = useRouter();
  const pathname = usePathname();
  const { isOpen, toggleSidebar, threads } = useSidebar();

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
    <>
      {/* Toggle Button - Always visible */}
      <button
        onClick={toggleSidebar}
        className={`fixed top-4 left-4 z-50 w-10 h-10 bg-sidebar border border-white/10 flex items-center justify-center text-white hover:bg-white/10 transition-all duration-300 ${
          isOpen ? 'rounded-lg' : 'rounded-l-lg rounded-r-none border-r-0'
        }`}
        aria-label={isOpen ? "Close sidebar" : "Open sidebar"}
      >
        <Menu size={18} />
      </button>
      {/* New Chat Button - Emerges from sidebar button */}
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

      {/* Sidebar */}
      <div 
        className={`fixed left-0 top-0 h-screen bg-sidebar border-r border-white/10 z-40 transition-transform duration-300 ease-in-out flex flex-col ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ width: '20%' }}
      >
        {/* Logo - positioned to align with toggle button */}
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 text-white font-bold">
          <Image src="/logo.jpg" alt="Logo" width={40} height={40} />
        </div>

        {/* New Chat Button */}
        <div className="p-3 pt-16 flex-shrink-0">
          <button 
            onClick={handleNewChat}
            className="w-full p-1.5 my-5 text-white bg-button hover:bg-button/80 rounded-xl transition-colors gap-2 font-medium flex justify-center items-center"
          >
            <Plus size={18} />
            New Chat
          </button>
        </div>
        
        {/* Threads List - Scrollable and takes remaining space */}
        <div className="flex-1 overflow-y-auto px-4 min-h-0">
          <div className="text-white/60 text-xs uppercase font-semibold mb-3 px-2">
            Recent Chats
          </div>
          
          <div className="space-y-1">
            {threads.map((thread) => (
              <button
                key={thread.id}
                onClick={() => handleThreadClick(thread.id)}
                className={`w-full text-left p-2.5 rounded-4xl transition-colors hover:bg-white/10 group ${
                  currentThreadId === thread.id ? 'bg-white/10' : ''
                }`}
              >
                <div className="flex items-start gap-2">
                  <div className={`mt-1 ${currentThreadId === thread.id ? 'text-button' : 'text-white/40 group-hover:text-white/60'}`}>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-medium truncate ${
                      currentThreadId === thread.id ? 'text-white' : 'text-white/80 group-hover:text-white'
                    }`}>
                      {thread.title || 'New Chat'}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* User Section - Always at bottom */}
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

      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/20 z-30 lg:hidden"
          onClick={() => toggleSidebar()}
        />
      )}
    </>
  );
}

// Layout wrapper component
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