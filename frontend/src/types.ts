export type Role = "USER" | "ADMIN" | "STAFF";

export type Movie = {
  movieId: string;
  title: string;
  description: string;
  durationMinutes: number;
  releaseDate?: string | null;
  language?: string;
  ageRating?: string;
  posterUrl?: string;
  rating: number;
  genres: string[];
  relevanceScore?: number | null;
  reason?: string;
};

export type Showtime = {
  showtimeId: string;
  movieId: string;
  hallId: string;
  hallName: string;
  startTime: string;
  endTime: string;
  totalSeats: number;
  availableSeats: number | null;
  price: number;
  currency: string;
};

export type Seat = {
  seatId: string;
  row: string;
  number: number;
  type: "STANDARD" | "PREMIUM" | "ACCESSIBLE";
  status: "AVAILABLE" | "HELD" | "BOOKED";
};

export type User = {
  userId: string;
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  role: Role;
  status: "ACTIVE" | "SUSPENDED";
  preferredGenres: string[];
};

export type Booking = {
  bookingId?: string;
  bookingGroupId: string;
  userId?: string;
  movieTitle: string;
  showtimeId?: string;
  startTime?: string;
  seat?: string;
  seats?: string[];
  status: string;
  totalAmount?: number;
  currency?: string;
  paymentToken?: string | null;
  qrCodeToken?: string | null;
  qrCodeUrl?: string | null;
  confirmedAt?: string | null;
  createdAt?: string | null;
  cancelledAt?: string | null;
};

export type Hall = {
  hallId: string;
  name: string;
  totalSeats: number;
};

export type PaymentMethod = {
  methodId: string;
  brand: string;
  last4: string;
  expMonth?: number;
  expYear?: number;
  isDefault: boolean;
};
