# AI News Agent

This is an autonomous agent that gathers the latest news on user-specified AI topics, learns user preferences over time, and delivers a personalized news brief via email.

## Features

- **Automated News Gathering**: Fetches recent articles from preferred, high-quality sources using the NewsAPI.
- **Content Parsing**: Extracts the clean, primary text from article URLs.
- **Personalized Learning**:
    - **Topic Prioritization**: Learns which topics you find most interesting based on a 1-5 rating system and re-prioritizes future searches accordingly.
    - **Keyword Weighting**: Analyzes the content of articles you like and dislike to identify positive and negative keywords, further refining future searches.
- **Automated Email Delivery**: Securely sends the generated report to your Gmail address using the Gmail API and OAuth 2.0.
- **Extensible Summarization**: Includes a clearly marked placeholder to integrate with any summarization provider (e.g., Cohere, OpenAI, local models).
- **Scheduled Execution**: Can be configured with `cron` to run automatically on a schedule (e.g., weekly).

## Project Structure

```
AI_News_Agent/
│
├── agent.py              # The main script for the agent.
├── config.json           # Configuration file for topics, sources, and learned weights.
├── credentials.json      # Your Google Cloud OAuth 2.0 credentials (DO NOT COMMIT).
├── token.json            # Generated token for Gmail API access (DO NOT COMMIT).
├── feedback.txt          # Simulated user feedback for non-interactive runs.
├── ratings.json          # Stores the ratings provided by the user.
├── report.md             # The generated Markdown report.
├── requirements.txt      # Python dependencies.
└── agent.log             # Log file for the scheduled cron job.
```

## Setup and Usage

### 1. Prerequisites

- Python 3.x
- A Google Cloud Platform project with the Gmail API enabled.
- A NewsAPI.org account for a free developer API key.

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/crizzo71/AI_Brief.git
    cd AI_Brief
    ```

2.  **Install dependencies:**
    ```bash
    python3 -m pip install -r requirements.txt
    ```

### 3. Configuration

1.  **Google Credentials**:
    - Follow the Google Cloud instructions to create OAuth 2.0 credentials for a "Desktop app".
    - Download the JSON file and rename it to `credentials.json` in the project directory.

2.  **NewsAPI Key**:
    - Get your API key from [NewsAPI.org](https://newsapi.org/).
    - Set it as an environment variable:
      ```bash
      export NEWS_API_KEY="your_news_api_key_here"
      ```

3.  **Agent Configuration (`config.json`)**:
    - `user_email`: Set the email address where you want to receive the report.
    - `search_topics`: Modify the list of AI topics to search for.
    - `preferred_sources`: Update the list of news source domains.

### 4. First Run and Authorization

The first time you run the agent, you will need to authorize it to use your Gmail account.

```bash
python3 agent.py
```

A browser window will open. Follow the prompts to grant the application permission. This will create a `token.json` file that will be used for authentication on subsequent runs.

### 5. Summarization (Customization)

Open `agent.py` and navigate to the `process_article` function. Replace the placeholder block with a call to your preferred LLM summarization service. The clean article text is available in the `article.text` variable.

### 6. Automated Execution (Optional)

To run the agent automatically (e.g., every Friday at 9 AM), you can set up a cron job.

1.  Open your crontab: `crontab -e`
2.  Add the following line, making sure to replace the placeholder API key and verify the Python path (`which python3`):

    ```
    0 9 * * 5 cd /path/to/your/AI_News_Agent && NEWS_API_KEY="your_news_api_key_here" /usr/bin/python3 agent.py >> agent.log 2>&1
    ```

## Security

- The script uses Google's recommended OAuth 2.0 flow to securely access your Gmail account without storing your password.
- Your NewsAPI key is loaded from an environment variable to avoid hardcoding it in the script.
- **Important**: Remember to add `credentials.json` and `token.json` to your `.gitignore` file to prevent committing sensitive information to your repository.
