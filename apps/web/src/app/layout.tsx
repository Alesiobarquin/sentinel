import type { Metadata } from "next";
import { Nav } from "@/components/nav";
import { Icon } from "@/components/icons";
import { REPO, UPSTREAM } from "@/lib/replay";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://alesiobarquin.github.io"),
  title: {
    default: "Sentinel — Evidence-driven incident investigation",
    template: "%s · Sentinel",
  },
  description:
    "Explore a real AI incident investigation: read-only telemetry tools, competing hypotheses, cited evidence, and a measured recovery. An engineering project with an open source audit trail.",
  alternates: { canonical: "/sentinel/" },
  openGraph: {
    title: "Sentinel — An incident, investigated",
    description:
      "One real payment failure. Follow the evidence from first signal to a defensible diagnosis.",
    type: "website",
    url: "/sentinel/",
    siteName: "Sentinel",
    images: [
      {
        url: "/sentinel/social.png",
        width: 1200,
        height: 630,
        alt: "Sentinel: a recorded, evidence-linked incident investigation",
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
                An engineering project by{" "}
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
