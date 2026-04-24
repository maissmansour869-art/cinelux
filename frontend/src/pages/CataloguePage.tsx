import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Calendar, Search, SlidersHorizontal, Sparkles } from "lucide-react";
import { catalogueApi, demoGenres } from "../api/cinelux";
import { ApiError } from "../api/client";
import MovieCard from "../components/MovieCard";
import { ErrorNote, Loading } from "../components/AsyncState";
import { useAuth } from "../state/auth";
import type { Movie } from "../types";
import { posterUrl, unique } from "../utils";

export default function CataloguePage() {
  const { user, token } = useAuth();
  const [movies, setMovies] = useState<Movie[]>([]);
  const [trending, setTrending] = useState<Movie[]>([]);
  const [recs, setRecs] = useState<Movie[]>([]);
  const [q, setQ] = useState("");
  const [genre, setGenre] = useState("");
  const [date, setDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ limit: "24" });
      if (q) params.set("q", q);
      if (genre) params.set("genre", genre);
      if (date) params.set("date", date);
      const [movieData, trendingData] = await Promise.all([catalogueApi.movies(params), catalogueApi.trending()]);
      setMovies(movieData.movies);
      setTrending(trendingData.movies);
      if (user && token) {
        const recommendationData = await catalogueApi.recommendations(user.userId, token);
        setRecs(recommendationData.recommendations);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Catalogue could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [user?.userId]);

  const hero = trending[0] ?? movies[0];
  const genres = useMemo(() => unique([...demoGenres, ...movies.flatMap((m) => m.genres)]).sort(), [movies]);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void load();
  }

  if (loading && !movies.length) return <main className="page"><Loading label="Opening the catalogue" /></main>;

  return (
    <main>
      {hero && (
        <section className="hero">
          {hero.posterUrl && <img src={posterUrl(hero.posterUrl)} alt="" />}
          <div className="hero-shade" />
          <div className="hero-copy">
            <span className="eyebrow">Premium selection</span>
            <h1>{hero.title}</h1>
            <p>{hero.description}</p>
            <div className="hero-actions">
              <Link className="primary-button" to={`/movies/${hero.movieId}`}>Book now</Link>
              <span className="meta-pill">{hero.ageRating || "Rated"} · {hero.durationMinutes} min</span>
            </div>
          </div>
        </section>
      )}

      <section className="floating-search">
        <form onSubmit={onSubmit} className="filter-bar">
          <label><Search size={18} /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search movies..." /></label>
          <label><SlidersHorizontal size={18} /><select value={genre} onChange={(e) => setGenre(e.target.value)}><option value="">All genres</option>{genres.map((g) => <option key={g}>{g}</option>)}</select></label>
          <label><Calendar size={18} /><input type="date" value={date} onChange={(e) => setDate(e.target.value)} /></label>
          <button className="icon-submit" aria-label="Filter catalogue"><Search size={21} /></button>
        </form>
      </section>

      <section className="page section-stack">
        {error && <ErrorNote message={error} />}
        {recs.length > 0 && (
          <section>
            <SectionTitle icon={<Sparkles size={18} />} title="Picked for You" action="Content-based recommendations" />
            <div className="movie-grid compact">{recs.map((movie) => <MovieCard key={movie.movieId} movie={movie} />)}</div>
          </section>
        )}
        <section>
          <SectionTitle title="Trending Now" action="Live from bookings and ratings" />
          <div className="bento-grid">{trending.slice(0, 5).map((movie, index) => <MovieCard key={movie.movieId} movie={movie} featured={index === 0} />)}</div>
        </section>
        <section>
          <SectionTitle title="Collection Catalogue" action={`${movies.length} films`} />
          <div className="movie-grid">{movies.map((movie) => <MovieCard key={movie.movieId} movie={movie} />)}</div>
        </section>
      </section>
    </main>
  );
}

function SectionTitle({ title, action, icon }: { title: string; action?: string; icon?: React.ReactNode }) {
  return <div className="section-title"><div>{icon}<h2>{title}</h2></div>{action && <span>{action}</span>}</div>;
}
