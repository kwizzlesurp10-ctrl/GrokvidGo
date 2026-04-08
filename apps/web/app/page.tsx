import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold">ViralAether Swarm</h1>
      <p className="text-gray-500">Automated viral video generation pipeline</p>
      <div className="flex gap-4">
        <Link
          href="/dashboard"
          className="rounded-lg bg-blue-600 px-6 py-3 text-white hover:bg-blue-700"
        >
          Open Dashboard
        </Link>
        <button
          onClick={async () => {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/jobs`, { method: "POST" });
          }}
          className="rounded-lg border px-6 py-3 hover:bg-gray-50"
        >
          Trigger Job
        </button>
      </div>
    </main>
  );
}
