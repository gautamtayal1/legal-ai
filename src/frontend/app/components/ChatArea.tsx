import InputBox from "./InputBox";

export default function ChatArea() {
  return (
    <div className="w-4/5 h-screen bg-chat-area relative">
      {/* Chat area content will go here */}
      
      {/* Floating input box at bottom */}
      <InputBox />
    </div>
  );
} 