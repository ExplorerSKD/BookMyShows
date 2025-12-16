# Quick Start Guide

## Setup in 5 Minutes ⚡

### 1. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Database
```bash
python manage.py migrate
python manage.py populate_data
```

### 4. Run Server
```bash
python manage.py runserver
```

### 5. Open Browser
Visit: http://127.0.0.1:8000/

## Default Credentials

**Admin Access:**
- Username: `admin`
- Password: `admin123`
- Dashboard: http://127.0.0.1:8000/admin/dashboard/

**Test User:**
- Username: `testuser`
- Password: `testpass123`

## Test the System

1. Browse movies at homepage
2. Click on a movie
3. Select a show
4. Login with testuser
5. Select seats and click "Lock Seats"
6. For payment testing:
   - Use Razorpay test mode
   - Or skip payment by directly accessing /profile/

## What's Included

✅ 2 Cinemas (Mumbai, Delhi)  
✅ 3 Screens with seats  
✅ 5 Movies with trailers  
✅ Shows for next 7 days  
✅ Ready-to-use admin dashboard  

## Next Steps

1. Configure email in `bms_project/settings.py`
2. Add Razorpay keys for payment gateway
3. Customize movies and shows via admin panel
4. Deploy using README deployment guide

## Troubleshooting

**Issue:** Import errors  
**Fix:** Make sure virtual environment is activated

**Issue:** Database not found  
**Fix:** Run `python manage.py migrate`

**Issue:** No data showing  
**Fix:** Run `python manage.py populate_data`

For detailed documentation, see [README.md](README.md)
