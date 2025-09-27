# Hippies Heaven Lead Generation & Outreach Bot

A comprehensive lead generation and email outreach system for smoke/vape shops in Illinois & Missouri.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp env.template .env
# Edit .env with your API keys and email settings
```

### 3. Collect Leads
```bash
python bot.py --mode collect
```

### 4. Send Emails
```bash
# Preview first (dry run)
python bot.py --mode email --dry-run --limit 5

# Send real emails
python bot.py --mode email --limit 10
```

### 5. Start Tracking Server
```bash
python pixel_server.py
# Dashboard: http://localhost:5000/dashboard
# PDF Report: http://localhost:5000/report.pdf
```

## 📋 Features

- **Lead Collection**: Scrapes smoke/vape shops from Google Places API
- **Email Outreach**: Personalized bulk email sending with Gmail SMTP
- **Open/Click Tracking**: Real-time analytics with pixel tracking
- **Dashboard**: Live web dashboard showing opens and clicks (http://localhost:5001/dashboard)
- **PDF Reports**: Automated weekly reports via email
- **Rate Limiting**: Anti-spam protection with configurable delays

## 🔧 Configuration

### Required Environment Variables (.env)
```env
# Google Places API
GOOGLE_API_KEY=your_google_places_api_key

# Gmail SMTP (use App Password)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=yourgmail@gmail.com
EMAIL_PASS=your_app_password

# Weekly Reports
REPORT_RECIPIENTS=ops@hhbrands.com,va1@hhbrands.com
REPORT_DAY=MON
REPORT_HOUR=9
```

### Getting API Keys
1. **Google Places API**: Google Cloud Console → Enable Places API → Create API Key
2. **Gmail App Password**: Google Account → Security → 2-Step Verification → App Passwords

## 📊 Usage Commands

### Lead Collection
```bash
# Default scan (IL + MO)
python bot.py --mode collect

# Denser coverage
python bot.py --mode collect --km-step 12

# Single state
python bot.py --mode collect --states IL
```

### Email Campaigns
```bash
# Dry run (preview)
python bot.py --mode email --dry-run --limit 5

# Send batch
python bot.py --mode email --limit 10

# Send all
python bot.py --mode email
```

### Tracking & Analytics
```bash
# Start tracking server
python pixel_server.py

# Access dashboard
open http://localhost:5001/dashboard

# Download PDF report
open http://localhost:5001/report.pdf
```

## 📁 Output Files

- `leads.csv` - Raw lead data
- `leads.xlsx` - Excel format
- `leads_call_sheet.xlsx` - Call sheet with contact info
- `sent_log.csv` - Email send log
- `tracking_opens.csv` - Open tracking data
- `tracking_clicks.csv` - Click tracking data

## 🎯 Email Template

Edit `email_template.txt` to customize your outreach message. Supports:
- `{Name}` - Lead name
- `{Website}` - Business website
- `{TrackingPixel}` - Open tracking pixel
- `{TrackLink:URL}` - Click tracking links

## 📈 Analytics Dashboard

The tracking server provides:
- Real-time open/click statistics
- Top 10 performing emails
- Full tracking data table
- PDF report generation
- Automated weekly email reports

## ⚠️ Important Notes

- **Rate Limiting**: Default 30s delay between emails
- **Compliance**: Includes opt-out language and age restrictions
- **Quotas**: Monitor Google Places API usage
- **Testing**: Always use `--dry-run` first
- **Logs**: Check `sent_log.csv` to avoid duplicates

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Set GOOGLE_API_KEY" | Create .env from template |
| Gmail login fails | Use App Password, not regular password |
| Few leads found | Use `--km-step 12` or increase SEARCH_RADIUS |
| No opens/clicks | Use HTML email template with tracking pixels |
| Server not reachable | Check firewall and port 5000 |

## 📞 Support

For technical issues or customization requests, contact the development team.

---
*Hippies Heaven Lead Generation Bot v1.0*
# LeadGenerationBotHippies
