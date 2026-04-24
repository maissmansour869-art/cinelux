import { useEffect, useMemo, useState } from "react";
import { Download, ExternalLink } from "lucide-react";
import QRCode from "qrcode";

type QrTicketProps = {
  token?: string | null;
  url?: string | null;
  title?: string;
  filename?: string;
  className?: string;
};

export default function QrTicket({ token, url, title = "Ticket QR", filename = "cinelux-ticket-qr.png", className = "" }: QrTicketProps) {
  const [dataUrl, setDataUrl] = useState("");
  const [error, setError] = useState("");

  const qrValue = useMemo(() => token || url || "", [token, url]);

  useEffect(() => {
    let cancelled = false;

    async function generateQr() {
      if (!qrValue) {
        setDataUrl("");
        setError("");
        return;
      }

      try {
        const nextDataUrl = await QRCode.toDataURL(qrValue, {
          width: 280,
          margin: 2,
          color: {
            dark: "#111111",
            light: "#ffffff",
          },
        });

        if (!cancelled) {
          setDataUrl(nextDataUrl);
          setError("");
        }
      } catch {
        if (!cancelled) {
          setDataUrl("");
          setError("QR code could not be generated.");
        }
      }
    }

    void generateQr();

    return () => {
      cancelled = true;
    };
  }, [qrValue]);

  if (!qrValue) return <p className="muted">QR code will appear after confirmation.</p>;

  return (
    <div className={`qr-ticket ${className}`.trim()}>
      <div className="qr-ticket-frame">
        {dataUrl ? (
          <img className="qr-ticket-image" src={dataUrl} alt={title} />
        ) : (
          <div className="qr-ticket-placeholder">{error || "Generating QR..."}</div>
        )}
      </div>
      <div className="qr-ticket-actions">
        {dataUrl && (
          <a className="secondary-button full" href={dataUrl} download={filename}>
            <Download size={16} /> Download QR
          </a>
        )}
        {url && (
          <a className="secondary-button full" href={url} target="_blank" rel="noreferrer">
            <ExternalLink size={16} /> Open original
          </a>
        )}
      </div>
      {token && <p className="qr-ticket-token">Token: <code>{token}</code></p>}
    </div>
  );
}
