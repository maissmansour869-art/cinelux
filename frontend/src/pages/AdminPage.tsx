import { FormEvent, useEffect, useMemo, useState } from "react";
import { Building2, CalendarClock, Film, Pencil, PlusCircle, Trash2, UserCog } from "lucide-react";
import { adminApi, catalogueApi, demoGenres } from "../api/cinelux";
import { ErrorNote, Loading } from "../components/AsyncState";
import { useAuth } from "../state/auth";
import type { Hall, Movie, Showtime, User } from "../types";
import { formatDateTime } from "../utils";

type EditableMovie = Record<string, string>;
type EditableShowtime = Record<string, string>;
type EditableHall = Record<string, string>;
type AdminSectionId = "users" | "halls" | "movies" | "showtimes";

export default function AdminPage() {
  const { token } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [halls, setHalls] = useState<Hall[]>([]);
  const [movies, setMovies] = useState<Movie[]>([]);
  const [showtimes, setShowtimes] = useState<Showtime[]>([]);
  const [editableMovies, setEditableMovies] = useState<EditableMovie>({});
  const [editableShowtimes, setEditableShowtimes] = useState<EditableShowtime>({});
  const [editableHalls, setEditableHalls] = useState<EditableHall>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [activeSection, setActiveSection] = useState<AdminSectionId>("users");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [usersData, hallsData, moviesData] = await Promise.all([
        adminApi.users(token),
        adminApi.halls(token),
        catalogueApi.movies(new URLSearchParams({ limit: "100" })),
      ]);
      const showtimeGroups = await Promise.all(
        moviesData.movies.map(async (movie) => {
          const data = await catalogueApi.showtimes(movie.movieId);
          return data.showtimes;
        }),
      );
      setUsers(usersData.users);
      setHalls(hallsData.halls);
      setMovies(moviesData.movies);
      setShowtimes(showtimeGroups.flat());
      setEditableMovies(Object.fromEntries(moviesData.movies.map((movie) => [movie.movieId, movie.genres.join(", ")])));
      setEditableShowtimes(
        Object.fromEntries(
          showtimeGroups.flat().map((showtime) => [showtime.showtimeId, toLocalDateTime(showtime.startTime)]),
        ),
      );
      setEditableHalls(Object.fromEntries(hallsData.halls.map((hall) => [hall.hallId, hall.name])));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Admin data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [token]);

  const movieLookup = useMemo(() => Object.fromEntries(movies.map((movie) => [movie.movieId, movie.title])), [movies]);
  const sections = [
    { id: "users", label: "Users", icon: UserCog, detail: `${users.length} accounts` },
    { id: "halls", label: "Halls", icon: Building2, detail: `${halls.length} spaces` },
    { id: "movies", label: "Movies", icon: Film, detail: `${movies.length} titles` },
    { id: "showtimes", label: "Showtimes", icon: CalendarClock, detail: `${showtimes.length} upcoming` },
  ] as const;

  async function patchUser(userId: string, field: "role" | "status", value: string) {
    setError("");
    setSuccess("");
    try {
      await adminApi.patchUser(userId, token, { [field]: value });
      setSuccess("User updated.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "User update failed.");
    }
  }

  async function createUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    const form = new FormData(event.currentTarget);
    try {
      await adminApi.createUser(token, {
        firstName: String(form.get("firstName")),
        lastName: String(form.get("lastName")),
        email: String(form.get("email")),
        password: String(form.get("password")),
        phone: String(form.get("phone")),
        preferredGenres: [],
        role: String(form.get("role")),
      });
      event.currentTarget.reset();
      setSuccess("User created.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "User creation failed.");
    }
  }

  async function createHall(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    const form = new FormData(event.currentTarget);
    try {
      await adminApi.createHall(token, String(form.get("name")));
      event.currentTarget.reset();
      setSuccess("Hall created.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hall creation failed.");
    }
  }

  async function renameHall(hallId: string) {
    setError("");
    setSuccess("");
    try {
      await adminApi.updateHall(token, hallId, { name: editableHalls[hallId] });
      setSuccess("Hall updated.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hall update failed.");
    }
  }

  async function createSeatMap(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    const form = new FormData(event.currentTarget);
    const hallId = String(form.get("hallId"));
    try {
      await adminApi.createSeatMap(token, hallId, [
        { label: "A", seatCount: 8, type: "PREMIUM" },
        { label: "B", seatCount: 8, type: "PREMIUM" },
        { label: "C", seatCount: 10, type: "STANDARD" },
        { label: "D", seatCount: 10, type: "STANDARD" },
        { label: "E", seatCount: 6, type: "ACCESSIBLE" },
      ]);
      setSuccess("Seat map created.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Seat map creation failed.");
    }
  }

  async function createMovie(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    const form = new FormData(event.currentTarget);
    try {
      await adminApi.createMovie(token, {
        title: String(form.get("title")),
        description: String(form.get("description")),
        durationMinutes: Number(form.get("durationMinutes")),
        releaseDate: String(form.get("releaseDate")) || null,
        language: String(form.get("language")),
        ageRating: String(form.get("ageRating")),
        posterUrl: String(form.get("posterUrl")),
        genres: String(form.get("genres")).split(",").map((g) => g.trim()).filter(Boolean),
      });
      event.currentTarget.reset();
      setSuccess("Movie created.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Movie creation failed.");
    }
  }

  async function updateMovie(movie: Movie) {
    setError("");
    setSuccess("");
    try {
      await adminApi.updateMovie(token, movie.movieId, {
        title: movie.title,
        description: movie.description,
        durationMinutes: movie.durationMinutes,
        releaseDate: movie.releaseDate,
        language: movie.language,
        ageRating: movie.ageRating,
        posterUrl: movie.posterUrl,
        genres: (editableMovies[movie.movieId] ?? "").split(",").map((g) => g.trim()).filter(Boolean),
      });
      setSuccess("Movie updated.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Movie update failed.");
    }
  }

  async function removeMovie(movieId: string) {
    setError("");
    setSuccess("");
    try {
      await adminApi.deleteMovie(token, movieId);
      setSuccess("Movie archived.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Movie deletion failed.");
    }
  }

  async function createShowtime(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    const form = new FormData(event.currentTarget);
    try {
      await adminApi.createShowtime(token, {
        movieId: String(form.get("movieId")),
        hallId: String(form.get("hallId")),
        startTime: new Date(String(form.get("startTime"))).toISOString(),
        price: String(form.get("price")),
        currency: "USD",
      });
      event.currentTarget.reset();
      setSuccess("Showtime created.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Showtime creation failed.");
    }
  }

  async function updateShowtime(showtime: Showtime) {
    setError("");
    setSuccess("");
    try {
      await adminApi.updateShowtime(token, showtime.showtimeId, {
        movieId: showtime.movieId,
        hallId: showtime.hallId,
        startTime: new Date(editableShowtimes[showtime.showtimeId]).toISOString(),
        price: String(showtime.price),
        currency: showtime.currency,
      });
      setSuccess("Showtime updated.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Showtime update failed.");
    }
  }

  async function removeShowtime(showtimeId: string) {
    setError("");
    setSuccess("");
    try {
      await adminApi.deleteShowtime(token, showtimeId);
      setSuccess("Showtime removed.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Showtime deletion failed.");
    }
  }

  if (loading && !users.length) return <main className="page"><Loading label="Loading admin console" /></main>;

  return (
    <main className="page admin-shell">
      <aside className="glass-panel admin-sidebar">
        <div className="admin-sidebar__intro">
          <p className="eyebrow">Control Center</p>
          <h1>Admin Console</h1>
          <p>Jump between teams, inventory, and scheduling without scrolling through the whole back office.</p>
        </div>
        <nav className="admin-sidebar__nav" aria-label="Admin sections">
          {sections.map((section) => {
            const Icon = section.icon;
            const isActive = activeSection === section.id;
            return (
              <button
                key={section.id}
                type="button"
                className={`admin-nav-button${isActive ? " active" : ""}`}
                onClick={() => setActiveSection(section.id)}
              >
                <span className="admin-nav-button__icon"><Icon size={18} /></span>
                <span>
                  <strong>{section.label}</strong>
                  <small>{section.detail}</small>
                </span>
              </button>
            );
          })}
        </nav>
        <div className="admin-sidebar__meta">
          <span className="meta-pill">4 focused workspaces</span>
          <span className="meta-pill">Live admin actions</span>
        </div>
      </aside>

      <div className="admin-content">
        <section className={`glass-panel admin-section${activeSection === "users" ? " active" : ""}`}>
        <div className="section-title"><div><UserCog size={18} /><h1>User Management</h1></div><span>{users.length} accounts</span></div>
        <div className="admin-table">
          {users.map((user) => (
            <article key={user.userId}>
              <div><strong>{user.firstName} {user.lastName}</strong><span>{user.email}</span></div>
              <select value={user.role} onChange={(e) => patchUser(user.userId, "role", e.target.value)}><option>USER</option><option>STAFF</option><option>ADMIN</option></select>
              <select value={user.status} onChange={(e) => patchUser(user.userId, "status", e.target.value)}><option>ACTIVE</option><option>SUSPENDED</option></select>
            </article>
          ))}
        </div>
        <form className="form-stack top-gap" onSubmit={createUser}>
          <div className="section-title"><div><PlusCircle size={18} /><h2>Create account</h2></div></div>
          <div className="two-col">
            <label>First name<input name="firstName" required /></label>
            <label>Last name<input name="lastName" required /></label>
          </div>
          <label>Email<input name="email" type="email" required /></label>
          <div className="two-col">
            <label>Password<input name="password" type="password" minLength={8} required /></label>
            <label>Role<select name="role" defaultValue="USER"><option>USER</option><option>STAFF</option><option>ADMIN</option></select></label>
          </div>
          <label>Phone<input name="phone" /></label>
          <button className="secondary-button full">Create user</button>
        </form>
        </section>

        <section className={`glass-panel admin-section${activeSection === "halls" ? " active" : ""}`}>
        <div className="section-title"><div><Building2 size={18} /><h2>Halls</h2></div></div>
        <form className="form-stack" onSubmit={createHall}>
          <label>Name<input name="name" placeholder="Hall 3" required /></label>
          <button className="secondary-button full">Create hall</button>
        </form>
        <form className="form-stack" onSubmit={createSeatMap}>
          <label>Seat map hall<select name="hallId">{halls.map((hall) => <option value={hall.hallId} key={hall.hallId}>{hall.name}</option>)}</select></label>
          <button className="secondary-button full">Create luxe seat map</button>
        </form>
        <div className="admin-list">
          {halls.map((hall) => (
            <article className="admin-card" key={hall.hallId}>
              <label>Hall name<input value={editableHalls[hall.hallId] ?? hall.name} onChange={(e) => setEditableHalls((current) => ({ ...current, [hall.hallId]: e.target.value }))} /></label>
              <span className="muted">{hall.totalSeats} seats</span>
              <button className="secondary-button full" onClick={() => renameHall(hall.hallId)}><Pencil size={15} /> Save hall</button>
            </article>
          ))}
        </div>
        </section>

        <section className={`glass-panel admin-section${activeSection === "movies" ? " active" : ""}`}>
        <div className="section-title"><div><Film size={18} /><h2>Movies</h2></div></div>
        <form className="form-stack" onSubmit={createMovie}>
          <label>Title<input name="title" required /></label>
          <label>Description<textarea name="description" required /></label>
          <div className="two-col"><label>Runtime<input name="durationMinutes" type="number" min={1} defaultValue={110} /></label><label>Rating<input name="ageRating" defaultValue="PG-13" /></label></div>
          <div className="two-col"><label>Release<input name="releaseDate" type="date" /></label><label>Language<input name="language" defaultValue="English" /></label></div>
          <label>Poster URL<input name="posterUrl" type="url" placeholder="https://..." /></label>
          <label>Genres<input name="genres" defaultValue={demoGenres.slice(0, 2).join(", ")} /></label>
          <button className="secondary-button full">Create movie</button>
        </form>
        <div className="admin-list">
          {movies.map((movie) => (
            <article className="admin-card" key={movie.movieId}>
              <strong>{movie.title}</strong>
              <span className="muted">{movie.durationMinutes} min · {movie.language || "English"}</span>
              <label>Genres<input value={editableMovies[movie.movieId] ?? movie.genres.join(", ")} onChange={(e) => setEditableMovies((current) => ({ ...current, [movie.movieId]: e.target.value }))} /></label>
              <div className="inline-actions">
                <button className="secondary-button" onClick={() => updateMovie(movie)}><Pencil size={15} /> Save</button>
                <button className="danger-button" onClick={() => removeMovie(movie.movieId)}><Trash2 size={15} /> Delete</button>
              </div>
            </article>
          ))}
        </div>
        </section>

        <section className={`glass-panel admin-section${activeSection === "showtimes" ? " active" : ""}`}>
        <div className="section-title"><div><h2>Showtimes</h2></div><span>{showtimes.length} upcoming</span></div>
        <form className="form-stack" onSubmit={createShowtime}>
          <label>Movie<select name="movieId">{movies.map((movie) => <option value={movie.movieId} key={movie.movieId}>{movie.title}</option>)}</select></label>
          <label>Hall<select name="hallId">{halls.map((hall) => <option value={hall.hallId} key={hall.hallId}>{hall.name}</option>)}</select></label>
          <div className="two-col"><label>Starts<input name="startTime" type="datetime-local" required /></label><label>Price<input name="price" type="number" step="0.01" defaultValue="14.50" /></label></div>
          <button className="primary-button full">Create showtime</button>
        </form>
        <div className="admin-list">
          {showtimes.map((showtime) => (
            <article className="admin-card" key={showtime.showtimeId}>
              <strong>{movieLookup[showtime.movieId] || "Movie"}</strong>
              <span className="muted">{showtime.hallName} · {formatDateTime(showtime.startTime)}</span>
              <div className="two-col">
                <label>Start<input type="datetime-local" value={editableShowtimes[showtime.showtimeId] ?? toLocalDateTime(showtime.startTime)} onChange={(e) => setEditableShowtimes((current) => ({ ...current, [showtime.showtimeId]: e.target.value }))} /></label>
                <label>Price<input type="number" step="0.01" value={showtime.price} onChange={(e) => setShowtimes((current) => current.map((entry) => entry.showtimeId === showtime.showtimeId ? { ...entry, price: Number(e.target.value) } : entry))} /></label>
              </div>
              <div className="inline-actions">
                <button className="secondary-button" onClick={() => updateShowtime(showtime)}><Pencil size={15} /> Save</button>
                <button className="danger-button" onClick={() => removeShowtime(showtime.showtimeId)}><Trash2 size={15} /> Delete</button>
              </div>
            </article>
          ))}
        </div>
        </section>

        <section className="admin-feedback">
          {success && <p className="success-inline">{success}</p>}
          {error && <ErrorNote message={error} />}
        </section>
      </div>
    </main>
  );
}

function toLocalDateTime(value: string) {
  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60000);
  return local.toISOString().slice(0, 16);
}
