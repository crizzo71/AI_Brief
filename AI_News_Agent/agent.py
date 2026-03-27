import json
import os
import base64
import re
import string
import sys
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, Counter

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from newsapi import NewsApiClient
from newspaper import Article, ArticleException

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# --- Keyword Extraction Setup ---
STOP_WORDS = set(['a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', "can't", 'cannot', 'com', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', 'let', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'r', 's', 'same', 'shall', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 't', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'www', 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves'])

def extract_keywords_from_text(text, num_keywords=5):
    """Extracts the most common keywords from a piece of text."""
    text = text.lower()
    text = re.sub(f'[{re.escape(string.punctuation)}]', '', text)
    words = text.split()
    words = [word for word in words if word not in STOP_WORDS and not word.isdigit()]
    return [word for word, _ in Counter(words).most_common(num_keywords)]

# --- Core Agent Functions ---

def load_config():
    """Loads the configuration from config.json."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def save_config(config):
    """Saves the configuration to config.json."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def gather_news_for_topic(topic, newsapi, sources, other_domains, keywords, days):
    """Gathers news articles for a single topic from multiple query types."""
    print(f"Searching for news on: {topic}")
    
    positive_keywords = ' OR '.join([f'"{k}"' for k, w in keywords['positive'].items() if w > 0])
    negative_keywords = ' NOT '.join([f'"{k}"' for k, w in keywords['negative'].items() if w > 0])
    
    base_query = f'"{topic}"'
    if positive_keywords:
        base_query += f' AND ({positive_keywords})'
    if negative_keywords:
        base_query += f' AND (NOT {negative_keywords})'

    from_date = datetime.now() - timedelta(days=days)
    urls = set()

    # Query 1: Search within the official NewsAPI sources
    try:
        source_articles = newsapi.get_everything(
            q=base_query,
            sources=','.join(sources),
            language='en',
            sort_by='relevancy',
            from_param=from_date.strftime('%Y-%m-%d'),
            page_size=5
        )
        for article in source_articles['articles']:
            urls.add(article['url'])
    except Exception as e:
        print(f"Error fetching from NewsAPI sources for {topic}: {e}")

    # Query 2: Search across the other specified domains
    try:
        domain_query = f'{base_query} AND ({ " OR ".join(other_domains) })'
        domain_articles = newsapi.get_everything(
            q=domain_query,
            language='en',
            sort_by='relevancy',
            from_param=from_date.strftime('%Y-%m-%d'),
            page_size=5
        )
        for article in domain_articles['articles']:
            urls.add(article['url'])
    except Exception as e:
        print(f"Error fetching from other domains for {topic}: {e}")

    return {topic: list(urls)}

def gather_news(topics, sources, other_domains, keywords, days=7):
    """Gathers news articles for the given topics in parallel."""
    print(f"Gathering news from the last {days} days...")
    news_api_key = os.getenv('NEWS_API_KEY')
    if not news_api_key:
        print("\n--- NewsAPI key not found ---")
        return {}
        
    newsapi = NewsApiClient(api_key=news_api_key)
    articles = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_topic = {executor.submit(gather_news_for_topic, topic, newsapi, sources, other_domains, keywords, days): topic for topic in topics}
        for future in as_completed(future_to_topic):
            try:
                articles.update(future.result())
            except Exception as e:
                print(f"Error in future result for news gathering: {e}")
    return articles

def process_article(url):
    """Downloads, parses, and prepares an article for summarization."""
    print(f"Processing: {url}")
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        summary = f"Placeholder summary for: {article.title}\n(Full text has been extracted and is ready for summarization)"
        
        return {"url": url, "summary": summary, "text": article.text, "title": article.title}
    except (ArticleException, Exception) as e:
        print(f"Could not process article at {url}. Error: {e}")
        return {"url": url, "summary": "Could not process or summarize this article.", "text": "", "title": ""}

def process_and_summarize_articles(articles):
    """Processes and summarizes the content of the given articles in parallel."""
    print("Processing and summarizing articles...")
    summaries = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        for topic, urls in articles.items():
            if not urls:
                continue
            summaries[topic] = []
            future_to_url = {executor.submit(process_article, url): url for url in urls}
            for future in as_completed(future_to_url):
                try:
                    summaries[topic].append(future.result())
                except Exception as e:
                    print(f"Error processing summary future: {e}")
    return summaries

def generate_report(summaries):
    """Generates a report from the summaries."""
    print("Generating report...")
    report_content = f"# AI News Report - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    for topic, summary_list in summaries.items():
        report_content += f"## {topic}\n\n"
        for item in summary_list:
            if item.get("title"):
                report_content += f"- **Source:** {item['url']}\n"
                report_content += f"  - **Summary:** {item['summary']}\n\n"
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(script_dir, 'report.md')
    with open(report_path, 'w') as f:
        f.write(report_content)
    print(f"Report generated: {report_path}")
    return report_content

