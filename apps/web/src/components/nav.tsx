"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "./icons";
import { REPO } from "@/lib/replay";

export function Nav() {
  const path =
    usePathname()
      .replace(/^\/sentinel/, "")
      .replace(/\/$/, "") || "/";
  return (
    <header className="site-header">
      <div className="container nav-wrap">
        <Link href="/" className="brand" aria-label="Sentinel home">
          Sentinel<span className="brand-note">/ student project</span>
        </Link>
        <nav aria-label="Main navigation">
          <Link
            href="/demo/"
            aria-current={path === "/demo" ? "page" : undefined}
          >
            Demo
          </Link>
          <Link
            href="/project/"
            aria-current={path === "/project" ? "page" : undefined}
          >
            The project
          </Link>
          <a href={REPO} className="nav-source" aria-label="Source on GitHub">
            <span>Source</span>
            <Icon name="external" size={15} />
          </a>
        </nav>
      </div>
    </header>
  );
}
