import { ChangeEvent, ClipboardEvent, FormEvent, useEffect, useRef, useState } from "react";
import { Camera, ImageUp, ScanLine, ShieldCheck } from "lucide-react";
import jsQR from "jsqr";
import { bookingApi } from "../api/cinelux";
import { ErrorNote } from "../components/AsyncState";
import { useAuth } from "../state/auth";

type ValidationResult = {
  result: string;
  movieTitle: string;
  hall: string;
  seats: string[];
};

declare global {
  interface Window {
    BarcodeDetector?: {
      new (options?: { formats?: string[] }): {
        detect(source: ImageBitmapSource): Promise<Array<{ rawValue?: string }>>;
      };
      getSupportedFormats?: () => Promise<string[]>;
    };
  }
}

export default function StaffPage() {
  const { token } = useAuth();
  const [qrToken, setQrToken] = useState("");
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [decodeBusy, setDecodeBusy] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraSupported, setCameraSupported] = useState(false);
  const [cameraMode, setCameraMode] = useState<"barcode-detector" | "jsqr" | null>(null);
  const [scanHint, setScanHint] = useState("Upload, paste, or scan a ticket QR image.");

  const formRef = useRef<HTMLFormElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const frameRef = useRef<number | null>(null);
  const detectorRef = useRef<InstanceType<NonNullable<typeof window.BarcodeDetector>> | null>(null);

  useEffect(() => {
    const mediaSupported = typeof navigator !== "undefined" && Boolean(navigator.mediaDevices?.getUserMedia);
    setCameraSupported(mediaSupported);
  }, []);

  useEffect(() => () => stopCamera(), []);

  useEffect(() => {
    async function attachCameraPreview() {
      if (!cameraOpen || !videoRef.current || !streamRef.current) return;

      try {
        videoRef.current.srcObject = streamRef.current;
        await videoRef.current.play();
        setCameraReady(true);
        frameRef.current = requestAnimationFrame(scanCameraFrame);
      } catch (err) {
        stopCamera();
        setError(err instanceof Error ? err.message : "Camera preview could not be started.");
        setScanHint("Camera access failed. You can still upload or paste a QR image.");
      }
    }

    void attachCameraPreview();
  }, [cameraOpen, cameraMode]);

  function stopCamera() {
    if (frameRef.current !== null) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraReady(false);
    setCameraOpen(false);
    setCameraMode(null);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      setResult(await bookingApi.validate(qrToken.trim(), token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ticket validation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function decodeQrFromFile(file: File) {
    setDecodeBusy(true);
    setError("");
    setResult(null);
    setScanHint(`Decoding ${file.name || "image"}...`);

    try {
      const tokenValue = await extractQrValue(file);
      setQrToken(tokenValue);
      setScanHint("QR detected. You can validate now or edit the token first.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "QR code could not be read from that image.");
      setScanHint("Try a sharper image, better lighting, or use the camera scanner.");
    } finally {
      setDecodeBusy(false);
    }
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    await decodeQrFromFile(file);
    event.target.value = "";
  }

  async function handlePaste(event: ClipboardEvent<HTMLDivElement>) {
    const imageItem = Array.from(event.clipboardData.items).find((item) => item.type.startsWith("image/"));
    if (!imageItem) return;
    const file = imageItem.getAsFile();
    if (!file) return;
    event.preventDefault();
    await decodeQrFromFile(file);
  }

  async function startCamera() {
    if (!cameraSupported) {
      setError("Camera access is not available in this browser.");
      return;
    }

    setError("");
    setScanHint("Starting camera...");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" },
        },
        audio: false,
      });

      streamRef.current = stream;
      setCameraOpen(true);

      let nextCameraMode: "barcode-detector" | "jsqr" = "jsqr";

      if (window.BarcodeDetector) {
        if (typeof window.BarcodeDetector.getSupportedFormats === "function") {
          try {
            const formats = await window.BarcodeDetector.getSupportedFormats();
            if (formats.includes("qr_code")) {
              detectorRef.current = detectorRef.current ?? new window.BarcodeDetector({ formats: ["qr_code"] });
              nextCameraMode = "barcode-detector";
            }
          } catch {
            detectorRef.current = detectorRef.current ?? new window.BarcodeDetector({ formats: ["qr_code"] });
            nextCameraMode = "barcode-detector";
          }
        } else {
          detectorRef.current = detectorRef.current ?? new window.BarcodeDetector({ formats: ["qr_code"] });
          nextCameraMode = "barcode-detector";
        }
      }

      setCameraMode(nextCameraMode);
      setScanHint(nextCameraMode === "barcode-detector" ? "Point the camera at the QR code." : "Camera is on. Scanning frames locally for a QR code.");
    } catch (err) {
      stopCamera();
      setError(err instanceof Error ? err.message : "Camera could not be started.");
      setScanHint("Camera access failed. You can still upload or paste a QR image.");
    }
  }

  async function scanCameraFrame() {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
      frameRef.current = requestAnimationFrame(scanCameraFrame);
      return;
    }

    try {
      let value = "";

      if (cameraMode === "barcode-detector" && detectorRef.current) {
        const codes = await detectorRef.current.detect(video);
        value = codes.find((code) => Boolean(code.rawValue))?.rawValue?.trim() || "";
      } else {
        const context = canvas.getContext("2d", { willReadFrequently: true });
        if (!context) throw new Error("Camera QR decoding canvas could not be created.");

        const width = video.videoWidth;
        const height = video.videoHeight;

        if (!width || !height) {
          frameRef.current = requestAnimationFrame(scanCameraFrame);
          return;
        }

        canvas.width = width;
        canvas.height = height;
        context.drawImage(video, 0, 0, width, height);

        const imageData = context.getImageData(0, 0, width, height);
        value = jsQR(imageData.data, width, height)?.data?.trim() || "";
      }

      if (value) {
        setQrToken(value);
        setScanHint("QR detected from camera. Ready to validate.");
        stopCamera();
        return;
      }
    } catch {
      setError("Live camera scanning failed. Try image upload instead.");
      stopCamera();
      return;
    }

    frameRef.current = requestAnimationFrame(scanCameraFrame);
  }

  async function extractQrValue(file: File) {
    const bitmap = await createImageBitmap(file);

    try {
      if (window.BarcodeDetector) {
        const detector = detectorRef.current ?? new window.BarcodeDetector({ formats: ["qr_code"] });
        detectorRef.current = detector;
        const codes = await detector.detect(bitmap);
        const detectedValue = codes.find((code) => Boolean(code.rawValue))?.rawValue?.trim();
        if (detectedValue) return detectedValue;
      }

      const canvas = canvasRef.current ?? document.createElement("canvas");
      const context = canvas.getContext("2d", { willReadFrequently: true });

      if (!context) throw new Error("QR decoding canvas could not be created.");

      canvas.width = bitmap.width;
      canvas.height = bitmap.height;
      context.drawImage(bitmap, 0, 0);

      const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
      const decoded = jsQR(imageData.data, imageData.width, imageData.height);

      if (!decoded?.data) throw new Error("No QR code was detected in that image.");

      return decoded.data.trim();
    } finally {
      bitmap.close();
    }
  }

  return (
    <main className="page staff-layout">
      <section>
        <span className="eyebrow">Gate staff</span>
        <h1>Validate ticket entry</h1>
        <p className="muted">Paste the token, upload a QR screenshot, paste an image from clipboard, or scan live with the camera.</p>
      </section>
      <section className="glass-panel validator-panel" onPaste={handlePaste}>
        <ScanLine size={42} />
        <div className="validator-tools">
          <label className="secondary-button full validator-upload">
            <ImageUp size={16} /> Upload QR image
            <input type="file" accept="image/*" onChange={handleFileChange} hidden />
          </label>
          <button className="secondary-button full" type="button" onClick={cameraOpen ? stopCamera : startCamera} disabled={!cameraSupported && !cameraOpen}>
            <Camera size={16} /> {cameraOpen ? "Stop camera" : "Scan with camera"}
          </button>
        </div>
        <p className="muted">{decodeBusy ? "Reading QR image..." : scanHint}</p>
        {cameraOpen && (
          <div className="camera-panel">
            <video ref={videoRef} className="camera-preview" muted playsInline autoPlay />
            <div className="camera-frame" aria-hidden="true" />
            {!cameraReady && <p className="muted">Preparing camera preview...</p>}
          </div>
        )}
        <form ref={formRef} className="form-stack" onSubmit={submit}>
          <label>QR token<input name="qrToken" placeholder="QR-..." required value={qrToken} onChange={(event) => setQrToken(event.target.value)} /></label>
          <button className="primary-button full" disabled={busy || decodeBusy || !qrToken.trim()}>Validate</button>
        </form>
        {result && (
          <div className="success-box">
            <ShieldCheck size={32} />
            <h2>{String(result.result)}</h2>
            <p>{String(result.movieTitle)} · {String(result.hall)}</p>
            <strong>{Array.isArray(result.seats) ? result.seats.join(", ") : ""}</strong>
          </div>
        )}
        {!cameraSupported && <p className="muted">This browser cannot access a camera here, but upload and paste still work.</p>}
        {error && <ErrorNote message={error} />}
        <canvas ref={canvasRef} hidden />
      </section>
    </main>
  );
}
