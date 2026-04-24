import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Clock, Languages, Star } from "lucide-react";
import { catalogueApi } from "../api/cinelux";
import { ErrorNote, Loading } from "../components/AsyncState";
import type { Movie, Showtime } from "../types";
import { formatDateTime, posterUrl } from "../utils";

export default function MoviePage() {
  const { movieId = "" } = useParams();
  const [movie, setMovie] = useState<Movie | null>(null);
  const [showtimes, setShowtimes] = useState<Showtime[]>([]);
  const [date, setDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load(targetDate = date) {
    setLoading(true);
    setError("");
    try {
      const [movieData, showtimeData] = await Promise.all([catalogueApi.movie(movieId), catalogueApi.showtimes(movieId, targetDate)]);
      setMovie(movieData);
      setShowtimes(showtimeData.showtimes);
    } catch {
      setError("Movie details could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(""); }, [movieId]);

  if (loading && !movie) return <main className="page"><Loading /></main>;
  if (!movie) return <main className="page"><ErrorNote message={error || "Movie not found."} /></main>;

  return (
    <main className="movie-detail">
      <div className="detail-backdrop">{movie.posterUrl && <img src={posterUrl(movie.posterUrl)} alt="" />}</div>
      <section className="page detail-layout">
        <Link className="back-link" to="/"><ArrowLeft size={17} /> Catalogue</Link>
        <div className="detail-poster">{movie.posterUrl && <img src={posterUrl(movie.posterUrl)} alt={`${movie.title} poster`} />}</div>
        <div className="detail-copy">
          <span className="eyebrow">{movie.genres.join(" / ")}</span>
          <h1>{movie.title}</h1>
          <p>{movie.description}</p>
          <div className="detail-meta">
            <span><Star size={16} /> {movie.rating.toFixed(1)}</span>
            <span><Clock size={16} /> {movie.durationMinutes} min</span>
            <span><Languages size={16} /> {movie.language || "English"}</span>
            <span>{movie.ageRating || "NR"}</span>
          </div>
          <div className="showtime-panel">
            <div className="panel-heading">
              <h2>Showtimes</h2>
              <input type="date" value={date} onChange={(e) => { setDate(e.target.value); void load(e.target.value); }} />
            </div>
            <div className="showtime-list">
              {showtimes.length ? showtimes.map((showtime) => (
                <Link className="showtime-card" to={`/book/${showtime.showtimeId}`} key={showtime.showtimeId}>
                  <strong>{formatDateTime(showtime.startTime)}</strong>
                  <span>{showtime.hallName} · {showtime.availableSeats ?? showtime.totalSeats} seats left</span>
                  <b>{showtime.currency} {showtime.price.toFixed(2)}</b>
                </Link>
              )) : <p className="muted">No upcoming showtimes match this date.</p>}
            </div>
          </div>
          {error && <ErrorNote message={error} />}
        </div>
      </section>
    </main>
  );
}
