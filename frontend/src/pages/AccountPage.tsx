import { FormEvent, useEffect, useState } from "react";
import { CreditCard, Eye, RefreshCw, Trash2 } from "lucide-react";
import { bookingApi, demoGenres, userApi } from "../api/cinelux";
import { ErrorNote, Loading } from "../components/AsyncState";
import QrTicket from "../components/QrTicket";
import { useAuth } from "../state/auth";
import type { Booking, PaymentMethod } from "../types";
import { formatDateTime } from "../utils";

export default function AccountPage() {
  const { user, token, setUser } = useAuth();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [methods, setMethods] = useState<PaymentMethod[]>([]);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [prefs, setPrefs] = useState<string[]>(user?.preferredGenres ?? []);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function load() {
    if (!user) return;
    setLoading(true);
    setError("");
    try {
      const [bookingData, methodData] = await Promise.all([bookingApi.list(token), userApi.paymentMethods(user.userId, token)]);
      setBookings(bookingData.bookings);
      setMethods(methodData.paymentMethods);
      setPrefs(user.preferredGenres);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Account data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [user?.userId]);

  async function updateProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user) return;
    setError("");
    setSuccess("");
    const form = new FormData(event.currentTarget);
    try {
      const updated = await userApi.update(user.userId, token, {
        firstName: String(form.get("firstName")),
        lastName: String(form.get("lastName")),
        email: String(form.get("email")),
        phone: String(form.get("phone")),
        currentPassword: String(form.get("currentPassword") || "") || undefined,
        password: String(form.get("password") || "") || undefined,
      });
      const withPrefs = await userApi.preferences(user.userId, token, prefs);
      setUser({ ...updated, preferredGenres: withPrefs.preferredGenres });
      setSuccess("Profile updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Profile update failed.");
    }
  }

  async function addMethod(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user) return;
    setError("");
    setSuccess("");
    const form = new FormData(event.currentTarget);
    try {
      await userApi.addPaymentMethod(user.userId, token, {
        gatewayCustomerId: `cus_${user.userId.slice(0, 8)}`,
        gatewayToken: `tok_good_${String(form.get("last4"))}`,
        brand: String(form.get("brand")),
        last4: String(form.get("last4")),
        expMonth: Number(form.get("expMonth")),
        expYear: Number(form.get("expYear")),
        isDefault: methods.length === 0,
      });
      event.currentTarget.reset();
      setSuccess("Payment method saved.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment method could not be added.");
    }
  }

  async function cancel(bookingId?: string) {
    if (!bookingId) return;
    setError("");
    setSuccess("");
    try {
      await bookingApi.cancel(bookingId, token);
      setSelectedBooking(null);
      setSuccess("Booking cancelled.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cancellation failed.");
    }
  }

  async function openBooking(bookingId?: string) {
    if (!bookingId) return;
    setError("");
    try {
      setSelectedBooking(await bookingApi.detail(bookingId, token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Booking details could not be loaded.");
    }
  }

  async function removeMethod(methodId: string) {
    if (!user) return;
    setError("");
    setSuccess("");
    try {
      await userApi.deletePaymentMethod(user.userId, methodId, token);
      setSuccess("Payment method removed.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment method could not be removed.");
    }
  }

  if (loading && !bookings.length) return <main className="page"><Loading label="Loading account" /></main>;
  if (!user) return null;

  return (
    <main className="page account-grid">
      <section className="glass-panel">
        <div className="section-title"><div><h1>Profile</h1></div><span>{user.role}</span></div>
        <form className="form-stack" onSubmit={updateProfile}>
          <div className="two-col">
            <label>First name<input name="firstName" defaultValue={user.firstName} /></label>
            <label>Last name<input name="lastName" defaultValue={user.lastName} /></label>
          </div>
          <label>Email<input name="email" type="email" defaultValue={user.email} /></label>
          <label>Phone<input name="phone" defaultValue={user.phone} /></label>
          <div className="two-col">
            <label>Current password<input name="currentPassword" type="password" placeholder="Needed only to rotate password" /></label>
            <label>New password<input name="password" type="password" minLength={8} placeholder="Leave blank to keep current" /></label>
          </div>
          <div className="choice-grid">
            {demoGenres.map((genre) => <button type="button" className={prefs.includes(genre) ? "active" : ""} key={genre} onClick={() => setPrefs((current) => current.includes(genre) ? current.filter((g) => g !== genre) : [...current, genre])}>{genre}</button>)}
          </div>
          <button className="primary-button full">Save profile</button>
        </form>
      </section>
      <section className="glass-panel">
        <div className="section-title"><div><h2>Bookings</h2></div><button className="icon-button" onClick={load}><RefreshCw size={16} /></button></div>
        <div className="booking-list">
          {bookings.map((booking) => (
            <article className="booking-card" key={booking.bookingId}>
              <div><strong>{booking.movieTitle}</strong><span>{formatDateTime(booking.startTime)} Â· Seat {booking.seat}</span></div>
              {booking.qrCodeToken || booking.qrCodeUrl ? <span className="booking-qr-status">QR ready</span> : <code>{booking.status}</code>}
              <div className="inline-actions">
                <button className="secondary-button" onClick={() => openBooking(booking.bookingId)}><Eye size={15} /> Details</button>
                {booking.status === "CONFIRMED" && <button className="danger-button" onClick={() => cancel(booking.bookingId)}><Trash2 size={15} /> Cancel</button>}
              </div>
            </article>
          ))}
          {!bookings.length && <p className="muted">No bookings yet.</p>}
        </div>
        <p className="muted">Cancellations are available only inside the backend refund window. Used, cancelled, or late bookings are rejected by policy.</p>
        {selectedBooking && (
          <div className="detail-card">
            <div className="section-title"><div><h3>Booking details</h3></div><button className="icon-button" onClick={() => setSelectedBooking(null)}>Close</button></div>
            <div className="detail-list">
              <span>Movie<strong>{selectedBooking.movieTitle}</strong></span>
              <span>Status<strong>{selectedBooking.status}</strong></span>
              <span>Seats<strong>{selectedBooking.seats?.join(", ") || selectedBooking.seat || "Assigned at venue"}</strong></span>
              <span>Showtime<strong>{selectedBooking.startTime ? formatDateTime(selectedBooking.startTime) : "TBD"}</strong></span>
              <span>Total<strong>{selectedBooking.currency ? `${selectedBooking.currency} ${selectedBooking.totalAmount?.toFixed(2) ?? "--"}` : "--"}</strong></span>
              <span>QR token<strong>{selectedBooking.qrCodeToken || "Issued on primary seat only"}</strong></span>
            </div>
            <QrTicket
              token={selectedBooking.qrCodeToken}
              url={selectedBooking.qrCodeUrl}
              title={`${selectedBooking.movieTitle} ticket QR`}
              filename={`${selectedBooking.movieTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "cinelux"}-ticket-qr.png`}
            />
          </div>
        )}
      </section>
      <section className="glass-panel">
        <div className="section-title"><div><CreditCard size={18} /><h2>Payment Methods</h2></div></div>
        <div className="payment-list">
          {methods.map((method) => (
            <span className="payment-chip" key={method.methodId}>
              {method.brand || "Card"} Â·Â·Â·Â· {method.last4}
              <button className="icon-button" onClick={() => removeMethod(method.methodId)} aria-label={`Delete ${method.brand} ending ${method.last4}`}>
                <Trash2 size={14} />
              </button>
            </span>
          ))}
          {!methods.length && <p className="muted">No saved payment methods yet.</p>}
        </div>
        <form className="form-stack" onSubmit={addMethod}>
          <div className="two-col">
            <label>Brand<input name="brand" placeholder="Visa" /></label>
            <label>Last 4<input name="last4" pattern="\d{4}" required /></label>
          </div>
          <div className="two-col">
            <label>Month<input name="expMonth" type="number" min={1} max={12} defaultValue={12} /></label>
            <label>Year<input name="expYear" type="number" min={2026} defaultValue={2028} /></label>
          </div>
          <button className="secondary-button full">Add method</button>
        </form>
      </section>
      {success && <p className="success-inline">{success}</p>}
      {error && <ErrorNote message={error} />}
    </main>
  );
}
