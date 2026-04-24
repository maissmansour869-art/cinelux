const state = {
    movies: [],
    recommendations: [],
    allGenres: [],
    selectedMovieId: null,
    showtimeCache: new Map(),
    session: JSON.parse(localStorage.getItem("cineluxSession") || "null"),
};

const els = {
    navLinks: document.querySelectorAll("[data-nav]"),
    views: {
        catalogue: document.getElementById("catalogueView"),
        auth: document.getElementById("authView"),
    },
    movieGrid: document.getElementById("movieGrid"),
    detailPanel: document.getElementById("detailPanel"),
    movieCount: document.getElementById("movieCount"),
    genreCount: document.getElementById("genreCount"),
    showtimeCount: document.getElementById("showtimeCount"),
    searchInput: document.getElementById("searchInput"),
    genreSelect: document.getElementById("genreSelect"),
    dateInput: document.getElementById("dateInput"),
    filterForm: document.getElementById("filterForm"),
    recommendationsPanel: document.getElementById("recommendationsPanel"),
    recommendationsGrid: document.getElementById("recommendationsGrid"),
    recommendationsStatus: document.getElementById("recommendationsStatus"),
    cardTemplate: document.getElementById("movieCardTemplate"),
    sessionChip: document.getElementById("sessionChip"),
    sessionText: document.getElementById("sessionText"),
    logoutButton: document.getElementById("logoutButton"),
    authTabs: document.querySelectorAll("[data-auth-tab]"),
    authForms: document.querySelectorAll("[data-auth-form]"),
    loginForm: document.getElementById("loginForm"),
    signupForm: document.getElementById("signupForm"),
    signupGenres: document.getElementById("signupGenres"),
    formMessage: document.getElementById("formMessage"),
};

function routeTo(viewName) {
    const name = viewName === "auth" ? "auth" : "catalogue";
    Object.entries(els.views).forEach(([key, view]) => view.classList.toggle("active", key === name));
    els.navLinks.forEach((link) => link.classList.toggle("active", link.dataset.nav === name));
}

function setMessage(message, type = "") {
    els.formMessage.textContent = message;
    els.formMessage.className = `form-message ${type}`.trim();
}

function setLoading(button, loadingText) {
    const original = button.textContent;
    button.textContent = loadingText;
    button.disabled = true;
    return () => {
        button.textContent = original;
        button.disabled = false;
    };
}

async function api(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    if (state.session?.token) {
        headers.Authorization = `Bearer ${state.session.token}`;
    }
    const response = await fetch(path, { ...options, headers });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.message || data.detail || "Something went wrong.");
    }
    return data;
}

function updateSession(session) {
    state.session = session;
    if (session) {
        localStorage.setItem("cineluxSession", JSON.stringify(session));
        els.sessionChip.classList.add("signed-in");
        els.sessionText.textContent = `Signed in`;
        els.logoutButton.classList.remove("hidden");
        loadRecommendations();
    } else {
        localStorage.removeItem("cineluxSession");
        els.sessionChip.classList.remove("signed-in");
        els.sessionText.textContent = "Guest mode";
        els.logoutButton.classList.add("hidden");
        state.recommendations = [];
        renderRecommendationsGuest();
    }
}

function formatRuntime(minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours ? `${hours}h ${mins}m` : `${mins}m`;
}

function formatDate(value) {
    if (!value) return "TBA";
    return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
}

function formatShowtime(value) {
    return new Intl.DateTimeFormat(undefined, {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
    }).format(new Date(value));
}

function getPosterUrl(movie) {
    if (!movie.posterUrl) return "";
    return movie.posterUrl.replace("http://localhost:8000", window.location.origin);
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }[char]));
}

function populateGenres() {
    const genres = [...new Set(state.movies.flatMap((movie) => movie.genres || []))].sort();
    state.allGenres = genres;
    els.genreCount.textContent = genres.length;

    const selected = els.genreSelect.value;
    els.genreSelect.innerHTML = '<option value="">All genres</option>';
    genres.forEach((genre) => {
        const option = document.createElement("option");
        option.value = genre;
        option.textContent = genre;
        els.genreSelect.append(option);
    });
    els.genreSelect.value = genres.includes(selected) ? selected : "";

    els.signupGenres.innerHTML = "";
    genres.forEach((genre) => {
        const label = document.createElement("label");
        label.className = "genre-choice";
        label.innerHTML = `<input type="checkbox" name="preferredGenres" value="${genre}"><span>${genre}</span>`;
        els.signupGenres.append(label);
    });
}

