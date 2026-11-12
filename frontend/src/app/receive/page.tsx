
"use client";

import Link from "next/link";
import { useState } from "react";

const API_BASE_URL = "http://localhost:8080/api";

type ReceivedFile = {
  id: string;
  original_filename: string;
  size_bytes: number;
  declared_content_type: string;
};

type LookupResponse = {
  transfer_id: string;
  expires_at: string;
  files: ReceivedFile[];
};

type DownloadResponse = {
  download_url: string;
  expires_in: number;
  downloads_remaining: number;
};

function formatSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function getErrorMessage(response: Response) {
  const message = await response.text();

  try {
    const data = JSON.parse(message);
    return data.detail || data.error || message;
  } catch {
    return message || `Request failed: ${response.status}`;
  }
}

export default function ReceivePage() {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [transfer, setTransfer] = useState<LookupResponse | null>(null);
  const [isLookingUp, setIsLookingUp] = useState(false);
  const [downloadingFileId, setDownloadingFileId] = useState<string | null>(
    null
  );

  const [downloadedFileIds, setDownloadedFileIds] = useState<string[]>([]);

  async function handleOpenFiles() {
    if (code.length !== 8) {
      setError("Please enter a valid 8-digit share code.");
      return;
    }

    setError("");
    setNotice("");
    setTransfer(null);
    setDownloadedFileIds([]);
    setIsLookingUp(true);

    try {
      const response = await fetch(`${API_BASE_URL}/transfers/lookup/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          share_code: code,
        }),
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response));
      }

      const data: LookupResponse = await response.json();

      setTransfer(data);

      if (data.files.length === 0) {
        setNotice("No files are available for this transfer.");
      } else {
        setNotice("Files retrieved successfully.");
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to retrieve files."
      );
    } finally {
      setIsLookingUp(false);
    }
  }

  async function handleDownload(file: ReceivedFile) {
    if (
      !transfer ||
      downloadingFileId ||
      downloadedFileIds.includes(file.id)
    ) {
      return;
    }

    setError("");
    setNotice("");
    setDownloadingFileId(file.id);

    try {
      // Step 1: Ask Django for a presigned S3 download URL.
      const response = await fetch(
        `${API_BASE_URL}/transfers/${transfer.transfer_id}/files/${file.id}/download/`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error(await getErrorMessage(response));
      }

      const data: DownloadResponse = await response.json();

       // Step 2: Download the actual file directly from S3.
      const fileResponse = await fetch(data.download_url);

      if (!fileResponse.ok) {
        throw new Error("Could not download the file from storage.");
      }

      const blob = await fileResponse.blob();
      const objectUrl = URL.createObjectURL(blob);

      // Step 3: Trigger browser download.
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = file.original_filename;

      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();

      setDownloadedFileIds((current) =>
        current.includes(file.id) ? current : [...current, file.id]
      );

      // Release the temporary browser URL after the download has started.
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);

      setNotice(`${file.original_filename} downloaded successfully.`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Download failed."
      );
    } finally {
      setDownloadingFileId(null);
    }
  }

  function handleSearchAgain() {
    setTransfer(null);
    setCode("");
    setError("");
    setNotice("");
    setDownloadedFileIds([]);
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
        <section className="mx-auto flex max-w-md flex-col items-center pt-16 text-center sm:pt-24">

          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#f0efff] text-3xl text-[#5144c8]">
            ↓
          </div>

          <h1 className="mt-7 text-3xl font-semibold tracking-tight sm:text-4xl">
            Receive files
          </h1>

          <p className="mt-3 text-sm leading-relaxed text-[#777670]">
            Enter the 8-digit share code you received to access your files.
          </p>

          {!transfer ? (
            /* Share code input */
            <div className="mt-9 w-full rounded-3xl border border-[#e9e8e4] bg-white p-6 sm:p-8">

              <label
                htmlFor="share-code"
                className="block text-left text-sm font-medium"
              >
                Enter share code
              </label>

              <input
                id="share-code"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={8}
                placeholder="00000000"
                value={code}
                disabled={isLookingUp}
                onChange={(event) => {
                  setCode(
                    event.target.value.replace(/\D/g, "").slice(0, 8)
                  );
                  setError("");
                  setNotice("");
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && code.length === 8) {
                    handleOpenFiles();
                  }
                }}
                className="mt-3 w-full rounded-2xl border border-[#e5e4df] bg-[#faf9f7] px-4 py-5 text-center text-2xl font-semibold tracking-[0.5em] outline-none transition placeholder:text-[#d2d0c9] focus:border-[#5144c8]"
              />

              {error && (
                <p className="mt-3 text-left text-xs text-red-600">
                  {error}
                </p>
              )}

              <button
                onClick={handleOpenFiles}
                disabled={code.length !== 8 || isLookingUp}
                className="mt-5 w-full rounded-full bg-[#171717] px-6 py-4 text-sm font-medium text-white transition hover:bg-[#333] disabled:cursor-not-allowed disabled:bg-[#e4e2dc] disabled:text-[#999890]"
              >
                {isLookingUp ? "Finding files..." : "Open files →"}
              </button>

              {notice && (
                <p className="mt-3 text-xs text-[#777670]">
                  {notice}
                </p>
              )}
            </div>
          ) : (
            /* Retrieved files */
            <div className="mt-9 w-full rounded-3xl border border-[#e9e8e4] bg-white p-6 text-left sm:p-8">

              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold">
                    Your files
                  </h2>

                  <p className="mt-1 text-xs text-[#777670]">
                    {transfer.files.length}{" "}
                    {transfer.files.length === 1 ? "file" : "files"} available
                  </p>
                </div>

                <span className="rounded-full bg-[#edf8ef] px-3 py-1 text-xs font-medium text-green-700">
                  Available
                </span>
              </div>

              <div className="mt-5 rounded-xl bg-[#f7f6f2] p-3">
                <p className="text-xs text-[#777670]">
                  Transfer expires
                </p>

                <p className="mt-1 text-sm font-medium">
                  {new Date(transfer.expires_at).toLocaleString()}
                </p>
              </div>

              {transfer.files.length === 0 ? (
                <p className="mt-6 text-center text-sm text-[#777670]">
                  No downloadable files are available.
                </p>
              ) : (
                <div className="mt-5 space-y-3">
                  {transfer.files.map((file) => (
                    <div
                      key={file.id}
                      className="rounded-xl border border-[#eeede9] p-4"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f4f3ef]">
                          📄
                        </div>

                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium">
                            {file.original_filename}
                          </p>

                          <p className="mt-1 text-xs text-[#999890]">
                            {formatSize(file.size_bytes)}
                          </p>
                        </div>
                      </div>

                      {downloadedFileIds.includes(file.id) ? (
                        <div className="mt-4 flex w-full items-center justify-center gap-2 rounded-full bg-[#edf8ef] px-5 py-3 text-sm font-medium text-green-700">
                          <span aria-hidden="true">✓</span>
                          Downloaded
                        </div>
                      ) : (
                        <button
                          onClick={() => handleDownload(file)}
                          disabled={downloadingFileId !== null}
                          className="mt-4 w-full rounded-full bg-[#171717] px-5 py-3 text-sm font-medium text-white transition hover:bg-[#333] disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {downloadingFileId === file.id
                            ? "Downloading..."
                            : "Download file ↓"}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {notice && (
                <p className="mt-4 text-center text-xs text-[#5144c8]">
                  {notice}
                </p>
              )}

              {error && (
                <p className="mt-4 text-center text-xs text-red-600">
                  {error}
                </p>
              )}

              <button
                onClick={handleSearchAgain}
                className="mt-6 w-full rounded-full border border-[#e5e4df] bg-white px-6 py-3 text-sm font-medium transition hover:bg-[#f7f6f2]"
              >
                Enter another code
              </button>
            </div>
          )}

          {/* QR hint */}
          {!transfer && (
            <div className="mt-7 flex items-center gap-3 rounded-2xl border border-[#e9e8e4] bg-white px-5 py-4 text-left">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#f4f3ef]">
                <span className="text-xl">▦</span>
              </div>

              <div>
                <p className="text-sm font-medium">
                  Have a QR code?
                </p>

                <p className="mt-1 text-xs text-[#777670]">
                  Scan it to access shared files.
                </p>
              </div>
            </div>
          )}

          <p className="mt-8 text-xs text-[#999890]">
            No account needed. Your files are temporary.
          </p>

        </section>
      </div>
    </main>
  );
}
