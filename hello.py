import requests
from bs4 import BeautifulSoup
import random
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch.nn.functional as F
import torch

# Initialize the model and tokenizer at the top level
model = AutoModelForCausalLM.from_pretrained('gpt2')
tokenizer = AutoTokenizer.from_pretrained('gpt2')

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
    return words[start_index:]

# Example usage
if __name__ == "__main__":
    article = get_random_wikipedia_article()
    # print(f"Title: {article['title']}\n")
    
    sample = get_random_text_sample(article['text'])
    prompt = ' '.join(sample[:5])
    
    # Tokenize the prompt
    inputs = tokenizer(prompt, return_tensors='pt')
    
    # Get model output
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits[0, -1, :]  # Get logits for the last position
        
    # Convert logits to probabilities
    probs = F.softmax(logits, dim=-1)
    
    # Get top 5 tokens and their probabilities
    top_probs, top_indices = torch.topk(probs, 5)
    
    print("Original text:", prompt)
    print("\nGPT-2:")
    for prob, idx in zip(top_probs, top_indices):
        token = tokenizer.decode(idx)
        print(f"{prob:.3f}: {token}")