def get_feedback(summaries):
    """Gets feedback from the user on the generated report."""
    print("\n--- Reading feedback from feedback.txt ---")
    ratings = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    feedback_path = os.path.join(script_dir, 'feedback.txt')
    if not os.path.exists(feedback_path):
        print("feedback.txt not found. Skipping feedback.")
        return []
    with open(feedback_path, 'r') as f:
        feedback_ratings = [int(line.strip()) for line in f.readlines()]
    
    rating_idx = 0
    for topic, summary_list in summaries.items():
        for item in summary_list:
            if item.get("title"):
                if rating_idx < len(feedback_ratings):
                    rating = feedback_ratings[rating_idx]
                    if rating > 0:
                        ratings.append({"url": item['url'], "rating": rating, "topic": topic, "text": item['text']})
                    print(f"Rated '{item['url']}' with {rating}")
                    rating_idx += 1
                else:
                    break
    return ratings

def save_ratings(ratings):
    """Saves the user's ratings to a file, excluding the large text field."""
    ratings_to_save = [{k: v for k, v in r.items() if k != 'text'} for r in ratings]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ratings_path = os.path.join(script_dir, 'ratings.json')
    with open(ratings_path, 'w') as f:
        json.dump(ratings_to_save, f, indent=2)
    print(f"Ratings saved to {ratings_path}")

def update_config_with_feedback(ratings):
    """Updates the config based on user feedback, including keyword weights."""
    print("\n--- Updating config with feedback ---")
    config = load_config()
    
    if not ratings:
        print("No ratings found. Skipping config update.")
        return
        
    topic_ratings = defaultdict(lambda: {'total': 0, 'count': 0})
    for rating in ratings:
        topic_ratings[rating['topic']]['total'] += rating['rating']
        topic_ratings[rating['topic']]['count'] += 1
    avg_ratings = {topic: data['total'] / data['count'] for topic, data in topic_ratings.items()}
    sorted_topics = sorted(config['search_topics'], key=lambda topic: avg_ratings.get(topic, 0), reverse=True)
    if sorted_topics != config['search_topics']:
        config['search_topics'] = sorted_topics
        print("Search topics have been reordered based on your ratings.")
    else:
        print("Search topics are already in preferred order.")

    print("Updating keyword weights...")
    for rating in ratings:
        if not rating.get('text'):
            continue
        
        keywords = extract_keywords_from_text(rating['text'])
        if rating['rating'] >= 4:
            for kw in keywords:
                config['keyword_weights']['negative'].pop(kw, None)
                config['keyword_weights']['positive'][kw] = config['keyword_weights']['positive'].get(kw, 0) + 1
        elif rating['rating'] <= 2:
            for kw in keywords:
                config['keyword_weights']['positive'].pop(kw, None)
                config['keyword_weights']['negative'][kw] = config['keyword_weights']['negative'].get(kw, 0) + 1
    
    save_config(config)
    print("Config updated with new keyword weights.")

def send_email_with_gmail_api(report_content, recipient_email):
    """Create and send an email using the Gmail API."""
    creds = None
    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(script_dir, 'token.json')
    creds_path = os.path.join(script_dir, 'credentials.json')
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('gmail', 'v1', credentials=creds)
        message = MIMEText(report_content)
        message['to'] = recipient_email
        message['subject'] = f"AI News Report - {datetime.now().strftime('%Y-%m-%d')}"
        create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        print(f"\nEmail sent successfully to {recipient_email}")
    except HttpError as error:
        print(f"An error occurred: {error}")
    except Exception as e:
        print(f"An unexpected error occurred during email sending: {e}")

def main():
    """Main function to run the AI news agent."""
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print("Usage: python3 agent.py [number_of_days]")
            sys.exit(1)
    else:
        days = 7

    config = load_config()
    topics = config.get('search_topics', [])
    sources = config.get('preferred_sources', [])
    other_domains = config.get('other_domains', [])
    keywords = config.get('keyword_weights', {"positive": {}, "negative": {}})
    recipient_email = config.get('user_email')
    
    articles = gather_news(topics, sources, other_domains, keywords, days=days)
    if not articles:
        print("No articles found. Exiting.")
        return
        
    summaries = process_and_summarize_articles(articles)
    report_content = generate_report(summaries)
    
    send_email_with_gmail_api(report_content, recipient_email)
    
    # ratings = get_feedback(summaries)
    # if ratings:
    #     save_ratings(ratings)
    #     update_config_with_feedback(ratings)

if __name__ == "__main__":
    main()
