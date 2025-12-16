# BookMyShow Clone - Movie Ticket Booking System

A complete, production-ready movie ticket booking system built with Django, featuring real-time seat locking, payment integration, and admin analytics.

## 🎯 Features

### Core Functionality
- **Movie Browsing**: Browse movies with filters by genre and language
- **Show Listings**: View upcoming shows with cinema, date, and time details
- **Seat Selection**: Interactive seat map with real-time availability
- **Seat Locking**: Temporary 5-minute seat reservation system
- **Payment Integration**: Razorpay payment gateway integration
- **Booking Confirmation**: Email notifications after successful booking
- **User Dashboard**: View booking history
- **Admin Analytics**: Revenue tracking, popular movies, busiest cinemas
- **Movie Promotion**: Organizers can promote movies for better visibility

### Technical Features
- Atomic transactions for booking operations
- AJAX-based seat selection without page reloads
- Countdown timer for seat lock expiry
- Automatic release of expired seat locks
- Responsive design for mobile and desktop
- RESTful API endpoints for booking operations

## 📁 Project Structure

```
bms_project/
├── bms_project/           # Django project settings
│   ├── __init__.py
│   ├── settings.py        # Configuration
│   ├── urls.py            # Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
├── core/                  # Main application
│   ├── management/
│   │   └── commands/
│   │       └── populate_data.py  # Sample data generator
│   ├── __init__.py
│   ├── admin.py           # Admin interface config
│   ├── apps.py
│   ├── models.py          # Database models
│   ├── urls.py            # App URL patterns
│   ├── views.py           # View functions
│   └── tests.py
├── templates/             # HTML templates
│   └── core/
│       ├── base.html
│       ├── movies.html
│       ├── movie_detail.html
│       ├── show.html
│       ├── login.html
│       ├── register.html
│       ├── profile.html
│       └── admin_dashboard.html
├── static/                # Static files
│   ├── styles.css         # All CSS styling
│   └── scripts.js         # JavaScript functionality
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

## 🗄️ Database Models

### Cinema
- name, city, address

### Screen
- cinema (FK), name, total_seats

### Seat
- screen (FK), number (e.g., A1, B1), seat_type (Normal/Premium)

### Movie
- title, description, duration_mins, language, genre, poster_url, trailer_url

### Show
- movie (FK), screen (FK), date, start_time, price

### Booking
- user (FK), show (FK), seats (JSON), total_amount, status, booking_id (UUID)

### SeatLock
- show (FK), seat_number, user (FK), locked_at, expires_at
- Unique constraint: (show, seat_number)

## 🚀 How to Run (Development)

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Step 1: Clone the Repository
```bash
cd C:\Users\devil\bms_project
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Settings

Edit `bms_project/settings.py`:

**Email Configuration (for booking confirmations):**
```python
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Use Gmail App Password
```

**Razorpay Configuration (for payments):**
```python
RAZORPAY_KEY_ID = 'your_razorpay_key_id'
RAZORPAY_KEY_SECRET = 'your_razorpay_key_secret'
```

> **Note:** For testing, you can use Razorpay test credentials or leave the default values.

### Step 5: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Populate Sample Data
```bash
python manage.py populate_data
```

This command creates:
- 2 cinemas (PVR Cinemas in Mumbai, INOX in Delhi)
- 3 screens with seats
- 5 movies with trailers
- Shows for the next 7 days
- Admin user: `admin` / `admin123`
- Test user: `testuser` / `testpass123`

### Step 7: Create Superuser (Optional)
If you want a custom admin account:
```bash
python manage.py createsuperuser
```

### Step 8: Run Development Server
```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/`

### Step 9: Access Admin Panel
Visit: `http://127.0.0.1:8000/admin/`
- Username: `admin`
- Password: `admin123`

## 🔑 Default Login Credentials

### Login Types & Default Credentials

| Role | Purpose | Username / Password | Where to log in | Notes |
|------|---------|---------------------|-----------------|-------|
| Customer (default) | Browse movies, book tickets, manage bookings | `testuser` / `testpass123` | `/login/` | Any new signup also becomes a customer by default. |
| Organizer / Venue | Publish shows, view schedule snapshots | `organizer` / `organizer123` | `/organizer/login/` → `/organizer/dashboard/` | Role is set via `UserProfile.role = ORGANIZER`. |
| Staff / Gate Scanner | Validate tickets at entry | `staff` / `staff123` | `/staff/login/` → `/staff/scan/` | Interface exposes booking lookup + validation status. |
| Platform Admin | Manage data + analytics | `admin` / `admin123` | `/admin/` (Django admin) and `/admin/dashboard/` | Requires `is_staff=True`. UI nav hides this link; hit URL directly. |

