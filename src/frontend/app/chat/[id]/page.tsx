import Sidebar from "@/components/Sidebar";
import HomeChatArea from "@/app/components/HomePage/HomeChatArea";

export default function Home() {
  return (
    <div className="flex h-screen ">
      <Sidebar />
      <HomeChatArea />
    </div>
  );
}
