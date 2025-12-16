# Scheduling Email Reminders

To automatically send email reminders for upcoming shows, you need to schedule the `send_upcoming_show_reminders` management command to run daily.

## For Linux/macOS (using crontab):

1. Open crontab:
   ```bash
   crontab -e
   ```

2. Add this line to run the command daily at 9 AM:
   ```bash
   0 9 * * * cd /path/to/your/project && /path/to/your/venv/bin/python manage.py send_upcoming_show_reminders
   ```

## For Windows (using Task Scheduler):

1. Open Task Scheduler
2. Create a new task
3. Set trigger to daily at your preferred time
4. Set action to run:
   ```
   Program: C:\path\to\your\venv\Scripts\python.exe
   Arguments: manage.py send_upcoming_show_reminders
   Start in: C:\path\to\your\project
   ```

## For Heroku (using Heroku Scheduler):

1. Add the Heroku Scheduler addon:
   ```bash
   heroku addons:create scheduler:standard
   ```

2. Open the scheduler dashboard:
   ```bash
   heroku addons:open scheduler
   ```

3. Add a new job with the command:
   ```
   python manage.py send_upcoming_show_reminders
   ```

## Testing the Command:

You can manually test the command with:
```bash
python manage.py send_upcoming_show_reminders
```

This will send reminders for all shows happening tomorrow.