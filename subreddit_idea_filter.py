import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime
import time
from dotenv import load_dotenv
from openai import OpenAI
import praw
import random

# Load environment variables
load_dotenv()

def validate_env_variables():
    """Validate that required environment variables are set."""
    required_vars = {
        "OPENROUTER_KEY": "Required for Gemini API access via OpenRouter",
    }
    
    optional_vars = {
        "RECIPIENT_EMAIL": "Required for email sending functionality",
        "SMTP_SERVER": "Used for email functionality (default: smtp.gmail.com)",
        "SMTP_PORT": "Used for email functionality (default: 587)",
        "SMTP_USERNAME": "Required for email authentication",
        "SMTP_PASSWORD": "Required for email authentication",
        "SENDER_EMAIL": "Used for email sending (defaults to SMTP_USERNAME)",
        "REDDIT_CLIENT_ID": "Required for Reddit API authentication",
        "REDDIT_CLIENT_SECRET": "Required for Reddit API authentication",
        "REDDIT_USER_AGENT": "Required for Reddit API authentication",
    }
    
    missing_required = []
    missing_optional = []
    
    # Check required variables
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_required.append(f"{var}: {description}")
    
    # Check optional variables
    for var, description in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"{var}: {description}")
    
    # Handle missing variables
    if missing_required:
        print("ERROR: The following required environment variables are missing:")
        for var in missing_required:
            print(f"  - {var}")
        print("\nMake sure you have a proper .env file in your project directory.")
        return False
    
    if missing_optional:
        print("WARNING: The following optional environment variables are missing:")
        for var in missing_optional:
            print(f"  - {var}")
        print("\nSome functionality may be limited.")
    
    return True

@dataclass
class Post:
    title: str
    author: str
    score: int
    url: str
    created_utc: float
    num_comments: int
    selftext: Optional[str]
    subreddit: str
    permalink: str
    
    def get_age_str(self) -> str:
        """Return a human-readable string representing the post's age."""
        now = time.time()
        age_seconds = now - self.created_utc
        
        if age_seconds < 60:
            return f"{int(age_seconds)}s"
        elif age_seconds < 3600:
            return f"{int(age_seconds / 60)}m"
        elif age_seconds < 86400:
            return f"{int(age_seconds / 3600)}h"
        else:
            return f"{int(age_seconds / 86400)}d"
    
    def get_full_url(self) -> str:
        """Return the full Reddit URL for the post."""
        return f"https://www.reddit.com{self.permalink}"


