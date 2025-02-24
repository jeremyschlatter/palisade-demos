import requests
from bs4 import BeautifulSoup
import random
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch.nn.functional as F
import torch
import tiktoken
import os
import openai

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Initialize Hyperbolic client
hyperbolic_client = openai.OpenAI(
    api_key=os.getenv('HYPERBOLIC_API_KEY'),
    base_url="https://api.hyperbolic.xyz/v1",
)

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
    enc = tiktoken.get_encoding("gpt2")
    tokens = enc.encode(text)
    words = [enc.decode([token]) for token in tokens]
    
    if len(words) > minimum_sample_length:
        max_start_index = len(words) - minimum_sample_length
        start_index = random.randint(0, max_start_index)
    else:
        start_index = 0
    
    return words[start_index:]

def step(words, prefix_size):
    """
    Generate next token predictions from different models based on a prefix of words.
    
    Args:
        words: List of tokens/words
        prefix_size: Number of tokens to use as prefix
    
    Returns:
        Dictionary containing predictions from each model
    """
    # Create the prompt from the prefix
    prefix = ''.join(words[:prefix_size])
    
    results = {
        "prefix": prefix,
        "next_actual_token": words[prefix_size] if prefix_size < len(words) else "END",
        "predictions": {}
    }
    
    # Get GPT-2 predictions
    gpt2_model = AutoModelForCausalLM.from_pretrained('gpt2')
    gpt2_tokenizer = AutoTokenizer.from_pretrained('gpt2')
    inputs = gpt2_tokenizer(prefix, return_tensors='pt')
    with torch.no_grad():
        outputs = gpt2_model(**inputs)
        logits = outputs.logits[0, -1, :]
    probs = F.softmax(logits, dim=-1)
    top_probs, top_indices = torch.topk(probs, 5)
    
    gpt2_predictions = []
    for prob, idx in zip(top_probs, top_indices):
        token = gpt2_tokenizer.decode(idx)
        gpt2_predictions.append({"token": token, "probability": prob.item()})
    
    results["predictions"]["gpt2"] = gpt2_predictions
    
    # Get Llama-2 predictions
    try:
        raise Exception('not implemented')
        llama_model = AutoModelForCausalLM.from_pretrained('meta-llama/Llama-2-70b-hf')
        llama_tokenizer = AutoTokenizer.from_pretrained('meta-llama/Llama-2-70b-hf')
        inputs = llama_tokenizer(prefix, return_tensors='pt')
        with torch.no_grad():
            outputs = llama_model(**inputs)
            logits = outputs.logits[0, -1, :]
        probs = F.softmax(logits, dim=-1)
        top_probs, top_indices = torch.topk(probs, 5)
        
        llama2_predictions = []
        for prob, idx in zip(top_probs, top_indices):
            token = llama_tokenizer.decode(idx)
            llama2_predictions.append({"token": token, "probability": prob.item()})
        
        results["predictions"]["llama2"] = llama2_predictions
    except Exception as e:
        results["predictions"]["llama2"] = [{"error": str(e)}]
    
    # Get Llama 3.1 predictions
    try:
        chat_completion = hyperbolic_client.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-FP8",
            prompt=prefix,
            temperature=0,
            top_p=1,
            max_tokens=1,
            logprobs=5,
        )
        
        logprobs = chat_completion.choices[0].logprobs.top_logprobs[0]
        
        # Sort by logprob values (highest first)
        sorted_logprobs = sorted(logprobs.items(), key=lambda x: x[1], reverse=True)
        
        llama3_predictions = []
        for token, logprob in sorted_logprobs:
            if logprob > -9999:  # Skip the placeholder values
                prob = torch.exp(torch.tensor(logprob)).item()
                llama3_predictions.append({"token": token, "probability": prob})
        
        results["predictions"]["llama3"] = llama3_predictions
    except Exception as e:
        results["predictions"]["llama3"] = [{"error": str(e)}]
    
    return results

# Example usage
if __name__ == "__main__":
    article = get_random_wikipedia_article()
    
    sample = get_random_text_sample(article['text'], minimum_sample_length=30)
    
    # Take 3 steps, starting with a prefix of 10 tokens
    prefix_size = 10
    for i in range(3):
        print(f"\n--- Step {i+1} ---")
        print(f"Prefix: {''.join(sample[:prefix_size])}")
        
        # Get predictions
        step_results = step(sample, prefix_size)
        
        # Print predictions
        print("\nGPT-2 predictions:")
        for pred in step_results["predictions"]["gpt2"]:
            print(f"{pred['probability']:.3f}: {pred['token']}")
        
        print("\nLlama-2 predictions:")
        if "llama2" in step_results["predictions"]:
            for pred in step_results["predictions"]["llama2"]:
                if "error" in pred:
                    print(f"Error: {pred['error']}")
                else:
                    print(f"{pred['probability']:.3f}: {pred['token']}")
        else:
            print("Not available")
        
        print("\nLlama 3.1 predictions:")
        for pred in step_results["predictions"]["llama3"]:
            if "error" in pred:
                print(f"Error: {pred['error']}")
            else:
                print(f"{pred['probability']:.3f}: {pred['token']}")
        
        # Print actual next token
        print(f"\nActual next token: {step_results['next_actual_token']}")
        
        # Increment prefix size for next step
        prefix_size += 1
