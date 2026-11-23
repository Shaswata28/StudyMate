import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  icons: { icon: { url: "/studymate-icon.webp", type: "image/webp" } },
  title: "StudyMate - AI-Powered Academic Assistant",
  description: "Personalized AI study tutor with course material retrieval and LaTeX support.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `try{const t=localStorage.getItem("studymate-theme");document.documentElement.classList.toggle("dark",t==="dark"||((!t||t==="system")&&matchMedia("(prefers-color-scheme: dark)").matches));}catch{}` }} />
      </head>
      <body className="antialiased min-h-screen bg-background dark:bg-slate-950">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

