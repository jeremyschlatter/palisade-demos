import requests
from bs4 import BeautifulSoup
import random
from transformers import AutoModelForCausalLM, AutoTokenizer
import ctransformers
import torch.nn.functional as F
import torch
import tiktoken
import os
import openai
import json
import time
from tqdm import tqdm
import argparse

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Initialize Hyperbolic client
def get_hyperbolic_client():
    return openai.OpenAI(
        api_key=os.getenv('HYPERBOLIC_API_KEY'),
        base_url="https://api.hyperbolic.xyz/v1",
    )

hyperbolic_client = get_hyperbolic_client()

gpt2_model = AutoModelForCausalLM.from_pretrained('gpt2')
gpt2_tokenizer = AutoTokenizer.from_pretrained('gpt2')

# llama2_model = ctransformers.AutoModelForCausalLM.from_pretrained('TheBloke/Llama-2-70B-GGUF', model_file='llama-2-70b.Q5_K_M.gguf', model_type='llama')
# llama2_tokenizer = ctransformers.AutoTokenizer.from_pretrained('TheBloke/Llama-2-70B-GGUF', model_file='llama-2-70b.Q5_K_M.gguf')

def get_random_wikipedia_article():
    """Fetch a random Wikipedia article"""
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
    """Extract a random sample from text using GPT-2 tokenization"""
    enc = tiktoken.get_encoding("gpt2")
    tokens = enc.encode(text)
    words = [enc.decode([token]) for token in tokens]
    
    if len(words) > minimum_sample_length:
        max_start_index = len(words) - minimum_sample_length
        start_index = random.randint(0, max_start_index)
    else:
        start_index = 0
    
    return words[start_index:]

def get_hf_predictions(prefix, top_k=5, name=None, model=None, tokenizer=None):
    """Get top-k predictions from GPT-2"""
    print(f"Getting {name} predictions for prefix: {prefix}")
    inputs = tokenizer(prefix, return_tensors='pt')
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits[0, -1, :]
    probs = F.softmax(logits, dim=-1)
    top_probs, top_indices = torch.topk(probs, top_k)
    
    predictions = []
    for prob, idx in zip(top_probs, top_indices):
        token = tokenizer.decode(idx)
        predictions.append({"token": token, "probability": prob.item()})
    
    return predictions

def get_gpt2_predictions(prefix, top_k=5):
    return get_hf_predictions(prefix, top_k, 'gpt2', gpt2_model, gpt2_tokenizer)

def get_llama2_predictions(prefix, top_k=5):
    return get_hf_predictions(prefix, top_k, 'llama2', llama2_model, llama2_tokenizer)

def get_llama3_predictions(prefix, top_k=5):
    """Get top-k predictions from Llama 3.1"""
    print(f"Getting Llama 3.1 predictions for prefix: {prefix}")
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
        
        predictions = []
        for token, logprob in sorted_logprobs[:top_k]:
            if logprob > -9999:  # Skip the placeholder values
                prob = torch.exp(torch.tensor(logprob)).item()
                predictions.append({"token": token, "probability": prob})
        
        return predictions
    except Exception as e:
        return [{"error": str(e)}]

def generate_step_data(words, prefix_size):
    """Generate prediction data for a single step"""
    prefix = ''.join(words[:prefix_size])
    
    result = {
        "prefix": prefix,
        "next_actual_token": words[prefix_size] if prefix_size < len(words) else "END",
        "predictions": {
            "gpt2": get_gpt2_predictions(prefix),
            "llama3": get_llama3_predictions(prefix),
            # "llama2": get_llama2_predictions(prefix)
        }
    }
    
    # Uncomment to add Llama-2 predictions if available
    # result["predictions"]["llama2"] = get_llama2_predictions(prefix)
    
    return result

def generate_sample_data(num_samples=10, steps_per_sample=10, min_sample_length=40):
    """Generate data for multiple samples with multiple steps each"""
    all_samples = []
    
    for i in tqdm(range(num_samples), desc="Generating samples"):
        # Get a random Wikipedia article
        article = get_random_wikipedia_article()
        
        # Get a random text sample
        sample_words = get_random_text_sample(article['text'], minimum_sample_length=min_sample_length)
        
        # Generate steps for this sample
        steps = []
        for step_idx in tqdm(range(steps_per_sample), desc=f"Sample {i+1} steps", leave=False):
            prefix_size = 10 + step_idx  # Start with 10 tokens and advance
            
            # Make sure we don't go beyond the sample length
            if prefix_size >= len(sample_words):
                break
                
            step_data = generate_step_data(sample_words, prefix_size)
            steps.append(step_data)
        
        # Add sample data
        sample_data = {
            "article_title": article['title'],
            "sample_words": sample_words,
            "steps": steps
        }
        
        all_samples.append(sample_data)
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    return all_samples

def main():
    parser = argparse.ArgumentParser(description='Generate model prediction data from Wikipedia articles')
    parser.add_argument('--num_samples', type=int, default=10, help='Number of Wikipedia samples to generate')
    parser.add_argument('--steps_per_sample', type=int, default=10, help='Number of steps per sample')
    parser.add_argument('--output', type=str, default='prediction_data.json', help='Output JSON file')
    args = parser.parse_args()
    
    print(f"Generating {args.num_samples} samples with {args.steps_per_sample} steps each...")
    data = generate_sample_data(args.num_samples, args.steps_per_sample)
    
    # Save to JSON file
    with open(args.output, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Data saved to {args.output}")
    print(f"Total samples: {len(data)}")
    print(f"Total steps: {sum(len(sample['steps']) for sample in data)}")

if __name__ == "__main__":
    main() 