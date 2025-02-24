import requests
from bs4 import BeautifulSoup
import random
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch.nn.functional as F
import torch
import tiktoken

# Initialize the models and tokenizers at the top level
gpt2_model = AutoModelForCausalLM.from_pretrained('gpt2')
gpt2_tokenizer = AutoTokenizer.from_pretrained('gpt2')
# llama_model = AutoModelForCausalLM.from_pretrained('meta-llama/Llama-2-70b-hf')
# llama_tokenizer = AutoTokenizer.from_pretrained('meta-llama/Llama-2-70b-hf')
enc = tiktoken.get_encoding("gpt2")

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

def get_random_text_sample(text, minimum_sample_length=20):
    # Tokenize text using tiktoken and convert back to strings
    tokens = enc.encode(text)
    words = [enc.decode([token]) for token in tokens]
    
    if len(words) > minimum_sample_length:
        max_start_index = len(words) - minimum_sample_length
        start_index = random.randint(0, max_start_index)
    else:
        start_index = 0
    
    return words[start_index:]

# Example usage
if __name__ == "__main__":
    article = get_random_wikipedia_article()
    # print(f"Title: {article['title']}\n")
    
    sample = get_random_text_sample(article['text'])
    prompt = ''.join(sample[:10])  # Join with empty string instead of space
    
    print("Original text:", prompt)
    
    # Get GPT-2 predictions
    inputs = gpt2_tokenizer(prompt, return_tensors='pt')
    with torch.no_grad():
        outputs = gpt2_model(**inputs)
        logits = outputs.logits[0, -1, :]
    probs = F.softmax(logits, dim=-1)
    top_probs, top_indices = torch.topk(probs, 5)
    
    print("\nGPT-2:")
    for prob, idx in zip(top_probs, top_indices):
        token = gpt2_tokenizer.decode(idx)
        print(f"{prob:.3f}: {token}")
    
    # # Get Llama-2 predictions
    # inputs = llama_tokenizer(prompt, return_tensors='pt')
    # with torch.no_grad():
    #     outputs = llama_model(**inputs)
    #     logits = outputs.logits[0, -1, :]
    # probs = F.softmax(logits, dim=-1)
    # top_probs, top_indices = torch.topk(probs, 5)
    
    # print("\nLlama-2:")
    # for prob, idx in zip(top_probs, top_indices):
    #     token = llama_tokenizer.decode(idx)
    #     print(f"{prob:.3f}: {token}")
