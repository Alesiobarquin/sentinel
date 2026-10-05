import type { Metadata } from "next";
import { Nav } from "@/components/nav";
import { Icon } from "@/components/icons";
import { REPO, UPSTREAM } from "@/lib/replay";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://alesiobarquin.github.io"),
  title: {
    default: "Sentinel — Student project",
    template: "%s · Sentinel",
  },
  description:
    "A student project: an AI-assisted tool for investigating service failures. Includes a recorded payment test, project overview, technical notes, and measured results.",
  alternates: { canonical: "/sentinel/" },
  openGraph: {
    title: "Sentinel — Student project",
    description:
      "A recorded payment-failure investigation, with tool calls, evidence, results, and project notes.",
    type: "website",
    url: "/sentinel/",
    siteName: "Sentinel",
    images: [
      {
        url: "/sentinel/social.png",
        width: 1200,
        height: 630,
        alt: "Sentinel student project: recorded investigation and measurements",
      },
    ],
  },
  robots: { index: true, follow: true },
  icons: { icon: "/sentinel/icon.svg" },
};

export default function Layout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        <Nav />
        {children}
        <footer className="site-footer">
          <div className="container footer-wrap">
            <div>
              <strong>Sentinel</strong>
              <span>
                Student project by{" "}
                <a href="https://github.com/Alesiobarquin">Alesiobarquin</a>.
              </span>
            </div>
            <div>
              <a href={REPO}>
                Code & documentation <Icon name="external" size={13} />
              </a>
              <span>
                External target: <a href={UPSTREAM}>OpenTelemetry Demo 3.1.0</a>
              </span>
              <a href="/sentinel/third-party-notices.txt">
                Third-party notices
              </a>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
