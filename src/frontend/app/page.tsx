import Sidebar from "./components/Sidebar";
import DocumentProcessing from "./components/DocumentProcessing";
import HomeChatArea from "./components/HomePage/HomeChatArea";

export default function Home() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <HomeChatArea />
      
    </div>
  );
}