> Need more roles? Create/assign users in `/admin/` and update `UserProfile.role`.

### Self-Registration & Role Approval

- New users can choose their account type during registration.
- Organizer and staff selections trigger an admin approval workflow. Until approved in `/admin/`, those users behave like regular customers and see a pending-approval notice on login.

## 🧪 Tests

Role-specific login flows are covered via Django tests:

```bash
py manage.py test core  # or python manage.py test core if your venv is active
```

The suite seeds organizer/staff/customer users, confirms the dedicated portals accept the correct roles, and verifies cross-role logins are blocked with the “restricted portal” error.

## 📱 Usage Guide

### For Regular Users

1. **Browse Movies**
   - Visit homepage to see all movies
   - Use filters to find movies by genre or language

2. **Select a Show**
   - Click on a movie to see details and trailer
   - Choose a show time and cinema

3. **Book Tickets**
   - Login or register
   - Select seats from the interactive seat map
   - Click "Lock Seats" to reserve for 5 minutes
   - Complete payment via Razorpay
   - Receive booking confirmation via email

4. **View Bookings**
   - Click "My Bookings" to see booking history

### For Administrators

1. **Access Admin Dashboard**
   - Login with admin credentials
   - Click "Dashboard" in navigation

2. **View Analytics**
   - Total revenue
   - Total bookings
   - Popular movies
   - Busiest cinemas
   - Recent bookings

3. **Manage Data**
   - Go to `/admin/` to manage all database records

## 🧵 Email Notifications

### Configuration
- SMTP backend (Gmail)
- Configurable in settings.py
- Sends on successful booking
- Daily reminder emails for upcoming shows

### Email Content
- Booking confirmation with QR code
- Booking ID
- Movie details
- Show time and date
- Seat numbers
- Total amount
- Reminder emails for shows happening tomorrow

### Setup
Email configuration is loaded from environment variables in the `.env` file:

```bash
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password  # Use Gmail App Password
```

For Gmail, you need to:
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the App Password instead of your regular password

### Testing Emails
You can test email functionality with the management commands:

```bash
# Test basic email
python manage.py test_email your-email@example.com

# Test booking confirmation email
python manage.py test_booking_email your-email@example.com
```

## 🌐 API Endpoints

### Public Endpoints
- `GET /` - Home page (movie list)
- `GET /movies/<id>/` - Movie detail
- `GET /login/` - Login page
- `GET /register/` - Registration page

### Protected Endpoints (Require Login)
- `GET /shows/<id>/` - Show page with seat map
- `POST /api/lock_seats/` - Lock selected seats
- `POST /api/create_order/` - Create payment order
- `POST /api/confirm_booking/` - Confirm booking after payment
- `GET /profile/` - User bookings
- `GET /admin/dashboard/` - Analytics dashboard (staff only)

## 🎨 Color Scheme

### Seat States
- **Green (`#2ecc71`)**: Available seats
- **Blue (`#3498db`)**: Selected/Locked by user
- **Yellow (`#f39c12`)**: Locked by others
- **Red (`#e74c3c`)**: Booked seats

### UI Colors
- Primary: `#e74c3c` (Red)
- Success: `#27ae60` (Green)
- Background: `#f5f5f5` (Light Gray)
- Text: `#333` (Dark Gray)

## 🔧 Configuration Options

### Seat Lock Duration
In `settings.py`:
```python
SEAT_LOCK_DURATION = 5  # minutes
```

### Database
SQLite by default. For production, switch to PostgreSQL:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bookmyshow_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🚀 Deployment Guide

### Deployment on PythonAnywhere

1. **Create Account**
   - Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Upload Code**
   ```bash
   # In PythonAnywhere Bash console
   git clone <your-repo-url>
   cd bms_project
   ```

3. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure Web App**
   - Go to Web tab
   - Add new web app
   - Select manual configuration (Python 3.x)
   - Set source code: `/home/yourusername/bms_project`
   - Set virtualenv: `/home/yourusername/bms_project/venv`

5. **Configure WSGI**
   Edit WSGI configuration file:
   ```python
   import sys
   import os
   
   path = '/home/yourusername/bms_project'
   if path not in sys.path:
       sys.path.append(path)
   
   os.environ['DJANGO_SETTINGS_MODULE'] = 'bms_project.settings'
   
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

6. **Update Settings**
   In `settings.py`:
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['yourusername.pythonanywhere.com']
   
   # Static files
   STATIC_ROOT = '/home/yourusername/bms_project/staticfiles'
   ```

