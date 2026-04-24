import { AlertTriangle, Loader2 } from "lucide-react";

export function Loading({ label = "Loading" }: { label?: string }) {
  return <div className="state-panel"><Loader2 className="spin" size={20} /> {label}</div>;
}

export function ErrorNote({ message }: { message: string }) {
  return <div className="state-panel error"><AlertTriangle size={18} /> {message}</div>;
}
