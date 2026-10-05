import Link from "next/link";
export default function NotFound() {
  return (
    <main id="main" className="container missing">
      <p className="eyebrow">404 / route not found</p>
      <h1>Page not found</h1>
      <p>This URL does not exist. Use the links below to return to the site.</p>
      <Link href="/demo/" className="button primary">
        View demo
      </Link>
      <Link href="/" className="button secondary">
        Home
      </Link>
    </main>
  );
}
