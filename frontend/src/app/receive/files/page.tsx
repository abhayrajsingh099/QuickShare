
"use client";

import Link from "next/link";
import { useState } from "react";

const sampleFiles = [
  { name: "Brand-guidelines.pdf", size: "12.4 MB", type: "pdf" },
  { name: "Product-shoot-04.png", size: "8.1 MB", type: "image" },
  { name: "Q3-report.xlsx", size: "2.3 MB", type: "file" },
  { name: "Walkthrough.mp4", size: "148 MB", type: "video" },
];

export default function ReceivedFilesPage() {
  const [downloaded, setDownloaded] = useState<number[]>([0]);

  function handleDownload(index: number) {
    setDownloaded((current) =>
      current.includes(index) ? current : [...current, index]
    );
  }

  return (
    <main className="min-h-screen bg-[#f7f6f2] px-5 py-6 text-[#171717] sm:px-10">
      <div className="mx-auto max-w-6xl">

        {/* Header */}
        <header className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-black text-white">
              ↑
            </span>
            <span className="text-lg font-semibold tracking-tight">
              QuickShare
            </span>
          </Link>

          <nav className="flex items-center gap-1 rounded-full bg-[#eeede9] p-1">
            <Link
              href="/send"
              className="rounded-full px-5 py-2 text-sm hover:bg-white"
            >
              Send
            </Link>

            <Link
              href="/receive"
              className="rounded-full bg-white px-5 py-2 text-sm shadow-sm"
            >
              Receive
            </Link>
          </nav>

          <div className="w-20" />
        </header>

        {/* Main content */}
        <section className="mx-auto max-w-3xl pt-12 sm:pt-14">

          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            {sampleFiles.length} files for you
          </h1>

          <p className="mt-2 text-base text-[#777670]">
            Download what you need, one at a time.
          </p>

          {/* File list */}
          <div className="mt-7 overflow-hidden rounded-3xl border border-[#e9e8e4] bg-white">

            {sampleFiles.map((file, index) => (
              <div
                key={file.name}
                className={`flex items-center gap-3 px-4 py-5 sm:px-6 ${
                  index !== sampleFiles.length - 1
                    ? "border-b border-[#eeede9]"
                    : ""
                }`}
              >
                {/* File icon */}
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[#f4f3ef] text-[#55544f]">
                  {file.type === "image" ? (
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      className="h-6 w-6"
                    >
                      <rect x="3" y="4" width="18" height="16" rx="2" />
                      <circle cx="8.5" cy="9" r="1.5" />
                      <path d="m21 15-5-5L5 20" />
                    </svg>
                  ) : file.type === "video" ? (
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      className="h-6 w-6"
                    >
                      <rect x="3" y="5" width="18" height="14" rx="3" />
                      <path d="m10 9 5 3-5 3z" />
                    </svg>
                  ) : (
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      className="h-6 w-6"
                    >
                      <path d="M6 3h8l5 5v13H6z" />
                      <path d="M14 3v5h5" />
                    </svg>
                  )}
                </div>

                {/* File details */}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium sm:text-base">
                    {file.name}
                  </p>
                  <p className="mt-1 text-sm text-[#777670]">
                    {file.size}
                  </p>
                </div>

                {/* Download status */}
                {downloaded.includes(index) ? (
                  <div className="flex shrink-0 items-center gap-2 rounded-full bg-[#e4f4eb] px-3 py-2 text-xs font-medium text-[#258453] sm:px-5 sm:py-3 sm:text-sm">
                    <span>✓</span>
                    <span>Downloaded</span>
                  </div>
                ) : (
                  <button
                    onClick={() => handleDownload(index)}
                    className="flex shrink-0 items-center gap-2 rounded-full bg-[#171717] px-4 py-3 text-xs font-medium text-white transition hover:bg-[#333] sm:px-6 sm:text-sm"
                  >
                    <span>↓</span>
                    <span>Download</span>
                  </button>
                )}
              </div>
            ))}

          </div>

          {/* Send files back */}
          <div className="mt-8 flex flex-col gap-4 rounded-3xl bg-[#efefff] p-6 sm:flex-row sm:items-center sm:justify-between sm:px-7">
            <div>
              <h2 className="text-base font-semibold text-[#4439ad]">
                Need to send something back?
              </h2>

              <p className="mt-1 text-sm text-[#66647a]">
                Share your own files in a few seconds.
              </p>
            </div>

            <Link
              href="/send"
              className="flex shrink-0 items-center justify-center gap-3 rounded-full border border-[#dedcff] bg-white px-6 py-3 text-sm font-medium text-[#4439ad] transition hover:bg-[#f8f7ff]"
            >
              Send files
              <span>→</span>
            </Link>
          </div>

        </section>
      </div>
    </main>
  );
}
