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

def get_random_text_sample(text, minimum_sample_length=10):
    # Split text into words and get random starting point
    words = text.split()
    
    if len(words) > minimum_sample_length:
        max_start_index = len(words) - minimum_sample_length
        start_index = random.randint(0, max_start_index)
    else:
        start_index = 0
    
    # Get the sample starting from start_index
    sample = words[start_index:]
    return sample

# Example usage
if __name__ == "__main__":
    article = get_random_wikipedia_article()
    print(f"Title: {article['title']}\n")
    
    sample = get_random_text_sample(article['text'])
    sample_text = ' '.join(sample[:10])
    print(sample_text + "...")
