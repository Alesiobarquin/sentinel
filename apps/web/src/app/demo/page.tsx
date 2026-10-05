import type { Metadata } from "next";
import { ReplayViewer } from "@/components/replay-viewer";

export const metadata: Metadata = {
  title: "Recorded investigation",
  alternates: { canonical: "/sentinel/demo/" },
};
export default function Demo() {
  return (
    <main id="main">
      <ReplayViewer />
    </main>
  );
}
