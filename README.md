# Reddit Idea Filter

This script fetches posts from selected subreddits, uses Google's Gemini AI to filter for potential startup ideas or technical problems, and emails you a beautifully formatted report.

## Features

- Fetches recent posts from multiple subreddits
- Uses Google's Gemini 2.0 Flash model via OpenRouter to filter posts based on custom criteria
- Generates a beautiful HTML report with filtered posts
- Emails the report to your specified email address
- Saves a local copy of the HTML report

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file (or rename `.env.example` to `.env`) and fill in your details:
   ```
   # OpenRouter API Key
   OPENROUTER_KEY=your_openrouter_key_here

   # Email Configuration
   RECIPIENT_EMAIL=your_email@example.com
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password_here
   SENDER_EMAIL=your_email@gmail.com
   ```

   Note: For Gmail, you'll need to create an App Password in your Google Account security settings.

## Usage

Run the script:

```bash
python subreddit_idea_filter.py
```

### Customizing

To modify which subreddits are monitored or change the filter criteria, edit the following sections in `subreddit_idea_filter.py`:

```python
# List of subreddits to monitor
subreddits = [
    "SaaS", 
    "startups", 
    "Entrepreneur", 
    "smallbusiness",
    "webdev",
    "programming"
]

# Filter criteria for Gemini
filter_criteria = "Does this post describe a user asking for technical help or mentioning a problem that could be grounds for a startup idea or SaaS business?"
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

Use Task Scheduler to create a scheduled task that runs the script. # ideacron
# ideacron
# ideacron
