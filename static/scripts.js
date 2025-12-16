// Global variables
let selectedSeats = [];
let showId = null;
let pricePerSeat = 0;
let lockTimer = null;
let lockExpiry = null;
let isLoading = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const seatGrid = document.getElementById('seatGrid');
    const movieFilterForm = document.getElementById('movieFilterForm');

    if (seatGrid) {
        initializeSeatSelection();
    }

    if (movieFilterForm) {
        initializeMovieFilters();
    }
});

// Initialize AJAX-based movie filters
function initializeMovieFilters() {
    const form = document.getElementById('movieFilterForm');
    const genreSelect = document.getElementById('genre');
    const languageSelect = document.getElementById('language');
    const clearBtn = document.getElementById('clearFiltersBtn');
    const searchInput = document.getElementById('movieSearch');
    const clearSearchBtn = document.getElementById('clearSearch');
    let searchDebounce;

    // Populate selects from backend meta if empty
    loadMoviesMeta(genreSelect, languageSelect);

    if (genreSelect) {
        genreSelect.addEventListener('change', fetchFilteredMovies);
    }
    if (languageSelect) {
        languageSelect.addEventListener('change', fetchFilteredMovies);
    }
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            if (genreSelect) genreSelect.value = '';
            if (languageSelect) languageSelect.value = '';
            fetchFilteredMovies();
        });
    }
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const val = this.value.trim();
            if (clearSearchBtn) {
                clearSearchBtn.style.display = val ? 'flex' : 'none';
            }
            clearTimeout(searchDebounce);
            searchDebounce = setTimeout(fetchFilteredMovies, 250);
        });
    }
    if (clearSearchBtn && searchInput) {
        clearSearchBtn.addEventListener('click', function() {
            searchInput.value = '';
            this.style.display = 'none';
            fetchFilteredMovies();
        });
    }
}

async function loadMoviesMeta(genreSelect, languageSelect) {
    try {
        const base = (typeof window !== 'undefined' && window.BACKEND_BASE_URL) ? window.BACKEND_BASE_URL.replace(/\/+$/, '') : '';
        const url = (base ? `${base}` : '') + '/api/meta/';
        const res = await fetch(url, { method: 'GET' });
        const data = await res.json();
        if (data.success) {
            if (genreSelect && genreSelect.options.length <= 1 && Array.isArray(data.genres)) {
                // Preserve "All Genres"
                data.genres.forEach(([code, name]) => {
                    const opt = document.createElement('option');
                    opt.value = code;
                    opt.textContent = name;
                    genreSelect.appendChild(opt);
                });
            }
            if (languageSelect && languageSelect.options.length <= 1 && Array.isArray(data.languages)) {
                // Preserve "All Languages"
                data.languages.forEach(([code, name]) => {
                    const opt = document.createElement('option');
                    opt.value = code;
                    opt.textContent = name;
                    languageSelect.appendChild(opt);
                });
            }
        }
    } catch (e) {
        console.warn('Failed to load movies meta', e);
    }
}

