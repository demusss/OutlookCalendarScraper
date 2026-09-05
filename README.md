# Outlook calendar scraper
Synchronize a Microsoft Outlook / Teams university calendar with Google Calendar using a self-hosted, Dockerized service.

This project was created to solve a real-world limitation: university Outlook calendars (published via Microsoft 365 / Teams) often cannot be directly subscribed to in Google Calendar due to permission or authentication restrictions.

## Architecture / App flow
```
  Outlook / Teams Calendar
            │
            ▼
     Selenium Scraper
            │
            ▼
    Event Parser (Python)
            │
            ▼
      ICS Generator
            │
            ▼
      Web Endpoint
            │
            ▼
 Google Calendar (Subscribe via URL)
```

## Tech stack
- Python + Selenium
- Docker / Docker compose
- Nginx (serving the calendar)
- VPS (running debian)
- Google Calendar (ICS subscription)

## Setting up dev env

### Clone repo
```
git clone https://github.com/Kir4R00t/OutlookCalendarScraper
cd OutlookCalendarScraper
```

### Create enviornment file
```
nano .env
OUTLOOK_URL=https://your-outlook-calendar-url
SCRAPE_DAYS=7
```

### Start services
```
sudo docker compose up --build -d
```

### Access the calendar
Now you can subscribe to your outlook calendar in Google by pasting in this link 
```
http://your-server-ip:8080/outlook.ics
```
