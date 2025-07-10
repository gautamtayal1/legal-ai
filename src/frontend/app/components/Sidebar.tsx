"use client";

import { SignedIn, SignedOut, SignInButton, SignOutButton, UserButton } from '@clerk/nextjs'
import { useUser } from '@clerk/nextjs'

export default function Sidebar() {
  const { user } = useUser();
  
  return (
    <div className="w-1/5 h-screen bg-sidebar flex flex-col border-r border-white/10">
      <div className="p-4">
        <div className="text-white font-bold">Legal AI</div>
      </div>
      
      <div className="p-4">
        <button className="w-full py-2 px-4 text-white rounded-lg hover:bg-white/10 hover:rounded-4xl">
          + New Chat
        </button>
      </div>
      
      <div className="flex-1 p-4 overflow-y-auto" style={{height: '70%'}}>
      </div>

      <div className="p-4 flex">
        <SignedOut>
          <button className="w-full py-2 px-4 rounded-lg">
            <SignInButton />
          </button>
        </SignedOut>
        <SignedIn>
          <button className="w-full py-2 px-4 rounded-lg flex items-center gap-5">
            <UserButton />
            <div className="text-white">  
              {user?.fullName}
            </div>
          </button>
          <SignOutButton />
        </SignedIn>
      </div>
    </div>
  );
}