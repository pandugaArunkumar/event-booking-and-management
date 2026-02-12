/* =========================
   GLOBAL CONFIRMATIONS
========================= */

// Confirm logout
function confirmLogout() {
    return confirm("Are you sure you want to logout?");
}

// Confirm delete (Admin)
function confirmDelete(btn) {
    if (!confirm("Are you sure you want to delete this?")) {
        return false;
    }

    // Disable delete button after confirm
    if (btn) {
        btn.innerText = "Deleting...";
        btn.classList.add("disabled");
        btn.style.pointerEvents = "none";
    }
    return true;
}

/* =========================
   EVENT SEARCH FILTER
========================= */

function filterEvents(value) {
    value = value.toLowerCase();
    const cards = document.querySelectorAll(".event-card");

    cards.forEach(card => {
        const title = card.querySelector("h3").innerText.toLowerCase();
        card.style.display = title.includes(value) ? "block" : "none";
    });
}

/* =========================
   BOOKING CONFIRMATION
========================= */

document.addEventListener("DOMContentLoaded", () => {

    // Booking buttons
    document.querySelectorAll(".book-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            const eventId = this.dataset.eventId;
            if (!eventId) return;

            if (confirm("🎟️ Do you want to book this event?")) {
                this.disabled = true;
                this.innerText = "Booking...";
                this.classList.add("disabled");

                window.location.href = `/book/${eventId}`;
            }
        });
    });

    // Admin delete buttons
    document.querySelectorAll(".btn.delete").forEach(btn => {
        btn.addEventListener("click", function (e) {
            if (!confirmDelete(this)) {
                e.preventDefault();
            }
        });
    });

});

/* =========================
   FORM VALIDATION
========================= */

// Login validation
function validateLogin() {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!email || !password) {
        alert("Please fill all fields");
        return false;
    }
    return true;
}

// Register validation
function validateRegister() {
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!name || !email || !password) {
        alert("All fields are required");
        return false;
    }

    if (password.length < 6) {
        alert("Password must be at least 6 characters");
        return false;
    }

    return true;
}

// Admin event form validation
function validateEvent() {
    const title = document.getElementById("title").value.trim();
    const date = document.getElementById("event_date").value;
    const location = document.getElementById("location").value.trim();
    const price = document.getElementById("price").value;
    const seats = document.getElementById("seats").value;

    if (!title || !date || !location || !price || !seats) {
        alert("Please fill all event details");
        return false;
    }

    if (price < 0 || seats <= 0) {
        alert("Price and seats must be valid numbers");
        return false;
    }

    return true;
}

/* =========================
   AUTO HIDE FLASH ALERTS
========================= */

setTimeout(() => {
    document.querySelectorAll(".alert").forEach(alert => {
        alert.style.display = "none";
    });
}, 3000);
