import { FormEvent, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { KeyRound, UserPlus } from "lucide-react";
import { authApi, demoGenres } from "../api/cinelux";
import { ErrorNote } from "../components/AsyncState";
import { useAuth } from "../state/auth";

export default function AuthPage() {
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [prefs, setPrefs] = useState<string[]>(["Drama", "Mystery"]);

  if (isAuthenticated) return <Navigate to="/" replace />;

  async function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      await login(String(form.get("email")), String(form.get("password")));
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed.");
    } finally {
      setBusy(false);
    }
  }

  async function submitRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email"));
    const password = String(form.get("password"));
    try {
      await authApi.register({
        firstName: String(form.get("firstName")),
        lastName: String(form.get("lastName")),
        email,
        password,
        phone: String(form.get("phone")),
        preferredGenres: prefs,
      });
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Account could not be created.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page auth-layout">
      <section className="auth-copy">
        <span className="eyebrow">Member access</span>
        <h1>Step into CineLux with your seats, tastes, and tickets in sync.</h1>
        <div className="demo-logins">
          <span>Demo user: maya@cinelux.local / CineLuxUser2026</span>
          <span>Staff: staff@cinelux.local / CineLuxStaff2026</span>
          <span>Admin: admin@cinelux.local / AdminPass2026</span>
        </div>
      </section>
      <section className="auth-panel glass-panel">
        <div className="tabs">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}><KeyRound size={17} /> Sign in</button>
          <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}><UserPlus size={17} /> Join</button>
        </div>
        {mode === "login" ? (
          <form className="form-stack" onSubmit={submitLogin}>
            <label>Email<input name="email" type="email" defaultValue="maya@cinelux.local" required /></label>
            <label>Password<input name="password" type="password" defaultValue="CineLuxUser2026" required /></label>
            <button className="primary-button full" disabled={busy}>Sign in</button>
          </form>
        ) : (
          <form className="form-stack" onSubmit={submitRegister}>
            <div className="two-col">
              <label>First name<input name="firstName" required /></label>
              <label>Last name<input name="lastName" required /></label>
            </div>
            <label>Email<input name="email" type="email" required /></label>
            <label>Password<input name="password" type="password" minLength={8} required /></label>
            <label>Phone<input name="phone" placeholder="+1555010103" /></label>
            <div className="choice-grid">
              {demoGenres.map((genre) => (
                <button type="button" className={prefs.includes(genre) ? "active" : ""} key={genre} onClick={() => setPrefs((current) => current.includes(genre) ? current.filter((g) => g !== genre) : [...current, genre])}>{genre}</button>
              ))}
            </div>
            <button className="primary-button full" disabled={busy}>Create account</button>
          </form>
        )}
        {error && <ErrorNote message={error} />}
      </section>
    </main>
  );
}