async function fetchFilteredMovies() {
    const genreSelect = document.getElementById('genre');
    const languageSelect = document.getElementById('language');
    const searchInput = document.getElementById('movieSearch');
    const moviesGridContainer = document.getElementById('moviesGrid');

    if (!moviesGridContainer) return;

    // Show loading state
    const originalContent = moviesGridContainer.innerHTML;
    moviesGridContainer.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem;">
            <div class="loading-spinner" style="display: inline-block; width: 40px; height: 40px; border: 4px solid rgba(231, 76, 60, 0.3); border-top-color: #e74c3c; border-radius: 50%; animation: spin 1s linear infinite;"></div>
            <p style="margin-top: 1rem; font-size: 1.2rem; color: #7f8c8d;">Loading movies...</p>
        </div>
    `;

    const params = new URLSearchParams();
    if (genreSelect && genreSelect.value) {
        params.append('genre', genreSelect.value);
    }
    if (languageSelect && languageSelect.value) {
        params.append('language', languageSelect.value);
    }
    if (searchInput && searchInput.value.trim()) {
        params.append('q', searchInput.value.trim());
    }

    const base = (typeof window !== 'undefined' && window.BACKEND_BASE_URL) ? window.BACKEND_BASE_URL.replace(/\/+$/, '') : '';
    const url = (base ? `${base}` : '') + '/api/movies/' + (params.toString() ? `?${params.toString()}` : '');

    try {
        const response = await fetch(url, { method: 'GET' });
        const data = await response.json();

        if (data.success && typeof data.html === 'string') {
            // Replace only the inner HTML of the movies grid container
            moviesGridContainer.outerHTML = data.html;
        } else {
            // Show error message
            moviesGridContainer.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; background: #f8d7da; border-radius: 12px; color: #721c24;">
                    <h3>Error Loading Movies</h3>
                    <p>${data.error || 'Failed to load movies. Please try again.'}</p>
                    <button onclick="fetchFilteredMovies()" class="btn btn-primary" style="margin-top: 1rem;">Retry</button>
                </div>
            `;
            console.error('Failed to load movies:', data.error || 'Unknown error');
        }
    } catch (error) {
        // Show error message
        moviesGridContainer.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; background: #f8d7da; border-radius: 12px; color: #721c24;">
                <h3>Connection Error</h3>
                <p>Failed to connect to server. Please check your connection and try again.</p>
                <button onclick="fetchFilteredMovies()" class="btn btn-primary" style="margin-top: 1rem;">Retry</button>
            </div>
        `;
        console.error('Error fetching movies:', error);
    }
}

// Initialize seat selection functionality
function initializeSeatSelection() {
    const seatGrid = document.getElementById('seatGrid');
    showId = seatGrid.dataset.showId;
    
    const priceElement = document.getElementById('pricePerSeat');
    pricePerSeat = parseFloat(priceElement.textContent);
    
    // Add click listeners to all available seats
    const seats = document.querySelectorAll('.seat.available');
    seats.forEach(seat => {
        seat.addEventListener('click', function() {
            toggleSeat(this);
        });
    });
    
    // Lock seats button
    const lockSeatsBtn = document.getElementById('lockSeatsBtn');
    if (lockSeatsBtn) {
        lockSeatsBtn.addEventListener('click', lockSeats);
    }
    
    // Proceed to payment button
    const proceedPaymentBtn = document.getElementById('proceedPaymentBtn');
    if (proceedPaymentBtn) {
        proceedPaymentBtn.addEventListener('click', initiatePayment);
    }
}

// Toggle seat selection
function toggleSeat(seatElement) {
    const seatNumber = seatElement.dataset.seat;
    const seatStatus = seatElement.dataset.status;
    
    // Only allow selecting available seats
    if (seatStatus !== 'available') {
        return;
    }
    
    if (seatElement.classList.contains('selected')) {
        // Deselect
        seatElement.classList.remove('selected');
        selectedSeats = selectedSeats.filter(s => s !== seatNumber);
    } else {
        // Select
        seatElement.classList.add('selected');
        selectedSeats.push(seatNumber);
    }
    
    updateBookingSummary();
}

// Update booking summary
function updateBookingSummary() {
    const selectedSeatsText = document.getElementById('selectedSeatsText');
    const seatCount = document.getElementById('seatCount');
    const totalPrice = document.getElementById('totalPrice');
    const lockSeatsBtn = document.getElementById('lockSeatsBtn');
    
    if (selectedSeats.length === 0) {
        selectedSeatsText.textContent = 'None';
        seatCount.textContent = '0 seat(s) selected';
        totalPrice.textContent = '0';
        lockSeatsBtn.disabled = true;
    } else {
        selectedSeatsText.textContent = selectedSeats.join(', ');
        seatCount.textContent = `${selectedSeats.length} seat(s) selected`;
        const total = selectedSeats.length * pricePerSeat;
        totalPrice.textContent = total.toFixed(2);
        lockSeatsBtn.disabled = false;
    }
}

// Lock selected seats
async function lockSeats() {
    if (selectedSeats.length === 0) {
        showMessage('Please select at least one seat', 'warning');
        return;
    }
    
    const lockSeatsBtn = document.getElementById('lockSeatsBtn');
    const originalText = lockSeatsBtn.textContent;
    lockSeatsBtn.disabled = true;
    lockSeatsBtn.textContent = 'Locking...';
    lockSeatsBtn.classList.add('loading');
    
    try {
        const csrfToken = document.getElementById('csrfToken').value;
        
        const response = await fetch('/api/lock_seats/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                show_id: showId,
                seats: selectedSeats
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update UI to show locked seats
            selectedSeats.forEach(seatNumber => {
                const seatElement = document.querySelector(`[data-seat="${seatNumber}"]`);
                if (seatElement) {
                    seatElement.classList.remove('selected', 'available');
                    seatElement.classList.add('user_locked');
                    seatElement.dataset.status = 'user_locked';
                }
            });
            
            // Show timer
            lockExpiry = new Date(data.expires_at);
            startLockTimer();
            
            // Show proceed to payment button
            const proceedPaymentBtn = document.getElementById('proceedPaymentBtn');
            proceedPaymentBtn.style.display = 'inline-block';
            lockSeatsBtn.style.display = 'none';
            
            showMessage('Seats locked successfully! Complete payment within 5 minutes.', 'success');
        } else {
            showMessage('Error: ' + data.error, 'error');
            lockSeatsBtn.disabled = false;
            lockSeatsBtn.textContent = originalText;
            lockSeatsBtn.classList.remove('loading');
        }
    } catch (error) {
        console.error('Error locking seats:', error);
        showMessage('An error occurred while locking seats. Please try again.', 'error');
        lockSeatsBtn.disabled = false;
        lockSeatsBtn.textContent = originalText;
        lockSeatsBtn.classList.remove('loading');
    }
}

// Start countdown timer for seat lock
function startLockTimer() {
    const timerDisplay = document.getElementById('timerDisplay');
    const timerText = document.getElementById('timerText');
    
    timerDisplay.style.display = 'block';
    
    lockTimer = setInterval(() => {
        const now = new Date();
        const timeLeft = lockExpiry - now;
        
        if (timeLeft <= 0) {
            clearInterval(lockTimer);
            timerText.textContent = '0:00';
            alert('Your seat lock has expired. Please select seats again.');
            location.reload();
        } else {
            const minutes = Math.floor(timeLeft / 60000);
            const seconds = Math.floor((timeLeft % 60000) / 1000);
            timerText.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            // Warning when 1 minute left
            if (timeLeft <= 60000 && timerDisplay.style.backgroundColor !== 'rgb(220, 53, 69)') {
                timerDisplay.style.backgroundColor = '#dc3545';
                timerDisplay.style.color = 'white';
            }
        }
    }, 1000);
}

// Initiate payment process
async function initiatePayment() {
    const proceedPaymentBtn = document.getElementById('proceedPaymentBtn');
    const originalText = proceedPaymentBtn.textContent;
    proceedPaymentBtn.disabled = true;
    proceedPaymentBtn.textContent = 'Processing...';
    proceedPaymentBtn.classList.add('loading');
    
    const modal = document.getElementById('paymentModal');
    const paymentMessage = document.getElementById('paymentMessage');
    paymentMessage.textContent = 'Initializing payment...';
    modal.style.display = 'flex';
    
    try {
        const csrfToken = document.getElementById('csrfToken').value;
        
        // Create Razorpay order
        const response = await fetch('/api/create_order/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                show_id: showId,
                seats: selectedSeats
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Initialize Razorpay payment
            openRazorpay(data);
        } else {
            modal.style.display = 'none';
            showMessage('Error: ' + data.error, 'error');
            proceedPaymentBtn.disabled = false;
            proceedPaymentBtn.textContent = originalText;
            proceedPaymentBtn.classList.remove('loading');
        }
    } catch (error) {
        console.error('Error creating order:', error);
        modal.style.display = 'none';
        showMessage('An error occurred while initializing payment. Please try again.', 'error');
        proceedPaymentBtn.disabled = false;
        proceedPaymentBtn.textContent = originalText;
        proceedPaymentBtn.classList.remove('loading');
    }
}

// Open Razorpay payment gateway
function openRazorpay(orderData) {
    const razorpayKey = document.getElementById('razorpayKey').value;
    
    const options = {
        key: razorpayKey,
        amount: orderData.amount * 100, // Amount in paise
        currency: orderData.currency,
        name: 'BookMyShow',
        description: 'Movie Ticket Booking',
        order_id: orderData.order_id,
        handler: function(response) {
            // Payment successful
            handlePaymentSuccess(response);
        },
        prefill: {
            name: '',
            email: '',
            contact: ''
        },
        theme: {
            color: '#e74c3c'
        },
        modal: {
            ondismiss: function() {
                // Payment cancelled
                const modal = document.getElementById('paymentModal');
                modal.style.display = 'none';
                const proceedPaymentBtn = document.getElementById('proceedPaymentBtn');
                proceedPaymentBtn.disabled = false;
                proceedPaymentBtn.textContent = 'Proceed to Payment';
                alert('Payment cancelled. Your seats are still locked.');
            }
        }
    };
    
    const modal = document.getElementById('paymentModal');
    modal.style.display = 'none';
    
    const rzp = new Razorpay(options);
    rzp.open();
}

// Handle successful payment
async function handlePaymentSuccess(paymentResponse) {
    const modal = document.getElementById('paymentModal');
    const paymentMessage = document.getElementById('paymentMessage');
    
    modal.style.display = 'flex';
    paymentMessage.textContent = 'Confirming your booking...';
    
    try {
        const csrfToken = document.getElementById('csrfToken').value;
        
        // Confirm booking
        const response = await fetch('/api/confirm_booking/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                show_id: showId,
                seats: selectedSeats,
                payment_id: paymentResponse.razorpay_payment_id
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Clear timer
            if (lockTimer) {
                clearInterval(lockTimer);
            }
            
            // Show success message
            paymentMessage.textContent = 'Booking confirmed! Redirecting...';
            showMessage('Booking confirmed successfully!', 'success');
            
            setTimeout(() => {
                window.location.href = '/bookings/';
            }, 2000);
        } else {
            modal.style.display = 'none';
            showMessage('Error confirming booking: ' + data.error, 'error');
            setTimeout(() => {
                location.reload();
            }, 3000);
        }
    } catch (error) {
        console.error('Error confirming booking:', error);
        modal.style.display = 'none';
        showMessage('An error occurred while confirming booking. Please contact support.', 'error');
    }
}

// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show message function
function showMessage(text, type = 'info') {
    // Remove existing messages of the same type
    const existingMessages = document.querySelectorAll(`.message-${type}`);
    existingMessages.forEach(msg => msg.remove());
    
    // Create message element
    const messageContainer = document.querySelector('.messages-container') || 
        (() => {
            const container = document.createElement('div');
            container.className = 'messages-container';
            document.querySelector('.main-content').prepend(container);
            return container;
        })();
    
    const message = document.createElement('div');
    message.className = `message message-${type}`;
    message.innerHTML = `
        <span>${text}</span>
        <button class="close-btn" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    messageContainer.appendChild(message);
    
    // Auto-hide after 5 seconds for non-error messages
    if (type !== 'error') {
        setTimeout(() => {
            if (message.parentNode) {
                message.style.opacity = '0';
                message.style.transition = 'opacity 0.5s';
                setTimeout(() => {
                    if (message.parentNode) {
                        message.remove();
                    }
                }, 500);
            }
        }, 5000);
    }
}

// Auto-hide messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const messages = document.querySelectorAll('.message');
    messages.forEach(message => {
        // Don't auto-hide error messages
        if (!message.classList.contains('message-error')) {
            setTimeout(() => {
                message.style.opacity = '0';
                message.style.transition = 'opacity 0.5s';
                setTimeout(() => {
                    message.remove();
                }, 500);
            }, 5000);
        }
    });
});
