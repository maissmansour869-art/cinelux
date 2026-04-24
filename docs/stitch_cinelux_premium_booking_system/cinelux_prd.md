# CineLux Product Requirements Document (PRD)

## Project Overview
CineLux is a premium cinema booking system designed as a role-based platform for Customers, Gate Staff, and Administrators. It emphasizes a cinematic, immersive experience over generic SaaS aesthetics.

## Design Direction
- **Visual Language:** Dark, elegant, "Cinematic Noir".
- **Color Palette:** Charcoal, deep navy, warm amber/gold, restrained red accents.
- **Tone:** Premium, immersive, poster-led, high-contrast.
- **Key Elements:** Glassy cards, layered depth, rich imagery, clear typography.

## Core User Roles
1. **Customer:** Browse movies, book seats, manage profile, view history.
2. **Gate Staff:** Validate QR tickets (sub-role of Admin).
3. **Administrator:** Manage catalogue, showtimes, halls, users, and permissions.

## Key Flows & Surfaces
1. **Public Catalogue:** Hero, search, filters (genre/date), trending, recommendations.
2. **Movie Detail:** Rich metadata, showtimes, booking CTA.
3. **Seat Selection:** Interactive map, seat states (held, booked, accessible, etc.), hold timer.
4. **Checkout:** Payment methods, summary, success/error states.
5. **Ticketing:** QR confirmation, group summary, status.
6. **User Account:** History (upcoming/past), profile, preferences.
7. **Staff Validation:** Scanning interface, clear validation feedback (VALID, INVALID, etc.).
8. **Admin Dashboard:** Overview and CRUD management for all entities.

## Technical & Product Constraints
- Django backend, API-driven.
- Form-based and synchronous (no websockets).
- Responsive (Mobile, Tablet, Desktop).
- High accessibility standards.
- Clear cancellation and expiry logic.