function renderMovies() {
    els.movieGrid.innerHTML = "";
    els.movieCount.textContent = state.movies.length;

    if (!state.movies.length) {
        els.movieGrid.innerHTML = '<div class="error-state">No movies match those filters.</div>';
        return;
    }

    state.movies.forEach((movie) => {
        const node = els.cardTemplate.content.firstElementChild.cloneNode(true);
        const button = node.querySelector(".poster-button");
        const img = node.querySelector(".poster");
        const title = node.querySelector("h2");
        const description = node.querySelector("p");
        const rating = node.querySelector(".rating-pill");
        const meta = node.querySelector(".movie-meta");

        img.src = getPosterUrl(movie);
        img.alt = `${movie.title} poster`;
        title.textContent = movie.title;
        description.textContent = movie.description;
        rating.textContent = `${Number(movie.rating || 0).toFixed(1)} rating`;
        meta.innerHTML = [
            movie.ageRating || "NR",
            formatRuntime(movie.durationMinutes),
            ...(movie.genres || []).slice(0, 2),
        ].map((item) => `<span>${item}</span>`).join("");
        button.addEventListener("click", () => selectMovie(movie.movieId));
        els.movieGrid.append(node);
    });
}

async function loadMovies() {
    els.movieGrid.innerHTML = '<div class="loading">Loading the catalogue...</div>';
    const params = new URLSearchParams({ page: "1", limit: "100" });
    if (els.searchInput.value.trim()) params.set("q", els.searchInput.value.trim());
    if (els.genreSelect.value) params.set("genre", els.genreSelect.value);
    if (els.dateInput.value) params.set("date", els.dateInput.value);

    try {
        const data = await api(`/api/movies?${params.toString()}`);
        state.movies = data.movies || [];
        populateGenres();
        renderMovies();
        if (!state.selectedMovieId && state.movies[0]) {
            await selectMovie(state.movies[0].movieId);
        } else if (state.selectedMovieId) {
            const stillVisible = state.movies.some((movie) => movie.movieId === state.selectedMovieId);
            if (stillVisible) await selectMovie(state.selectedMovieId);
        }
    } catch (error) {
        els.movieGrid.innerHTML = `<div class="error-state">${error.message}</div>`;
    }
}

async function selectMovie(movieId) {
    const movie = state.movies.find((item) => item.movieId === movieId)
        || state.recommendations.find((item) => item.movieId === movieId);
    if (!movie) return;
    state.selectedMovieId = movieId;
    els.detailPanel.innerHTML = `
        <img class="detail-poster" src="${getPosterUrl(movie)}" alt="${movie.title} poster">
        <div class="detail-body">
            <p class="eyebrow">Movie details</p>
            <h2>${movie.title}</h2>
            <p>${movie.description}</p>
            <div class="detail-stats">
                <span><strong>${Number(movie.rating || 0).toFixed(1)}</strong>Rating</span>
                <span><strong>${formatRuntime(movie.durationMinutes)}</strong>Runtime</span>
                <span><strong>${movie.ageRating || "NR"}</strong>Rated</span>
            </div>
            <div class="genre-tags">${(movie.genres || []).map((genre) => `<span>${genre}</span>`).join("")}</div>
            <section class="showtime-section">
                <h3>Showtimes</h3>
                <div class="showtime-list" id="showtimeList"><span>Loading sessions...</span></div>
            </section>
        </div>
    `;
    await loadShowtimes(movieId);
}

async function loadShowtimes(movieId) {
    const showtimeList = document.getElementById("showtimeList");
    const cacheKey = `${movieId}:${els.dateInput.value || "all"}`;
    try {
        if (!state.showtimeCache.has(cacheKey)) {
            const params = new URLSearchParams();
            if (els.dateInput.value) params.set("date", els.dateInput.value);
            const suffix = params.toString() ? `?${params.toString()}` : "";
            state.showtimeCache.set(cacheKey, await api(`/api/movies/${movieId}/showtimes${suffix}`));
        }
        const showtimes = state.showtimeCache.get(cacheKey).showtimes || [];
        els.showtimeCount.textContent = showtimes.length;
        if (!showtimes.length) {
            showtimeList.innerHTML = "<span>No upcoming showtimes for this filter.</span>";
            return;
        }
        showtimeList.innerHTML = showtimes.slice(0, 6).map((showtime) => `
            <span>
                <b>${formatShowtime(showtime.startTime)}</b>
                <em>${showtime.hallName} - ${showtime.availableSeats ?? showtime.totalSeats} seats - $${Number(showtime.price).toFixed(2)}</em>
            </span>
        `).join("");
    } catch (error) {
        showtimeList.innerHTML = `<span>${error.message}</span>`;
    }
}

function renderRecommendationsGuest() {
    els.recommendationsPanel.classList.add("guest");
    els.recommendationsStatus.textContent = "Sign in for personal picks";
    els.recommendationsGrid.innerHTML = `
        <div class="recommendations-empty">
            <span>Recommendations use your saved genre preferences and recent activity.</span>
            <button class="ghost-button small" type="button" id="recommendationSignIn">Sign in</button>
        </div>
    `;
    document.getElementById("recommendationSignIn").addEventListener("click", () => {
        routeTo("auth");
        history.replaceState(null, "", "#auth");
    });
}