7. **Collect Static Files**
   ```bash
   python manage.py collectstatic
   ```

8. **Set Static Files Mapping**
   In Web tab:
   - URL: `/static/`
   - Directory: `/home/yourusername/bms_project/staticfiles`

9. **Run Migrations**
   ```bash
   python manage.py migrate
   python manage.py populate_data
   ```

10. **Reload Web App**

### Deployment on Heroku

1. **Install Heroku CLI**
   ```bash
   # Download from heroku.com/cli
   ```

2. **Prepare for Heroku**
   
   Create `Procfile`:
   ```
   web: gunicorn bms_project.wsgi
   ```
   
   Add to `requirements.txt`:
   ```
   gunicorn==21.2.0
   psycopg2-binary==2.9.9
   whitenoise==6.6.0
   ```
   
   Update `settings.py`:
   ```python
   import dj_database_url
   
   MIDDLEWARE = [
       'django.middleware.security.SecurityMiddleware',
       'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
       # ... rest
   ]
   
   # Database
   DATABASES = {
       'default': dj_database_url.config(
           default='sqlite:///db.sqlite3',
           conn_max_age=600
       )
   }
   
   # Static files
   STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
   ```

3. **Deploy**
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   heroku run python manage.py migrate
   heroku run python manage.py populate_data
   heroku open
   ```

### Deployment on AWS EC2

1. **Launch EC2 Instance**
   - Choose Ubuntu Server 22.04
   - Configure security group (ports 22, 80, 443)

2. **Connect and Setup**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install dependencies
   sudo apt install python3-pip python3-venv nginx -y
   ```

3. **Deploy Application**
   ```bash
   git clone <your-repo>
   cd bms_project
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt gunicorn
   
   # Run migrations
   python manage.py migrate
   python manage.py populate_data
   python manage.py collectstatic
   ```

4. **Configure Gunicorn**
   ```bash
   gunicorn --bind 0.0.0.0:8000 bms_project.wsgi
   ```

5. **Configure Nginx**
   Create `/etc/nginx/sites-available/bookmyshow`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location = /favicon.ico { access_log off; log_not_found off; }
       
       location /static/ {
           root /home/ubuntu/bms_project;
       }
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
   
   Enable site:
   ```bash
   sudo ln -s /etc/nginx/sites-available/bookmyshow /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

6. **Setup Systemd Service**
   Create `/etc/systemd/system/gunicorn.service`:
   ```ini
   [Unit]
   Description=gunicorn daemon
   After=network.target
   
   [Service]
   User=ubuntu
   Group=www-data
   WorkingDirectory=/home/ubuntu/bms_project
   ExecStart=/home/ubuntu/bms_project/venv/bin/gunicorn \
             --workers 3 \
             --bind 127.0.0.1:8000 \
             bms_project.wsgi:application
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Start service:
   ```bash
   sudo systemctl start gunicorn
   sudo systemctl enable gunicorn
   ```

## 🧪 Testing

Run tests:
```bash
python manage.py test
```

## 🐛 Troubleshooting

### Issue: Seats not locking
**Solution:** Check that JavaScript is enabled and CSRF token is present.

### Issue: Payment not working
**Solution:** Verify Razorpay credentials in settings.py. Use test mode keys for development.

### Issue: Email not sending
**Solution:** 
- Use Gmail App Password instead of regular password
- Enable "Less secure app access" in Gmail settings
- Or use console backend for testing:
  ```python
  EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
  ```

### Issue: Static files not loading
**Solution:**
```bash
python manage.py collectstatic
```

## 📝 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

Created as a complete BookMyShow clone implementation.

## 🙏 Acknowledgments

- Django framework
- Razorpay for payment gateway
- Bootstrap for responsive design concepts

## 📞 Support

For issues and questions, please create an issue in the repository.

---

## 🎬 Movie Promotion System

Organizers can promote their movies to gain better visibility on the platform:

### How It Works
1. Organizers visit their wallet page and add funds
2. From the organizer dashboard, they can promote any of their movies
3. Promotion costs ₹500 per movie
4. Promoted movies appear at the top of the movie listings with special styling
5. Promoted movies are clearly marked with "FEATURED" badges

### Benefits
- Increased visibility for promoted movies
- Better placement in search results
- Visual distinction from regular movies
- Higher likelihood of being booked

### For Users
- Promoted movies are clearly marked with special badges
- Featured movies appear first in listings
- Easy to identify promoted content

---

**Happy Booking! 🎬🍿**
