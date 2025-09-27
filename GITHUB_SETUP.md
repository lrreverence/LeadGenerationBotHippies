# GitHub Actions Setup Guide

## Repository Setup Complete ✅

Your Lead Generation Bot has been successfully pushed to GitHub with automated daily collection for all 50 states.

## Required GitHub Secrets Configuration

To enable the automated workflow, you need to configure the following secrets in your GitHub repository:

### 1. Go to Repository Settings
- Navigate to: https://github.com/lrreverence/LeadGenerationBotHippies
- Click on **Settings** tab
- Click on **Secrets and variables** → **Actions**

### 2. Add Required Secrets

Click **New repository secret** for each of the following:

#### `GOOGLE_API_KEY`
- **Value**: Your Google Places API key
- **Description**: Required for lead collection from Google Places API

#### `GMAIL_USER`
- **Value**: Your Gmail address (e.g., wholesale@hippiesheavencbd.com)
- **Description**: Gmail account for sending outreach emails

#### `GMAIL_PASSWORD`
- **Value**: Your Gmail app password (not regular password)
- **Description**: Gmail app password for SMTP authentication

#### `REPORT_EMAIL`
- **Value**: Email address to receive daily reports
- **Description**: Where to send collection reports and summaries

### 3. Gmail App Password Setup

If you haven't set up an app password for Gmail:

1. Go to your Google Account settings
2. Navigate to **Security** → **2-Step Verification**
3. Under **App passwords**, create a new app password
4. Use this app password (not your regular Gmail password) for `GMAIL_PASSWORD`

## Workflow Schedule

The GitHub Action is configured to run:
- **Daily at 6:00 AM CST** (12:00 PM UTC)
- **All 50 states** in parallel for maximum efficiency
- **Automatic data collection** and storage
- **Results committed** back to the repository

## Manual Testing

You can manually trigger the workflow:
1. Go to **Actions** tab in your repository
2. Select **Daily Lead Collection - All 50 States**
3. Click **Run workflow** → **Run workflow**

## Monitoring

- Check the **Actions** tab to monitor workflow runs
- View logs for each state's collection progress
- Download artifacts containing collected lead data
- Review committed results in the repository

## File Structure

Each daily run will create:
- State-specific folders: `Alabama-20250926/`, `Alaska-20250926/`, etc.
- Timestamped files: `leads_Alabama_20250926_060000.csv`
- Main accumulation files: `leads.csv`, `leads.xlsx`, `leads_call_sheet.xlsx`

## Next Steps

1. ✅ Configure the GitHub Secrets above
2. ✅ Test the workflow manually
3. ✅ Monitor the first automated run tomorrow at 6 AM CST
4. ✅ Review collected data and adjust search parameters if needed

Your bot is now fully automated and will collect leads from all 50 states daily!
