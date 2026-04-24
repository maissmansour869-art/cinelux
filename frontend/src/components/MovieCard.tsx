import { Link } from "react-router-dom";
import type { Movie } from "../types";
import { posterUrl } from "../utils";

export default function MovieCard({ movie, featured = false }: { movie: Movie; featured?: boolean }) {
  return (
    <Link to={`/movies/${movie.movieId}`} className={`movie-card ${featured ? "featured" : ""}`}>
      <div className="poster-frame">
        {movie.posterUrl ? <img src={posterUrl(movie.posterUrl)} alt={`${movie.title} poster`} /> : <div className="poster-fallback">{movie.title}</div>}
        <span className="rating-pill">{movie.rating.toFixed(1)}</span>
      </div>
      <h3>{movie.title}</h3>
      <p>{movie.genres.slice(0, 2).join(" / ") || "Cinema"}</p>
    </Link>
  );
}
