import Link from "next/link";

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative z-10 flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-deep/70 backdrop-blur-xl">
        <div className="mx-auto flex min-h-14 max-w-6xl items-center justify-between px-5 py-3 sm:px-8">
          <Link href="/" className="group flex items-center gap-2">
            <span className="font-syne text-lg font-bold tracking-tight text-white sm:text-xl">
              pulse<span className="text-gradient">.</span>
            </span>
            <span className="rounded-full border border-white/15 bg-white/5 px-2 py-0.5 font-dm text-[10px] font-semibold uppercase tracking-wider text-white/45">
              beta
            </span>
          </Link>
          <nav className="flex items-center gap-1">
            <Link
              href="/"
              className="rounded-full px-4 py-2 font-dm text-sm font-medium text-white/70 transition hover:bg-white/10 hover:text-white"
            >
              Latest
            </Link>
            <Link
              href="/history"
              className="rounded-full px-4 py-2 font-dm text-sm font-medium text-white/70 transition hover:bg-white/10 hover:text-white"
            >
              Archive
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-10 sm:px-8 md:py-12">
        {children}
      </main>
      <footer className="border-t border-white/[0.06] py-8 text-center font-dm text-xs text-white/35 md:py-10">
        Groww weekly pulse · built for sharp reads on messy reviews
      </footer>
    </div>
  );
}
