export function formatDateTime(value?: string) {
  if (!value) return "TBA";
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export function posterUrl(url?: string) {
  if (!url) return "";
  if (url.startsWith("http://localhost:8000")) return url.replace("http://localhost:8000", "");
  return url;
}

export function initials(first?: string, last?: string) {
  return `${first?.[0] ?? "C"}${last?.[0] ?? "L"}`;
}

export function unique<T>(items: T[]) {
  return Array.from(new Set(items));
}
