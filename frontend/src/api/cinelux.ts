import { api, asJson } from "./client";
import type { Booking, Hall, Movie, PaymentMethod, Seat, Showtime, User } from "../types";

export const demoGenres = [
  "Action", "Adventure", "Animation", "Comedy", "Drama", "Family", "Fantasy",
  "History", "Horror", "Mystery", "Romance", "Sci-Fi", "Thriller",
];

export const authApi = {
  login: (email: string, password: string) =>
    api<{ token: string; refreshToken: string; expiresIn: number; userId: string }>("/api/users/login", {
      method: "POST",
      body: asJson({ email, password }),
    }),
  register: (payload: Record<string, unknown>) =>
    api<User>("/api/users/register", { method: "POST", body: asJson(payload) }),
  profile: (userId: string, token: string) => api<User>(`/api/users/${userId}`, { token }),
};

export const catalogueApi = {
  movies: (params: URLSearchParams) => api<{ movies: Movie[]; total: number }>(`/api/movies?${params}`),
  trending: () => api<{ movies: Movie[] }>("/api/movies/trending?limit=6"),
  movie: (movieId: string) => api<Movie>(`/api/movies/${movieId}`),
  showtimes: (movieId: string, date?: string) =>
    api<{ showtimes: Showtime[] }>(`/api/movies/${movieId}/showtimes${date ? `?date=${date}` : ""}`),
  recommendations: (userId: string, token: string) =>
    api<{ recommendations: Movie[]; algorithm: string; coldStart: boolean }>(`/api/recommendations/${userId}?limit=6`, { token }),
};

export const bookingApi = {
  seats: (showtimeId: string, token: string) =>
    api<{ seats: Seat[]; hallName: string; price: number; currency: string }>(`/api/showtimes/${showtimeId}/seats`, { token }),
  hold: (showtimeId: string, seatIds: string[], token: string) =>
    api<{ bookingGroupId: string; holdExpiresAt: string; totalAmount: number; currency: string }>("/api/bookings/hold", {
      method: "POST",
      token,
      body: asJson({ showtimeId, seatIds }),
    }),
  confirm: (bookingGroupId: string, token: string) =>
    api<Booking>("/api/bookings/confirm", {
      method: "POST",
      token,
      body: asJson({ bookingGroupId, paymentMethod: { token: `tok_good_${crypto.randomUUID().slice(0, 8)}` } }),
    }),
  list: (token: string, status = "") => api<{ bookings: Booking[] }>(`/api/bookings${status ? `?status=${status}` : ""}`, { token }),
  detail: (bookingId: string, token: string) => api<Booking>(`/api/bookings/${bookingId}`, { token }),
  cancel: (bookingId: string, token: string) => api<{ status: string }>(`/api/bookings/${bookingId}`, { method: "DELETE", token }),
  validate: (qrToken: string, token: string) =>
    api<{ result: string; movieTitle: string; hall: string; seats: string[]; userName: string }>("/api/validate", {
      method: "POST",
      token,
      body: asJson({ qrToken }),
    }),
};

export const userApi = {
  update: (userId: string, token: string, payload: Partial<User> & { currentPassword?: string; password?: string }) =>
    api<User>(`/api/users/${userId}`, { method: "PUT", token, body: asJson(payload) }),
  preferences: (userId: string, token: string, preferredGenres: string[]) =>
    api<User>(`/api/users/${userId}/preferences`, { method: "PUT", token, body: asJson({ preferredGenres }) }),
  paymentMethods: (userId: string, token: string) =>
    api<{ paymentMethods: PaymentMethod[] }>(`/api/users/${userId}/payment-methods`, { token }),
  addPaymentMethod: (userId: string, token: string, payload: Record<string, unknown>) =>
    api<PaymentMethod>(`/api/users/${userId}/payment-methods`, { method: "POST", token, body: asJson(payload) }),
  deletePaymentMethod: (userId: string, methodId: string, token: string) =>
    api<{ deleted: boolean }>(`/api/users/${userId}/payment-methods/${methodId}`, { method: "DELETE", token }),
};

export const adminApi = {
  users: (token: string) => api<{ users: User[] }>("/api/admin/users", { token }),
  createUser: (token: string, payload: Record<string, unknown>) =>
    api<User>("/api/admin/users", { method: "POST", token, body: asJson(payload) }),
  patchUser: (userId: string, token: string, payload: { role?: string; status?: string }) =>
    api<User>(`/api/admin/users/${userId}`, { method: "PATCH", token, body: asJson(payload) }),
  halls: (token: string) => api<{ halls: Hall[] }>("/api/admin/halls", { token }),
  createHall: (token: string, name: string) => api<Hall>("/api/admin/halls", { method: "POST", token, body: asJson({ name }) }),
  updateHall: (token: string, hallId: string, payload: { name: string }) =>
    api<Hall>(`/api/admin/halls/${hallId}`, { method: "PUT", token, body: asJson(payload) }),
  createSeatMap: (token: string, hallId: string, rows: Array<{ label: string; seatCount: number; type: string }>) =>
    api<{ totalSeats: number }>(`/api/admin/halls/${hallId}/seats`, { method: "POST", token, body: asJson({ rows }) }),
  createMovie: (token: string, payload: Record<string, unknown>) =>
    api<Movie>("/api/admin/movies", { method: "POST", token, body: asJson(payload) }),
  updateMovie: (token: string, movieId: string, payload: Record<string, unknown>) =>
    api<Movie>(`/api/admin/movies/${movieId}`, { method: "PUT", token, body: asJson(payload) }),
  deleteMovie: (token: string, movieId: string) =>
    api<{ deleted: boolean }>(`/api/admin/movies/${movieId}`, { method: "DELETE", token }),
  createShowtime: (token: string, payload: Record<string, unknown>) =>
    api<Showtime>("/api/admin/showtimes", { method: "POST", token, body: asJson(payload) }),
  updateShowtime: (token: string, showtimeId: string, payload: Record<string, unknown>) =>
    api<Showtime>(`/api/admin/showtimes/${showtimeId}`, { method: "PUT", token, body: asJson(payload) }),
  deleteShowtime: (token: string, showtimeId: string) =>
    api<{ deleted: boolean }>(`/api/admin/showtimes/${showtimeId}`, { method: "DELETE", token }),
};
