import Sidebar, { MainContent } from "./components/Sidebar";
import DocumentProcessing from "./components/DocumentProcessing";
import HomeChatArea from "./components/HomePage/HomeChatArea";

export default function Home() {
  return (
    <>
      <Sidebar />
      <MainContent>
        <HomeChatArea />
      </MainContent>
    </>
  );
}
