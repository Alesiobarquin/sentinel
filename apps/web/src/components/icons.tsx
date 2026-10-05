import type { CSSProperties } from "react";

type Props = {
  name:
    | "arrow"
    | "external"
    | "check"
    | "play"
    | "pause"
    | "back"
    | "reset"
    | "code"
    | "signal";
  size?: number;
  style?: CSSProperties;
};
export function Icon({ name, size = 18, style }: Props) {
  const paths = {
    arrow: "M5 12h14M13 6l6 6-6 6",
    external:
      "M14 3h7v7M21 3l-9 9M10 3H4a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1v-6",
    check: "m5 12 4 4L19 6",
    play: "m8 5 11 7-11 7V5Z",
    pause: "M8 5v14M16 5v14",
    back: "M19 12H5m6-6-6 6 6 6",
    reset: "M3 10a9 9 0 1 1 2 8M3 4v6h6",
    code: "m8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18",
    signal: "M3 12h4l3-8 4 16 3-8h4",
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      style={style}
    >
      <path d={paths[name]} />
    </svg>
  );
}
export function Mark() {
  return (
    <svg
      viewBox="0 0 32 32"
      width="30"
      height="30"
      fill="none"
      aria-hidden="true"
    >
      <rect width="32" height="32" rx="9" fill="currentColor" />
      <path
        d="M10 10H8v12h2m12-12h2v12h-2M12 16h2l2-5 2 10 2-5"
        stroke="#fff"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
