import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-[55vh] flex-col items-center justify-center px-6 text-center">
      <p className="font-syne text-[clamp(5rem,18vw,10rem)] font-black leading-none text-white/[0.07]">
        404
      </p>
      <h1 className="mt-6 font-syne text-4xl font-extrabold tracking-tight text-white md:text-5xl">
        That page isn&apos;t here
      </h1>
      <p className="mt-6 max-w-lg font-dm text-lg leading-relaxed text-white/50 md:text-xl">
        Check the URL — use <strong className="text-white/80">/</strong> for the
        dashboard or open Archive. If you deployed to Vercel, set the project{" "}
        <strong className="text-[#00ffc8]/90">Root Directory</strong> to{" "}
        <code className="rounded-lg bg-white/10 px-2 py-1 text-base text-[#ff6bc7]">
          phase6_ui
        </code>
        .
      </p>
      <div className="mt-12 flex flex-wrap justify-center gap-5">
        <Link
          href="/"
          className="rounded-full bg-gradient-to-r from-[#d4ff4d] via-[#00ffc8] to-[#00c4ff] px-10 py-4 font-syne text-lg font-bold text-black shadow-lg shadow-[#00ffc8]/20"
        >
          Go home
        </Link>
        <Link
          href="/history"
          className="rounded-full border-2 border-white/20 px-10 py-4 font-dm text-lg font-semibold text-white/85 hover:border-[#00ffc8]/40 hover:text-[#00ffc8]"
        >
          Archive
        </Link>
      </div>
    </div>
  );
}
