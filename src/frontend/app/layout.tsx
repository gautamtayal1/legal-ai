import { ClerkProvider } from "@clerk/nextjs";
import { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "Legal AI",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ClerkProvider>{children}</ClerkProvider>
      </body>
    </html>
  );
}
