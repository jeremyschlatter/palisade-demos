import requests
from bs4 import BeautifulSoup
import random  # Add this import at the top

def get_random_wikipedia_article():
    # URL for random Wikipedia article
    url = "https://en.wikipedia.org/wiki/Special:Random"

    # Send request and get response
    response = requests.get(url)

    # Parse HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Get article title
    title = soup.find(id="firstHeading").text

    # Get main content (excluding references, navigation, etc.)
    content = soup.find(id="mw-content-text")

    # Remove unwanted elements
    for unwanted in content.find_all(['table', 'sup', 'div.thumb', 'span.mw-editsection']):
        unwanted.decompose()

    # Extract text
    text = content.get_text().strip()

    return {
        'title': title,
        'text': text
    }

# Example usage
if __name__ == "__main__":
    article = get_random_wikipedia_article()
    print(f"Title: {article['title']}\n")
    
    # Split text into words and get random starting point
    words = article['text'].split()
    minimum_sample_length = 10
    
    if len(words) > minimum_sample_length:
        max_start_index = len(words) - minimum_sample_length
        start_index = random.randint(0, max_start_index)
    else:
        start_index = 0
    
    # Take up to 10 words from the starting point
    sample_text = ' '.join(words[start_index:start_index + minimum_sample_length])
    print(sample_text + "...")
