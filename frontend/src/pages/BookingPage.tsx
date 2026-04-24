import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { BadgeCheck, TimerReset } from "lucide-react";
import { bookingApi } from "../api/cinelux";
import { ErrorNote, Loading } from "../components/AsyncState";
import QrTicket from "../components/QrTicket";
import SeatMap from "../components/SeatMap";
import { useAuth } from "../state/auth";
import type { Booking, Seat } from "../types";

export default function BookingPage() {
  const { showtimeId = "" } = useParams();
  const { token } = useAuth();
  const [seats, setSeats] = useState<Seat[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [price, setPrice] = useState(0);
  const [currency, setCurrency] = useState("USD");
  const [hold, setHold] = useState<{ bookingGroupId: string; holdExpiresAt: string } | null>(null);
  const [ticket, setTicket] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadSeats() {
      setLoading(true);
      try {
        const data = await bookingApi.seats(showtimeId, token);
        setSeats(data.seats);
        setPrice(data.price);
        setCurrency(data.currency);
      } catch {
        setError("Seat map could not be loaded.");
      } finally {
        setLoading(false);
      }
    }
    void loadSeats();
  }, [showtimeId, token]);

  const total = useMemo(() => selected.length * price, [selected, price]);

  function toggleSeat(seat: Seat) {
    setSelected((current) => current.includes(seat.seatId) ? current.filter((id) => id !== seat.seatId) : [...current, seat.seatId]);
    setHold(null);
    setTicket(null);
  }

  async function holdSeats() {
    setBusy(true);
    setError("");
    try {
      setHold(await bookingApi.hold(showtimeId, selected, token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not hold selected seats.");
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    if (!hold) return;
    setBusy(true);
    setError("");
    try {
      setTicket(await bookingApi.confirm(hold.bookingGroupId, token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment could not be completed.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <main className="page"><Loading label="Preparing seat map" /></main>;

  return (
    <main className="page booking-layout">
      <section className="glass-panel">
        <div className="section-title"><div><h1>Select Seats</h1></div><span>{currency} {price.toFixed(2)} each</span></div>
        <SeatMap seats={seats} selected={selected} onToggle={toggleSeat} />
      </section>
      <aside className="checkout-panel">
        <span className="eyebrow">Checkout</span>
        <h2>{selected.length || "No"} seats selected</h2>
        <p className="muted">Your seats are held before payment so another guest cannot claim them mid-checkout.</p>
        <div className="summary-row"><span>Total</span><strong>{currency} {total.toFixed(2)}</strong></div>
        <button className="primary-button full" disabled={!selected.length || busy || Boolean(hold)} onClick={holdSeats}>
          <TimerReset size={18} /> Hold seats
        </button>
        {hold && !ticket && (
          <div className="hold-box">
            <strong>Held until {new Date(hold.holdExpiresAt).toLocaleTimeString()}</strong>
            <button className="primary-button full" disabled={busy} onClick={confirm}>Pay with simulated card</button>
          </div>
        )}
        {ticket && (
          <div className="success-box">
            <BadgeCheck size={28} />
            <h3>Booking confirmed</h3>
            <p>{ticket.movieTitle}</p>
            <QrTicket
              token={ticket.qrCodeToken}
              url={ticket.qrCodeUrl}
              title={`${ticket.movieTitle} ticket QR`}
              filename={`${ticket.movieTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "cinelux"}-ticket-qr.png`}
            />
            <Link className="secondary-button full" to="/account">View tickets</Link>
          </div>
        )}
        {error && <ErrorNote message={error} />}
      </aside>
    </main>
  );
}
