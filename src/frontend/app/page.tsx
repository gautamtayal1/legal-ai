import Sidebar, { MainContent } from "./components/Sidebar";
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
