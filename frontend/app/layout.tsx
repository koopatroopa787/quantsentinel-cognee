import type { Metadata } from "next";
import React from "react";

export const metadata: Metadata = {
  title: "QuantSentinel — Research Terminal",
  description: "Self-improving multi-agent quantitative research platform",
};

const globalStyles = `
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  font-family: 'Inter', system-ui, sans-serif;
  background-color: #050505;
  background-image:
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 36px 36px, 36px 36px;
  color: #f5f5f5;
  overflow: hidden;
  color-scheme: dark;
}

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.25); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.45); }

textarea, button, input { font-family: inherit; }
textarea { color-scheme: dark; }
textarea::placeholder { color: rgba(255,255,255,0.35); }

@keyframes q2Pulse   { 0%,100%{opacity:1} 50%{opacity:0.2} }
@keyframes q2Shimmer { 0%{transform:translateX(-220%)} 100%{transform:translateX(440%)} }
@keyframes q2Bounce  { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-5px)} }
@keyframes q2FadeIn  { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com"/>
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin=""/>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet"/>
        <style dangerouslySetInnerHTML={{ __html: globalStyles }} />
      </head>
      <body style={{ color: '#f5f5f5', height: '100dvh', overflow: 'hidden' }}>
        {children}
      </body>
    </html>
  );
}
