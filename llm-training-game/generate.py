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

def process_literal_file(file_path, single_token=False, model_completions=True):
    """Process a literal file where each line has format 'prefix|answer'"""
    print(f"Processing literal file: {file_path}")
    samples = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # First, validate the entire file
        print("Validating file format and token counts...")
        valid_problems = []
        enc = tiktoken.get_encoding("gpt2")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or '|' not in line:
                print(f"Skipping line {i+1}: Invalid format (no '|' separator)")
                continue
                
            # Split by the first '|' character
            parts = line.split('|', 1)
            if len(parts) != 2:
                print(f"Skipping line {i+1}: Invalid format (wrong number of parts)")
                continue
                
            prefix = parts[0]
            answer = parts[1]
            
            # Check if answer is a single token, if required
            if single_token:
                answer_tokens = enc.encode(answer)
                if len(answer_tokens) != 1:
                    print(f"Error on line {i+1}: Answer '{answer}' is not a single token (it's {len(answer_tokens)} tokens)")
                    exit(1)
            
            valid_problems.append((prefix, answer))
        
        print(f"Validation complete. Found {len(valid_problems)} valid problems.")
        
        # Now generate predictions for each valid problem
        for i, (prefix, answer) in enumerate(valid_problems):
            print(f"Processing problem {i+1}/{len(valid_problems)}: {prefix}")
            
            # Create a sample with one step
            sample = {
                "article_title": f"Problem {i+1}",
                "sample_words": [prefix, answer],  # Just for reference
                "steps": [{
                    "prefix": prefix,
                    "next_actual_token": answer,
                }]
            }
            
            # Add model predictions if requested
            if model_completions:
                sample["steps"][0]["predictions"] = {
                    "gpt2": get_gpt2_predictions(prefix),
                    "llama3": get_llama3_predictions(prefix)
                }
            
            samples.append(sample)
            
            # Small delay to avoid rate limiting
            time.sleep(1)
            
        return samples
    except Exception as e:
        print(f"Error processing literal file: {e}")
        exit(1)

def generate_step_data(words, prefix_size, model_completions=True):
    """Generate prediction data for a single step"""
    prefix = ''.join(words[:prefix_size])
    
    result = {
        "prefix": prefix,
        "next_actual_token": words[prefix_size] if prefix_size < len(words) else "END",
    }
    
    # Add model predictions if requested
    if model_completions:
        result["predictions"] = {
            "gpt2": get_gpt2_predictions(prefix),
            "llama3": get_llama3_predictions(prefix),
            # "llama2": get_llama2_predictions(prefix)
        }
    
    return result

def get_text_from_file(file_path):
    """Read text from a file"""
    print(f"Reading text from file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return {
            'title': os.path.basename(file_path),
            'text': text
        }
    except Exception as e:
        print(f"Error reading file: {e}")
        exit(1)

def generate_sample_data(num_samples=10, steps_per_sample=10, min_sample_length=40, file_path=None, mode=None, single_token=False, model_completions=True):
    """Generate data for multiple samples with multiple steps each"""
    
    # Special handling for literal mode
    if mode == 'literal' and file_path:
        return process_literal_file(file_path, single_token, model_completions)
    
    all_samples = []
    
    for i in tqdm(range(num_samples), desc="Generating samples"):
        # Get text either from file or Wikipedia
        if file_path:
            # For file input, we only get the text once and create multiple samples from it
            if i == 0:
                article = get_text_from_file(file_path)
                full_text = article['text']
            
            # For each sample, get a different portion of the text
            article_text = full_text
            article = {'title': f"{os.path.basename(file_path)} (section {i+1})", 'text': article_text}
        else:
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
                
            step_data = generate_step_data(sample_words, prefix_size, model_completions)
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
    parser = argparse.ArgumentParser(description='Generate model prediction data from Wikipedia articles or a text file')
    parser.add_argument('--num_samples', type=int, default=10, help='Number of samples to generate')
    parser.add_argument('--steps_per_sample', type=int, default=10, help='Number of steps per sample')
    parser.add_argument('--output', type=str, default='prediction_data.json', help='Output JSON file')
    parser.add_argument('--file', type=str, help='Path to a text file to use instead of Wikipedia articles')
    parser.add_argument('--mode', type=str, choices=['wiki', 'file', 'literal'], default='wiki', 
                        help='Mode to use: wiki (default), file (text file), or literal (problems with answers)')
    parser.add_argument('--single_token', action='store_true', help='In literal mode, require answers to be a single token')
    parser.add_argument('--no-model-completions', dest='model_completions', action='store_false', 
                        help='Skip generating model completions for steps')
    parser.set_defaults(model_completions=True)
    args = parser.parse_args()
    
    # Validate arguments
    if args.mode == 'literal' and not args.file:
        print("Error: --file argument is required when using --mode=literal")
        exit(1)
    
    if args.mode == 'file' and not args.file:
        print("Error: --file argument is required when using --mode=file")
        exit(1)
    
    # Set file path based on mode
    file_path = args.file if args.mode in ['file', 'literal'] else None
    
    # Determine source text description
    if args.mode == 'wiki':
        source_text = "Wikipedia articles"
    elif args.mode == 'file':
        source_text = f"text from {args.file}"
    else:  # literal mode
        source_text = f"problems from {args.file}"
    
    print(f"Generating data from {source_text}...")
    data = generate_sample_data(
        args.num_samples, 
        args.steps_per_sample, 
        file_path=file_path, 
        mode=args.mode,
        single_token=args.single_token,
        model_completions=args.model_completions
    )
    
    # Save to JSON file
    with open(args.output, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Data saved to {args.output}")
    print(f"Total samples: {len(data)}")
    print(f"Total steps: {sum(len(sample['steps']) for sample in data)}")

if __name__ == "__main__":
    main() 