function renderRecommendations() {
    els.recommendationsPanel.classList.remove("guest");
    if (!state.recommendations.length) {
        els.recommendationsStatus.textContent = "No picks yet";
        els.recommendationsGrid.innerHTML = `
            <div class="recommendations-empty">
                <span>No personalized picks are available yet. Add preferences on signup or browse the catalogue.</span>
            </div>
        `;
        return;
    }

    els.recommendationsStatus.textContent = `${state.recommendations.length} picks ready`;
    els.recommendationsGrid.innerHTML = state.recommendations.slice(0, 6).map((movie) => `
        <button class="recommendation-card" type="button" data-recommendation-id="${movie.movieId}">
            <img src="${getPosterUrl(movie)}" alt="${escapeHtml(movie.title)} poster">
            <span>
                <h3>${escapeHtml(movie.title)}</h3>
                <p>${escapeHtml(movie.reason || movie.description)}</p>
                <span class="recommendation-meta">
                    <span>${Number(movie.rating || 0).toFixed(1)} rating</span>
                    <span>${movie.relevanceScore ? `${Math.round(movie.relevanceScore * 100)}% match` : "Popular"}</span>
                </span>
            </span>
        </button>
    `).join("");
    els.recommendationsGrid.querySelectorAll("[data-recommendation-id]").forEach((card) => {
        card.addEventListener("click", () => selectMovie(card.dataset.recommendationId));
    });
}

async function loadRecommendations() {
    if (!state.session?.token || !state.session?.userId) {
        renderRecommendationsGuest();
        return;
    }
    els.recommendationsStatus.textContent = "Finding picks...";
    els.recommendationsGrid.innerHTML = '<div class="recommendations-empty"><span>Loading recommendations...</span></div>';
    try {
        const data = await api(`/api/recommendations/${state.session.userId}?limit=6`);
        state.recommendations = data.recommendations || [];
        renderRecommendations();
    } catch (error) {
        if (/missing|invalid|token|credentials|auth/i.test(error.message)) {
            updateSession(null);
            return;
        }
        els.recommendationsStatus.textContent = "Unavailable";
        els.recommendationsGrid.innerHTML = `<div class="recommendations-empty"><span>${escapeHtml(error.message)}</span></div>`;
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const reset = setLoading(event.submitter, "Signing in...");
    setMessage("");
    try {
        const payload = Object.fromEntries(new FormData(els.loginForm));
        const data = await api("/api/users/login", { method: "POST", body: JSON.stringify(payload) });
        updateSession(data);
        setMessage("Signed in successfully.", "success");
        routeTo("catalogue");
    } catch (error) {
        setMessage(error.message, "error");
    } finally {
        reset();
    }
}

async function handleSignup(event) {
    event.preventDefault();
    const reset = setLoading(event.submitter, "Creating...");
    setMessage("");
    try {
        const formData = new FormData(els.signupForm);
        const payload = Object.fromEntries(formData);
        payload.preferredGenres = formData.getAll("preferredGenres");
        await api("/api/users/register", { method: "POST", body: JSON.stringify(payload) });
        const data = await api("/api/users/login", {
            method: "POST",
            body: JSON.stringify({ email: payload.email, password: payload.password }),
        });
        updateSession(data);
        setMessage("Account created and signed in.", "success");
        els.signupForm.reset();
        routeTo("catalogue");
    } catch (error) {
        setMessage(error.message, "error");
    } finally {
        reset();
    }
}

function bindEvents() {
    els.navLinks.forEach((link) => {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            routeTo(link.dataset.nav);
            history.replaceState(null, "", `#${link.dataset.nav}`);
        });
    });

    els.filterForm.addEventListener("submit", (event) => {
        event.preventDefault();
        state.showtimeCache.clear();
        state.selectedMovieId = null;
        loadMovies();
    });
    els.searchInput.addEventListener("input", () => {
        clearTimeout(window.__cineluxSearchTimer);
        window.__cineluxSearchTimer = setTimeout(() => {
            state.selectedMovieId = null;
            loadMovies();
        }, 260);
    });
    els.genreSelect.addEventListener("change", loadMovies);
    els.dateInput.addEventListener("change", () => {
        state.showtimeCache.clear();
        loadMovies();
    });

    els.authTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const active = tab.dataset.authTab;
            els.authTabs.forEach((item) => {
                item.classList.toggle("active", item === tab);
                item.setAttribute("aria-selected", item === tab ? "true" : "false");
            });
            els.authForms.forEach((form) => form.classList.toggle("active", form.dataset.authForm === active));
            setMessage("");
        });
    });

    els.loginForm.addEventListener("submit", handleLogin);
    els.signupForm.addEventListener("submit", handleSignup);
    els.logoutButton.addEventListener("click", () => {
        updateSession(null);
        setMessage("Signed out.", "success");
    });
    window.addEventListener("hashchange", () => routeTo(location.hash.replace("#", "")));
}

bindEvents();
updateSession(state.session);
routeTo(location.hash.replace("#", ""));
loadMovies();