def fetch_new_posts(subreddit: str, limit: int = 25) -> List[Post]:
    """Fetch new posts from a subreddit using authenticated Reddit API."""
    posts = []
    
    # Try to use Reddit API with authentication first
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "python:idea-filter:v1.0 (by /u/yourusername)")
    
    if client_id and client_secret:
        try:
            print(f"Using authenticated Reddit API for r/{subreddit}...")
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            
            subreddit_obj = reddit.subreddit(subreddit)
            for submission in subreddit_obj.new(limit=limit):
                post = Post(
                    title=submission.title,
                    author=str(submission.author),
                    score=submission.score,
                    url=submission.url,
                    created_utc=submission.created_utc,
                    num_comments=submission.num_comments,
                    selftext=submission.selftext,
                    subreddit=submission.subreddit.display_name,
                    permalink=submission.permalink
                )
                posts.append(post)
            
            print(f"Successfully fetched {len(posts)} posts from r/{subreddit} using authenticated API")
            return posts
            
        except Exception as e:
            print(f"Error using authenticated Reddit API: {e}")
            print("Falling back to anonymous API...")
    else:
        print("Reddit API credentials not found, using anonymous API (may be blocked by Reddit)...")
    
    # Fall back to anonymous API if authentication fails or credentials not provided
    try:
        # Add a random delay to avoid rate limiting
        time.sleep(1 + random.random() * 2)
        
        url = f"https://www.reddit.com/r/{subreddit}/new.json"
        headers = {
            "User-Agent": user_agent,
            # Add more headers to look like a real browser
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        params = {"limit": limit}
        
        # Try different proxies if available (you might want to add these to .env)
        proxy = os.getenv("HTTP_PROXY") 
        proxies = {"http": proxy, "https": proxy} if proxy else None
        
        response = requests.get(url, headers=headers, params=params, proxies=proxies, timeout=10)
        response.raise_for_status()  
        data = response.json()
        
        for item in data["data"]["children"]:
            post_data = item["data"]
            post = Post(
                title=post_data["title"],
                author=post_data["author"],
                score=post_data["score"],
                url=post_data["url"],
                created_utc=post_data["created_utc"],
                num_comments=post_data["num_comments"],
                selftext=post_data.get("selftext", ""),
                subreddit=post_data["subreddit"],
                permalink=post_data["permalink"]
            )
            posts.append(post)
        
        print(f"Successfully fetched {len(posts)} posts from r/{subreddit} using anonymous API")
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred fetching from r/{subreddit}: {e}")
    
    return posts


def filter_posts_with_gemini(posts: List[Post], filter_criteria: str) -> List[tuple[Post, str]]:
    """
    Filter posts using Gemini model via OpenRouter.
    Returns a list of (post, reason) tuples for posts that pass the filter.
    """
    filtered_posts = []
    
    # Get the OpenRouter API key
    openrouter_key = os.getenv("OPENROUTER_KEY")
    if not openrouter_key:
        print("Error: OPENROUTER_KEY not found in .env file")
        return filtered_posts
        
    # Initialize the OpenAI client with OpenRouter configuration
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_key,
    )
    
    for post in posts:
        post_content = f"""
        Title: {post.title}
        Subreddit: r/{post.subreddit}
        Content: {post.selftext if post.selftext else '[No content]'}
        """
        
        prompt = f"""
        {filter_criteria}
        
        Post details:
        {post_content}
        
        First, answer with just YES or NO. 
        Then, if YES, provide a one-sentence explanation of why this post matches the criteria.
        Format your answer exactly like this example:
        YES
        This post describes a specific pain point that could be addressed with a SaaS solution.
        
        Or if it doesn't match:
        NO
        """
        
        try:
            # Print debug info for the first post
            if posts.index(post) == 0:
                print(f"Using OpenRouter API key: {openrouter_key[:5]}...{openrouter_key[-4:]}")
                print("Attempting to call OpenRouter API...")
            
            # Make the API call
            completion = client.chat.completions.create(
                model="google/gemini-2.0-flash-001",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response = completion.choices[0].message.content.strip()
            
            # Parse the response to get the decision and reason
            lines = response.split('\n', 1)
            decision = lines[0].strip().upper()
            
            if decision == "YES" and len(lines) > 1:
                reason = lines[1].strip()
                filtered_posts.append((post, reason))
                print(f"✅ Accepted post: {post.title}")
            else:
                print(f"❌ Rejected post: {post.title}")
                
        except Exception as e:
            print(f"Error filtering post {post.title}: {e}")
    
    return filtered_posts


def build_html_report(filtered_posts: List[tuple[Post, str]]) -> str:
    """Build an HTML report of filtered posts."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reddit Idea Filter Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }}
            h1 {{
                color: #ff4500;
                border-bottom: 2px solid #ff4500;
                padding-bottom: 10px;
            }}
            .post {{
                margin-bottom: 30px;
                padding: 15px;
                border-radius: 5px;
                background-color: #f9f9f9;
                border-left: 4px solid #ff4500;
            }}
            .subreddit {{
                color: #0079d3;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .title {{
                font-size: 1.2em;
                margin: 5px 0;
            }}
            .title a {{
                color: #1a1a1b;
                text-decoration: none;
            }}
            .title a:hover {{
                text-decoration: underline;
            }}
            .age {{
                color: #787c7e;
                font-size: 0.9em;
            }}
            .reason {{
                margin-top: 10px;
                font-style: italic;
                color: #4a4a4a;
            }}
            .summary {{
                margin-top: 20px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <h1>Reddit Idea Filter Report</h1>
        <p>Generated on: {timestamp}</p>
        
        <div class="summary">
            <p>Found {len(filtered_posts)} posts matching your filter criteria.</p>
        </div>
    """
    
    for post, reason in filtered_posts:
        html += f"""
        <div class="post">
            <div class="subreddit">r/{post.subreddit}</div>
            <div class="title">
                <a href="{post.get_full_url()}" target="_blank">
                    {post.title} <span class="age">({post.get_age_str()})</span>
                </a>
            </div>
            <div class="reason">{reason}</div>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    return html


def send_email(recipient: str, subject: str, html_content: str):
    """Send an email with the HTML report."""
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender_email = os.getenv("SENDER_EMAIL", smtp_username)
    
    if not all([smtp_username, smtp_password, sender_email, recipient]):
        print("Email configuration is incomplete. Check your .env file.")
        return False
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient
    
    # Attach HTML content
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {recipient}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def main():
    """Main function to run the Reddit idea filter."""
    # Validate environment variables first
    if not validate_env_variables():
        return
    
    subreddits = [
        "RealEstateTechnology", 
        "PropTech",
        "HealthTech",
        "EdTech"
    ]
    
    filter_criteria = "Does the post include a user posing a question, asking for reccomendation or about the existence of some software that could lay the groundwork for a startup. For example, a user might ask others if they've used AI for generating leads, or if they've had any luck using AI for product photography. The user should NOT be promoting their own existing company. Exclude posts that simply ask a question about an existing technology."
    
    # Check for email configuration if we want to send emails
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    if not recipient_email:
        print("WARNING: Recipient email not configured. Email functionality will be disabled.")
        print("Add RECIPIENT_EMAIL to your .env file to enable email reports.")
    
    # Collect posts from all subreddits
    all_posts = []
    for subreddit in subreddits:
        print(f"Fetching posts from r/{subreddit}...")
        posts = fetch_new_posts(subreddit, limit=10)
        all_posts.extend(posts)
        print(f"Found {len(posts)} posts in r/{subreddit}")
    
    print(f"Total posts collected: {len(all_posts)}")
    
    if not all_posts:
        print("No posts were collected. Check your internet connection or Reddit API access.")
        return
    
    # Filter posts using Gemini
    print("Filtering posts with Gemini...")
    filtered_post_tuples = filter_posts_with_gemini(all_posts, filter_criteria)
    
    print(f"Posts that passed the filter: {len(filtered_post_tuples)}")
    
    if filtered_post_tuples:
        # Build HTML report
        html_report = build_html_report(filtered_post_tuples)
        
        # Send email if configured
        if recipient_email:
            subject = f"Reddit Idea Filter Report - {datetime.now().strftime('%Y-%m-%d')}"
            if send_email(recipient_email, subject, html_report):
                print(f"Email report sent to {recipient_email}")
            else:
                print("Failed to send email report. Check your email configuration.")
        else:
            print("No recipient email configured, so the report was not sent.")
            print("To see the report, add RECIPIENT_EMAIL to your .env file.")
    else:
        print("No posts matched your filter criteria.")


if __name__ == "__main__":
    main() 