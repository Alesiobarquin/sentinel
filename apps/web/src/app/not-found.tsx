import Link from "next/link";
export default function NotFound() {
  return (
    <main id="main" className="container missing">
      <p className="eyebrow">404 / route not found</p>
      <h1>This signal leads nowhere.</h1>
      <p>
        Return to the recorded investigation or read how Sentinel was built.
      </p>
      <Link href="/demo/" className="button primary">
        Explore the demo
      </Link>
      <Link href="/" className="button secondary">
        Home
      </Link>
    </main>
  );
}
