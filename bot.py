#!/usr/bin/env python3
"""
Hippies Heaven Lead Generation & Outreach Bot
Scrapes smoke/vape shops in IL & MO, sends personalized emails
"""

import os
import sys
import csv
import json
import time
import smtplib
import argparse
import pandas as pd
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import googlemaps
import requests
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

class LeadGenerationBot:
    def __init__(self):
        self.gmaps = None
        self.smtp_server = None
        self.delay = int(os.getenv('DEFAULT_DELAY', 30))
        self.max_emails = int(os.getenv('MAX_EMAILS_PER_BATCH', 50))
        
        # Initialize Google Maps client
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key or api_key == 'YOUR_GOOGLE_PLACES_API_KEY':
            print("❌ Error: Set GOOGLE_API_KEY in .env file")
            sys.exit(1)
        
        self.gmaps = googlemaps.Client(key=api_key)
        
        # Initialize SMTP
        self._init_smtp()
        
    def _init_smtp(self):
        """Initialize SMTP connection for email sending"""
        try:
            self.smtp_server = smtplib.SMTP(
                os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                int(os.getenv('SMTP_PORT', 587))
            )
            self.smtp_server.starttls()
            self.smtp_server.login(
                os.getenv('EMAIL_USER'),
                os.getenv('EMAIL_PASS')
            )
            print("✅ SMTP connection established")
        except Exception as e:
            print(f"❌ SMTP connection failed: {e}")
            self.smtp_server = None
    
    def collect_leads(self, states=['IL', 'MO'], km_step=25):
        """Collect leads from Google Places API"""
        print(f"🔍 Collecting leads for states: {', '.join(states)}")
        
        all_leads = []
        search_radius = int(os.getenv('SEARCH_RADIUS', 5000))
        include_vape = os.getenv('INCLUDE_VAPE', 'true').lower() == 'true'
        
        # Search terms for smoke/vape shops (focused list)
        search_terms = [
            'smoke shop',
            'tobacco shop',
            'vape shop',
            'head shop',
            'cigar shop'
        ]
        
        for state in states:
            print(f"📍 Processing {state}...")
            
            # Get state center coordinates
            state_centers = self._get_state_centers()
            if state not in state_centers:
                print(f"⚠️ Unknown state: {state}")
                continue
                
            center_lat, center_lng = state_centers[state]
            
            # For Illinois, use major cities for better coverage
            if state == 'IL':
                major_cities = [
                    (41.8781, -87.6298),  # Chicago
                    (40.1164, -89.1989), # Springfield
                    (40.1125, -88.2073), # Champaign
                    (41.2619, -89.0644), # Rockford
                    (41.4993, -90.5154), # Moline
                    (41.7370, -88.0112), # Aurora
                    (41.7508, -87.9735), # Naperville
                    (42.2711, -89.0940), # Rockford area
                    (40.1106, -88.2072), # Urbana
                    (41.5200, -90.5750), # Davenport area (IL side)
                    (39.7817, -89.6501), # Decatur
                    (41.5200, -87.8870), # Joliet
                    (42.0334, -88.0834), # Elgin
                    (41.8500, -87.6500), # Cicero
                    (41.8781, -87.6298), # Chicago Loop
                ]
                grid_points = major_cities
            else:
                # Create search grid for other states
                grid_points = self._create_search_grid(center_lat, center_lng, km_step)
            
            for i, (lat, lng) in enumerate(grid_points):
                print(f"  Grid point {i+1}/{len(grid_points)}: {lat:.4f}, {lng:.4f}")
                
                for term in search_terms:
                    try:
                        # Search for places
                                        places_result = self.gmaps.places_nearby(
                                            location=(lat, lng),
                                            radius=search_radius,
                                            keyword=term,
                                            type='store'
                                        )
                                        
                                        for place in places_result.get('results', []):
                                            lead = self._process_place(place, state)
                                            if lead and not self._is_duplicate(lead, all_leads):
                                                all_leads.append(lead)
                                                print(f"    ✅ Found: {lead.get('name', 'Unknown')} ({term})")
                                        
                                        # Rate limiting
                                        time.sleep(0.5)
                                        
                    except Exception as e:
                        print(f"    ❌ Error searching {term}: {e}")
                        continue
                        
        # Save leads
        state_name_mapping = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
            'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
            'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
            'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
            'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
            'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
            'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
            'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
        }
        state_name = state_name_mapping.get(state, state)
        self._save_leads(all_leads, state_name)
        print(f"✅ Collected {len(all_leads)} leads")
        return all_leads
    
    def _get_state_centers(self):
        """Get center coordinates for all 50 states"""
        return {
            'AL': (32.806671, -86.791130),  # Alabama
            'AK': (64.200841, -149.493673), # Alaska
            'AZ': (33.729759, -111.431221), # Arizona
            'AR': (34.969704, -92.373123), # Arkansas
            'CA': (36.116203, -119.681564), # California
            'CO': (39.059811, -105.311104), # Colorado
            'CT': (41.597782, -72.755371),  # Connecticut
            'DE': (39.318523, -75.507141),  # Delaware
            'FL': (27.766279, -82.640373),  # Florida
            'GA': (33.040619, -83.643074),  # Georgia
            'HI': (21.094318, -157.498337), # Hawaii
            'ID': (44.240459, -114.478828), # Idaho
            'IL': (40.349457, -88.986137),  # Illinois
            'IN': (39.849426, -86.258278),  # Indiana
            'IA': (42.011539, -93.210526),  # Iowa
            'KS': (38.526600, -96.726486),  # Kansas
            'KY': (37.668140, -84.670067),  # Kentucky
            'LA': (31.169546, -91.867805),  # Louisiana
            'ME': (44.323535, -69.765261),  # Maine
            'MD': (39.063946, -76.802101),  # Maryland
            'MA': (42.230171, -71.530106),  # Massachusetts
            'MI': (43.326618, -84.536095),  # Michigan
            'MN': (45.694454, -93.900192),  # Minnesota
            'MS': (32.320, -89.877),        # Mississippi
            'MO': (38.456085, -92.288368), # Missouri
            'MT': (47.052632, -110.454353), # Montana
            'NE': (41.125370, -98.268082),  # Nebraska
            'NV': (38.313515, -117.055374), # Nevada
            'NH': (43.452492, -71.563896), # New Hampshire
            'NJ': (40.298904, -74.521011), # New Jersey
            'NM': (34.840515, -106.248482), # New Mexico
            'NY': (42.165726, -74.948051),  # New York
            'NC': (35.630066, -79.806419),  # North Carolina
            'ND': (47.528912, -99.784012),  # North Dakota
            'OH': (40.388783, -82.764915),  # Ohio
            'OK': (35.565342, -96.928917),  # Oklahoma
            'OR': (44.572021, -122.070938), # Oregon
            'PA': (40.590752, -77.209755),  # Pennsylvania
            'RI': (41.680893, -71.51178),  # Rhode Island
            'SC': (33.856892, -80.945007),  # South Carolina
            'SD': (44.299782, -99.438828),  # South Dakota
            'TN': (35.747845, -86.692345),  # Tennessee
            'TX': (31.054487, -97.563461),  # Texas
            'UT': (40.150032, -111.862434), # Utah
            'VT': (44.045876, -72.710686),  # Vermont
            'VA': (37.769337, -78.169968),  # Virginia
            'WA': (47.400902, -121.490494), # Washington
            'WV': (38.491226, -80.954453),  # West Virginia
            'WI': (44.268543, -89.616508),  # Wisconsin
            'WY': (42.755966, -107.302490), # Wyoming
        }
                    
    def _create_search_grid(self, center_lat, center_lng, km_step):
        """Create a grid of search points around state center"""
        # Convert km to degrees (rough approximation)
        lat_step = km_step / 111.0
        lng_step = km_step / (111.0 * abs(center_lat) * 0.0174532925)
        
        grid_points = []
        for lat_offset in range(-2, 3):  # 5x5 grid
            for lng_offset in range(-2, 3):
                lat = center_lat + (lat_offset * lat_step)
                lng = center_lng + (lng_offset * lng_step)
                grid_points.append((lat, lng))
        
        return grid_points
    
    def _process_place(self, place, state):
        """Process a Google Places result into a lead"""
        try:
            # Get detailed place info       
            place_id = place.get('place_id')
            if not place_id:
                return None
            
            details = self.gmaps.place(
                place_id=place_id,
                fields=['name', 'formatted_address', 'formatted_phone_number', 
       'website', 'business_status']
            )
            
            place_details = details.get('result', {})
            
            # Skip if permanently closed, but allow other statuses
            if place_details.get('business_status') == 'CLOSED_PERMANENTLY':
                return None
            
            # Extract contact info
            name = place_details.get('name', '')
            address = place_details.get('formatted_address', '')
            phone = place_details.get('formatted_phone_number', '')
            website = place_details.get('website', '')
            
            # Filter by state - only include if address contains the target state
            if state == 'IL' and not any(state_code in address.upper() for state_code in ['IL', 'ILLINOIS']):
                return None
            elif state == 'MO' and not any(state_code in address.upper() for state_code in ['MO', 'MISSOURI']):
                return None
            
            # Try to extract email from website
            email = self._extract_email_from_website(website)
            
            return {
                'name': name,
                'address': address,
                'phone': phone,
                'website': website,
                'email': email,
                'state': state,
                'contacted': 'No',
                'notes': '',
                'place_id': place_id,
                'collected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"    ⚠️ Error processing place: {e}")
            return None
    
    def _extract_email_from_website(self, website):
        """Try to extract email from business website"""
        if not website:
            return ''
        
        try:
            response = requests.get(website, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for email patterns
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, soup.get_text())
            
            # Return first valid email found
            for email in emails:
                if not email.lower().endswith(('.png', '.jpg', '.gif', '.css', '.js')):
                    return email.lower()
            
        except Exception:
            pass
            
        return ''
    
    def _is_duplicate(self, new_lead, existing_leads):
        """Check if lead already exists"""
        for existing in existing_leads:
            if (existing.get('name') == new_lead.get('name') and 
                existing.get('address') == new_lead.get('address')):
                return True
        return False
    
    def _save_leads(self, leads, state_name):
        """Save leads to CSV and Excel files"""
        if not leads:
            print("⚠️ No leads to save")
            return
        
        # Create timestamp for unique filenames and folder
        date = datetime.now().strftime('%Y%m%d')
        time_24h = datetime.now().strftime('%H%M%S')
        timestamp = f'{date}_{time_24h}'
        folder_name = f'{state_name}-{date}'
        
        # Create folder for this collection
        import os
        os.makedirs(folder_name, exist_ok=True)
        
        # Save to CSV in folder
        csv_filename = os.path.join(folder_name, f'leads_{state_name}_{date}_{time_24h}.csv')
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            if leads:
                writer = csv.DictWriter(f, fieldnames=leads[0].keys())
                writer.writeheader()
                writer.writerows(leads)
        
        # Save to Excel in folder
        excel_filename = os.path.join(folder_name, f'leads_{state_name}_{date}_{time_24h}.xlsx')
        df = pd.DataFrame(leads)
        df.to_excel(excel_filename, index=False)
        
        # Create call sheet with specific columns in folder
        call_sheet_filename = os.path.join(folder_name, f'leads_call_sheet_{state_name}_{date}_{time_24h}.xlsx')
        call_sheet_df = df[['name', 'phone', 'address', 'website', 'state', 'contacted', 'notes', 'email']].copy()
        call_sheet_df.to_excel(call_sheet_filename, index=False)
        
        # Append to main files (accumulate all states)
        main_csv_exists = os.path.exists('leads.csv')
        with open('leads.csv', 'a', newline='', encoding='utf-8') as f:
            if leads:
                writer = csv.DictWriter(f, fieldnames=leads[0].keys())
                if not main_csv_exists:
                    writer.writeheader()
                writer.writerows(leads)
        
        # For Excel files, we need to read existing data and append
        if os.path.exists('leads.xlsx'):
            existing_df = pd.read_excel('leads.xlsx')
            combined_df = pd.concat([existing_df, df], ignore_index=True)
        else:
            combined_df = df
        combined_df.to_excel('leads.xlsx', index=False)
        
        if os.path.exists('leads_call_sheet.xlsx'):
            existing_call_df = pd.read_excel('leads_call_sheet.xlsx')
            combined_call_df = pd.concat([existing_call_df, call_sheet_df], ignore_index=True)
        else:
            combined_call_df = call_sheet_df
        combined_call_df.to_excel('leads_call_sheet.xlsx', index=False)
        
        print(f"💾 Saved {len(leads)} leads to folder: {folder_name}/")
        print(f"   📁 {folder_name}/")
        print(f"   📄 leads_{state_name}_{date}_{time_24h}.csv")
        print(f"   📊 leads_{state_name}_{date}_{time_24h}.xlsx")
        print(f"   📋 leads_call_sheet_{state_name}_{date}_{time_24h}.xlsx")
        print(f"   📄 leads.csv (appended)")
        print(f"   📊 leads.xlsx (appended)")
        print(f"   📋 leads_call_sheet.xlsx (appended)")
    
    def send_emails(self, dry_run=False, limit=None):
        """Send emails to leads"""
        if not self.smtp_server:
            print("❌ SMTP not configured")
            return
        
        # Load leads
        try:
            df = pd.read_excel('leads_call_sheet.xlsx')
        except FileNotFoundError:
            print("❌ leads_call_sheet.xlsx not found. Run collection first.")
            return
        
        # Filter leads with emails
        email_leads = df[df['email'].notna() & (df['email'] != '') & (df['email'] != ' ')]
        
        if email_leads.empty:
            print("❌ No leads with email addresses found")
            return
        
        # Apply limit if specified
        if limit:
            email_leads = email_leads.head(limit)
        
        print(f"📧 {'Previewing' if dry_run else 'Sending'} emails to {len(email_leads)} leads")
        
        # Load email template
        try:
            with open('email_template.txt', 'r', encoding='utf-8') as f:
                template_content = f.read()
        except FileNotFoundError:
            print("❌ email_template.txt not found")
            return
        
        # Extract subject line and body
        lines = template_content.strip().split('\n')
        if lines[0].startswith('Subject: '):
            subject = lines[0][9:]  # Remove "Subject: " prefix
            template = '\n'.join(lines[1:]).strip()  # Rest of the content
        else:
            subject = "Wholesale Opportunity – Hippies Heaven Products"
            template = template_content
        
        # Load sent log             
        sent_log = self._load_sent_log()
        
        sent_count = 0
        for index, lead in email_leads.iterrows():
            email = lead['email'].strip()
            
            # Skip if already sent
            if email in sent_log:
                print(f"⏭️ Skipping {email} (already sent)")
                continue
            
            if dry_run:
                print(f"📧 Would send to: {email} ({lead.get('name', 'Unknown')})")
                sent_count += 1
            else:
                success = self._send_single_email(email, lead, template, subject)
                if success:
                    sent_count += 1
                    sent_log[email] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._save_sent_log(sent_log)
                
                # Rate limiting
                time.sleep(self.delay)
        
        print(f"✅ {'Previewed' if dry_run else 'Sent'} {sent_count} emails")
    
    def send_test_email(self, test_email, dry_run=False):
        """Send a test email to a specific address"""
        if not self.smtp_server:
            print("❌ SMTP not configured")
            return
        
        # Create a test lead
        test_lead = {
            'name': 'Test Store',
            'email': test_email,
            'phone': '(555) 123-4567',
            'address': '123 Test Street, Test City, IL 12345',
            'website': 'https://teststore.com',
            'state': 'IL',
            'contacted': 'No',
            'notes': 'Test email'
        }
        
        print(f"📧 {'Previewing' if dry_run else 'Sending'} test email to {test_email}...")
        
        # Load email template
        try:
            with open('email_template.txt', 'r', encoding='utf-8') as f:
                template_content = f.read()
        except FileNotFoundError:
            print("❌ email_template.txt not found")
            return
        
        # Extract subject line and body
        lines = template_content.strip().split('\n')
        if lines[0].startswith('Subject: '):
            subject = lines[0][9:]  # Remove "Subject: " prefix
            template = '\n'.join(lines[1:]).strip()  # Rest of the content
        else:
            subject = "Wholesale Opportunity – Hippies Heaven Products"
            template = template_content
        
        try:
            if dry_run:
                print(f"📧 Would send to: {test_email} (Test Store)")
                print("📋 Email preview:")
                print("-" * 50)
                # Show personalized template
                # Replace TrackLink placeholders manually
                personalized = template.replace('{Name}', test_lead.get('name', 'Valued Customer'))
                personalized = personalized.replace('{Website}', test_lead.get('website', ''))
                personalized = personalized.replace('{TrackingPixel}', f'<img src="http://localhost:5001/pixel/{test_email}" width="1" height="1" style="display:none;">')
                # Replace TrackLink with actual link text
                personalized = personalized.replace('{TrackLink:https://hippiesheavencbd.com/wholesale}', 'latest wholesale catalog')
                # Update the href to use tracking
                personalized = personalized.replace('href="https://hippiesheavencbd.com/wholesale"', f'href="http://localhost:5001/click/{test_email}?url=https://hippiesheavencbd.com/wholesale"')
                print(personalized[:500] + "..." if len(personalized) > 500 else personalized)
                print("-" * 50)
            else:
                success = self._send_single_email(test_email, test_lead, template, subject)
                if success:
                    print(f"✅ Test email sent successfully to {test_email}")
                else:
                    print(f"❌ Failed to send test email")
        except Exception as e:
            print(f"❌ Error sending test email: {e}")
    
    def _send_single_email(self, email, lead, template, subject="Wholesale Opportunity – Hippies Heaven Products"):
        """Send a single email to a lead"""
        try:
            # Personalize template
            personalized = template.replace('{Name}', lead.get('name', 'Valued Customer'))
            personalized = personalized.replace('{Website}', lead.get('website', ''))
            personalized = personalized.replace('{TrackingPixel}', f'<img src="http://localhost:5001/pixel/{email}" width="1" height="1" style="display:none;">')
            # Replace TrackLink with actual link text
            personalized = personalized.replace('{TrackLink:https://hippiesheavencbd.com/wholesale}', 'latest wholesale catalog')
            # Update the href to use tracking
            personalized = personalized.replace('href="https://hippiesheavencbd.com/wholesale"', f'href="http://localhost:5001/click/{email}?url=https://hippiesheavencbd.com/wholesale"')
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = os.getenv('EMAIL_USER')
            msg['To'] = email
            msg['Subject'] = subject
            
            # Add HTML body
            html_part = MIMEText(personalized, 'html')
            msg.attach(html_part)
            
            # Send email
            self.smtp_server.send_message(msg)
            print(f"✅ Sent to: {email} ({lead.get('name', 'Unknown')})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send to {email}: {e}")
            return False
    
    def _load_sent_log(self):
        """Load sent emails log"""
        try:
            with open('sent_log.csv', 'r') as f:
                reader = csv.reader(f)
                return {row[0]: row[1] for row in reader}
        except FileNotFoundError:
            return {}
    
    def _save_sent_log(self, sent_log):
        """Save sent emails log"""
        with open('sent_log.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            for email, timestamp in sent_log.items():
                writer.writerow([email, timestamp])

def main():
    parser = argparse.ArgumentParser(description='Hippies Heaven Lead Generation Bot')
    parser.add_argument('--mode', choices=['collect', 'email'], required=True,
                       help='Mode: collect leads or send emails')
    parser.add_argument('--states', nargs='+', default=['IL', 'MO'],
                       help='States to process (default: IL MO)')
    parser.add_argument('--km-step', type=int, default=25,
                       help='Grid step size in km (default: 25)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview emails without sending')
    parser.add_argument('--limit', type=int,
                       help='Limit number of emails to send')
    parser.add_argument('--test-email', type=str,
                       help='Send test email to specific address')
    
    args = parser.parse_args()
    
    bot = LeadGenerationBot()
    
    if args.mode == 'collect':
        bot.collect_leads(states=args.states, km_step=args.km_step)
    elif args.mode == 'email':
        if args.test_email:
            bot.send_test_email(args.test_email, dry_run=args.dry_run)
        else:
            bot.send_emails(dry_run=args.dry_run, limit=args.limit)

if __name__ == '__main__':
    main()
