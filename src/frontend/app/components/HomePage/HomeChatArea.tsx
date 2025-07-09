import InputBox from "../InputBox";

export default function HomeChatArea() {
  return (
    <div className="w-4/5 h-screen bg-chat-area relative">
      <div className="flex flex-col items-center justify-center h-full -mt-8">
        <div className="text-center mb-8">
          <h2 className="text-white text-3xl">How can I help you crack legal codes?</h2>
        </div>
        <InputBox />
      </div>
    </div>
  );
} 