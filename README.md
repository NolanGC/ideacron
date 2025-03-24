# Reddit Idea Filter

This script fetches posts from selected subreddits, uses Google's Gemini AI to filter for potential startup ideas or technical problems, and emails you a beautifully formatted report.

## Features

- Fetches recent posts from multiple subreddits using Reddit's API
- Uses Google's Gemini 2.0 Flash model via OpenRouter to filter posts based on custom criteria
- Generates a beautiful HTML report with filtered posts
- Emails the report to your specified email address

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file (or rename `.env.example` to `.env`) and fill in your details:
   ```
   # OpenRouter API Key - REQUIRED
   OPENROUTER_KEY=your_openrouter_key_here

   # Reddit API Credentials - RECOMMENDED for AWS/cloud deployments
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   REDDIT_USER_AGENT=python:idea-filter:v1.0 (by /u/yourusername)

   # Email Configuration (if you want email reports)
   RECIPIENT_EMAIL=your_email@example.com
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password_here
   SENDER_EMAIL=your_email@gmail.com
   ```

## Setting up Reddit API Access (Essential for AWS/Cloud Deployments)

To avoid 403 errors when running in AWS or other cloud environments, you need to set up Reddit API credentials:

1. Go to https://www.reddit.com/prefs/apps
2. Scroll to the bottom and click "create another app..."
3. Fill in the form:
   - Name: IdeaFilter (or any name you prefer)
   - Type: Select "script" 
   - Description: Reddit post filtering script
   - About URL: (can be left blank)
   - Redirect URI: http://localhost:8080 (this won't be used but is required)
4. Click "create app"
5. Copy the Client ID (the string under the app name)
6. Copy the Client Secret
7. Add these to your .env file

## Usage

Run the script:

```bash
python subreddit_idea_filter.py
```

### Customizing

To modify which subreddits are monitored or change the filter criteria, edit the following sections in `subreddit_idea_filter.py`:

```python
subreddits = [
    "RealEstateTechnology", 
    "PropTech",
    "HealthTech",
    "EdTech"
]

filter_criteria = "Does the post include a user posing a question, asking for reccomendation or about the existence of some software that could lay the groundwork for a startup..."
```

## Automation

To run this script automatically on a schedule:

### On Linux/Mac:

Add a cron job:

```bash
crontab -e
```

Add a line like this to run it daily at 8 AM:

```
0 8 * * * cd /path/to/script/directory && python subreddit_idea_filter.py
```

### On Windows:

Use Task Scheduler to create a scheduled task that runs the script.
