import "./globals.css";
import { ClerkProvider } from '@clerk/nextjs'
import { SidebarProvider } from "./components/Sidebar";
import { ReactNode } from "react";
import { IBM_Plex_Sans } from "next/font/google";

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-ibm-plex-sans",
});

export const metadata = {
  title: "Legal AI",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={ibmPlexSans.variable}>
        <ClerkProvider>
          <SidebarProvider>
            {children}
          </SidebarProvider>
        </ClerkProvider>
      </body>
    </html>
  );
}
