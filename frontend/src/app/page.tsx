
import Link from "next/link";

function Header() {
  return (
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
          className="rounded-full px-5 py-2 text-sm transition hover:bg-white"
        >
          Send
        </Link>
        <Link
          href="/receive"
          className="rounded-full px-5 py-2 text-sm transition hover:bg-white"
        >
          Receive
        </Link>
      </nav>

      <div className="w-28" />
    </header>
  );
}

function ActionCard({
  title,
  description,
  href,
  icon,
  dark = false,
}: {
  title: string;
  description: string;
  href: string;
  icon: string;
  dark?: boolean;
}) {
  return (
    <Link
      href={href}
      className={`group flex min-h-52 flex-col justify-between rounded-3xl border p-6 transition hover:-translate-y-1 hover:shadow-lg ${
        dark
          ? "border-black bg-[#141414] text-white"
          : "border-[#e9e8e4] bg-white text-[#171717]"
      }`}
    >
      <div className="flex items-center justify-between">
        <span
          className={`flex h-12 w-12 items-center justify-center rounded-full text-xl ${
            dark ? "bg-white/10" : "bg-[#f0efff] text-[#5144c8]"
          }`}
        >
          {icon}
        </span>

        <span className="text-xl transition-transform group-hover:translate-x-1">
          →
        </span>
      </div>

      <div>
        <h2 className="text-2xl font-semibold tracking-tight">
          {title}
        </h2>
        <p
          className={`mt-1 max-w-64 text-sm leading-relaxed ${
            dark ? "text-white/65" : "text-[#777670]"
          }`}
        >
          {description}
        </p>
      </div>
    </Link>
  );
}

export default function Home() {
  return (
    <main className="min-h-screen bg-[#f7f6f2] px-5 py-6 text-[#171717] sm:px-10">
      <div className="mx-auto max-w-6xl">
        <Header />

        <section className="mx-auto flex max-w-2xl flex-col items-center pt-24 text-center sm:pt-32">
          <span className="rounded-full border border-[#e9e8e4] bg-white px-4 py-2 text-xs text-[#55544f]">
            <span className="mr-2 inline-block h-2 w-2 rounded-full bg-[#5144c8]" />
            No account needed
          </span>

          <h1 className="mt-7 text-4xl font-semibold tracking-tight sm:text-6xl">
            Share files, simply.
          </h1>

          <p className="mt-5 max-w-md text-base leading-relaxed text-[#777670] sm:text-lg">
            Pick files, get a code. The other person enters it
            or scans the QR, and downloads.
          </p>

          <div className="mt-12 grid w-full max-w-xl grid-cols-1 gap-4 sm:grid-cols-2">
            <ActionCard
              title="Send"
              description="Choose files and get a code and QR to share."
              href="/send"
              icon="↑"
              dark
            />

            <ActionCard
              title="Receive"
              description="Enter an 8-digit code or scan a QR."
              href="/receive"
              icon="↓"
            />
          </div>
        </section>
      </div>
    </main>
  );
}
