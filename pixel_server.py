#!/usr/bin/env python3
"""
Hippies Heaven Tracking Server
Handles open/click tracking, dashboard, and PDF reports
"""

import os
import csv
import json
import time
import smtplib
import schedule
from datetime import datetime, timedelta
from flask import Flask, request, render_template_string, send_file, jsonify
from flask_cors import CORS
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Tracking data storage
tracking_data = {
    'opens': {},  # email -> timestamp
    'clicks': {}  # email -> [(url, timestamp), ...]
}

def load_tracking_data():
    """Load tracking data from CSV files"""
    global tracking_data
    
    # Load opens
    try:
        with open('tracking_opens.csv', 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    tracking_data['opens'][row[0]] = row[1]
    except FileNotFoundError:
        pass
    
    # Load clicks
    try:
        with open('tracking_clicks.csv', 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    email = row[0]
                    if email not in tracking_data['clicks']:
                        tracking_data['clicks'][email] = []
                    tracking_data['clicks'][email].append((row[1], row[2]))
    except FileNotFoundError:
        pass

def save_tracking_data():
    """Save tracking data to CSV files"""
    # Save opens
    with open('tracking_opens.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        for email, timestamp in tracking_data['opens'].items():
            writer.writerow([email, timestamp])
    
    # Save clicks
    with open('tracking_clicks.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        for email, clicks in tracking_data['clicks'].items():
            for url, timestamp in clicks:
                writer.writerow([email, url, timestamp])

@app.route('/pixel/<email>')
def tracking_pixel(email):
    """Track email opens with 1x1 pixel"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tracking_data['opens'][email] = timestamp
    save_tracking_data()
    
    # Return transparent 1x1 pixel
    return send_file('transparent.png', mimetype='image/png')

@app.route('/click/<email>')
def tracking_click(email):
    """Track link clicks and redirect"""
    url = request.args.get('url', 'https://hippiesheavencbd.com/wholesale')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if email not in tracking_data['clicks']:
        tracking_data['clicks'][email] = []
    tracking_data['clicks'][email].append((url, timestamp))
    save_tracking_data()
    
    # Redirect to actual URL
    from flask import redirect
    return redirect(url)

@app.route('/dashboard')
def dashboard():
    """Display tracking dashboard"""
    # Get top 10 by opens
    open_counts = {}
    for email in tracking_data['opens']:
        open_counts[email] = 1
    
    top_opens = sorted(open_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Get click counts
    click_counts = {}
    for email, clicks in tracking_data['clicks'].items():
        click_counts[email] = len(clicks)
    
    top_clicks = sorted(click_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Create dashboard HTML
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hippies Heaven Tracking Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c5530; text-align: center; margin-bottom: 30px; }}
            .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
            .stat-box {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #2c5530; }}
            .stat-number {{ font-size: 2em; font-weight: bold; color: #2c5530; }}
            .stat-label {{ color: #666; margin-top: 5px; }}
            .chart-container {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .chart-title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 15px; color: #333; }}
            .bar {{ background: #2c5530; color: white; padding: 8px 12px; margin: 5px 0; border-radius: 4px; display: flex; justify-content: space-between; }}
            .table-container {{ background: white; padding: 20px; border-radius: 8px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #f8f9fa; font-weight: bold; color: #333; }}
            .export-btn {{ background: #2c5530; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 10px 5px; }}
            .export-btn:hover {{ background: #1e3a21; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌿 Hippies Heaven Tracking Dashboard</h1>
            
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number">{len(tracking_data['opens'])}</div>
                    <div class="stat-label">Total Opens</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{sum(len(clicks) for clicks in tracking_data['clicks'].values())}</div>
                    <div class="stat-label">Total Clicks</div>
                </div>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">📊 Top 10 Email Opens</div>
                {"".join([f'<div class="bar"><span>{email}</span><span>{count}</span></div>' for email, count in top_opens])}
            </div>
            
            <div class="chart-container">
                <div class="chart-title">🔗 Top 10 Link Clicks</div>
                {"".join([f'<div class="bar"><span>{email}</span><span>{count}</span></div>' for email, count in top_clicks])}
            </div>
            
            <div class="table-container">
                <div class="chart-title">📋 Full Tracking Data</div>
                <table>
                    <tr>
                        <th>Email</th>
                        <th>Opens</th>
                        <th>Clicks</th>
                        <th>Last Open</th>
                        <th>Last Click</th>
                    </tr>
                    {"".join([f'<tr><td>{email}</td><td>{"Yes" if email in tracking_data["opens"] else "No"}</td><td>{len(tracking_data["clicks"].get(email, []))}</td><td>{tracking_data["opens"].get(email, "Never")}</td><td>{tracking_data["clicks"].get(email, [("", "Never")])[-1][1] if tracking_data["clicks"].get(email) else "Never"}</td></tr>' for email in set(list(tracking_data["opens"].keys()) + list(tracking_data["clicks"].keys()))])}
                </table>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/report.pdf" class="export-btn">📄 Download PDF Report</a>
                <button onclick="location.reload()" class="export-btn">🔄 Refresh</button>
            </div>
        </div>
    </body>
    </html>
    """
    
    return dashboard_html

@app.route('/report.pdf')
def generate_pdf_report():
    """Generate PDF report"""
    try:
        # Create PDF
        filename = f"hippies_heaven_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,
            textColor=colors.HexColor('#2c5530')
        )
        story.append(Paragraph("Hippies Heaven Lead Generation Report", title_style))
        story.append(Spacer(1, 20))
        
        # Summary stats
        total_opens = len(tracking_data['opens'])
        total_clicks = sum(len(clicks) for clicks in tracking_data['clicks'].values())
        
        # Calculate rates
        all_emails = set(list(tracking_data['opens'].keys()) + list(tracking_data['clicks'].keys()))
        total_emails = len(all_emails) if all_emails else 1
        open_rate = (total_opens / total_emails * 100) if all_emails else 0
        click_rate = (total_clicks / total_emails * 100) if all_emails else 0
        
        summary_data = [
            ['Metric', 'Count'],
            ['Total Email Opens', str(total_opens)],
            ['Total Link Clicks', str(total_clicks)],
            ['Open Rate', f"{open_rate:.1f}%"],
            ['Click Rate', f"{click_rate:.1f}%"],
            ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5530')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Summary Statistics", styles['Heading2']))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Detailed tracking data
        all_emails = set(list(tracking_data['opens'].keys()) + list(tracking_data['clicks'].keys()))
        tracking_data_list = []
        
        for email in sorted(all_emails):
            opens = "Yes" if email in tracking_data['opens'] else "No"
            click_count = len(tracking_data['clicks'].get(email, []))
            last_open = tracking_data['opens'].get(email, "Never")
            last_click = tracking_data['clicks'].get(email, [("", "Never")])[-1][1] if tracking_data['clicks'].get(email) else "Never"
            
            tracking_data_list.append([email, opens, str(click_count), last_open, last_click])
        
        if tracking_data_list:
            # Add headers
            tracking_data_list.insert(0, ['Email', 'Opened', 'Clicks', 'Last Open', 'Last Click'])
            
            tracking_table = Table(tracking_data_list)
            tracking_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5530')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(Paragraph("Detailed Tracking Data", styles['Heading2']))
            story.append(tracking_table)
        
        # Build PDF
        doc.build(story)
        
        return send_file(filename, as_attachment=True, mimetype='application/pdf')
        
    except Exception as e:
        return f"Error generating PDF: {str(e)}", 500

def send_weekly_report():
    """Send weekly report via email"""
    try:
        # Generate PDF report
        filename = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Create report content (similar to generate_pdf_report)
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,
            textColor=colors.HexColor('#2c5530')
        )
        story.append(Paragraph("Hippies Heaven Weekly Report", title_style))
        story.append(Spacer(1, 20))
        
        # Add summary and data
        total_opens = len(tracking_data['opens'])
        total_clicks = sum(len(clicks) for clicks in tracking_data['clicks'].values())
        
        summary_data = [
            ['Metric', 'Count'],
            ['Total Email Opens', str(total_opens)],
            ['Total Link Clicks', str(total_clicks)],
            ['Report Date', datetime.now().strftime('%Y-%m-%d')]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5530')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Weekly Summary", styles['Heading2']))
        story.append(summary_table)
        doc.build(story)
        
        # Send email
        recipients = os.getenv('REPORT_RECIPIENTS', '').split(',')
        if not recipients or not recipients[0]:
            print("⚠️ No report recipients configured")
            return
        
        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_USER')
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = f"Hippies Heaven Weekly Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
        Weekly Lead Generation Report
        
        Total Opens: {total_opens}
        Total Clicks: {total_clicks}
        
        Please see attached PDF for detailed tracking data.
        
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        with open(filename, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(os.getenv('SMTP_SERVER', 'smtp.gmail.com'), int(os.getenv('SMTP_PORT', 587)))
        server.starttls()
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Weekly report sent to {len(recipients)} recipients")
        
        # Clean up
        os.remove(filename)
        
    except Exception as e:
        print(f"❌ Error sending weekly report: {e}")

def schedule_weekly_reports():
    """Schedule weekly reports"""
    report_day = os.getenv('REPORT_DAY', 'MON').upper()
    report_hour = int(os.getenv('REPORT_HOUR', 9))
    
    # Map day names to schedule
    day_mapping = {
        'MON': schedule.every().monday,
        'TUE': schedule.every().tuesday,
        'WED': schedule.every().wednesday,
        'THU': schedule.every().thursday,
        'FRI': schedule.every().friday,
        'SAT': schedule.every().saturday,
        'SUN': schedule.every().sunday
    }
    
    if report_day in day_mapping:
        day_mapping[report_day].at(f"{report_hour:02d}:00").do(send_weekly_report)
        print(f"📅 Weekly reports scheduled for {report_day} at {report_hour}:00")
    else:
        print(f"⚠️ Invalid REPORT_DAY: {report_day}")

if __name__ == '__main__':
    # Load existing tracking data
    load_tracking_data()
    
    # Schedule weekly reports
    schedule_weekly_reports()
    
    print("🚀 Starting Hippies Heaven Tracking Server...")
    print("📊 Dashboard: http://localhost:5001/dashboard")
    print("📄 PDF Report: http://localhost:5001/report.pdf")
    print("⏰ Weekly reports scheduled")
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5001, debug=False)
