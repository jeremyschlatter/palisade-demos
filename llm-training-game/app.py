import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch.nn.functional as F
import torch
import tiktoken
import os
import openai
import time
import threading

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Set page config
st.set_page_config(
    page_title="LLM Training Game",
    page_icon="🤖",
    layout="wide",
)

# Initialize Hyperbolic client
@st.cache_resource
def get_hyperbolic_client():
    return openai.OpenAI(
        api_key=os.getenv('HYPERBOLIC_API_KEY'),
        base_url="https://api.hyperbolic.xyz/v1",
    )

hyperbolic_client = get_hyperbolic_client()

# Cache GPT-2 model to avoid reloading
@st.cache_resource
def load_gpt2_model():
    return AutoModelForCausalLM.from_pretrained('gpt2')

@st.cache_resource
def load_gpt2_tokenizer():
    return AutoTokenizer.from_pretrained('gpt2')

def get_random_wikipedia_article():
    # URL for random Wikipedia article
    url = "https://en.wikipedia.org/wiki/Special:Random"

    # Send request and get response
    with st.spinner("Fetching random Wikipedia article..."):
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
    with st.spinner("Getting GPT-2 predictions..."):
        gpt2_model = load_gpt2_model()
        gpt2_tokenizer = load_gpt2_tokenizer()
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
        # Llama-2 code would go here
    except Exception as e:
        results["predictions"]["llama2"] = [{"error": str(e)}]
    
    # Get Llama 3.1 predictions
    try:
        with st.spinner("Getting Llama 3.1 predictions..."):
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

def precompute_steps(words, start_prefix_size, num_steps=10):
    """Precompute multiple steps and cache the results"""
    results = {}
    for i in range(num_steps):
        current_prefix_size = start_prefix_size + i
        if current_prefix_size < len(words):
            results[current_prefix_size] = step(words, current_prefix_size)
    return results

def background_precompute(words, start_prefix_size, num_steps=10):
    """Run precomputation in background and update session state when done"""
    results = precompute_steps(words, start_prefix_size, num_steps)
    # Update the session state with the precomputed results
    st.session_state.cached_steps.update(results)
    st.session_state.precomputing = False

# Initialize session state
if 'article' not in st.session_state:
    st.session_state.article = get_random_wikipedia_article()
    st.session_state.sample = get_random_text_sample(st.session_state.article['text'], minimum_sample_length=40)
    st.session_state.prefix_size = 10
    st.session_state.show_predictions = False
    st.session_state.show_actual = False
    st.session_state.step_results = None
    st.session_state.cached_steps = {}
    st.session_state.precomputing = False

# Start precomputation if needed
if not st.session_state.precomputing and len(st.session_state.cached_steps) < 5:
    st.session_state.precomputing = True
    start_prefix = max(st.session_state.prefix_size, max(st.session_state.cached_steps.keys()) + 1) if st.session_state.cached_steps else st.session_state.prefix_size
    threading.Thread(target=background_precompute, args=(st.session_state.sample, start_prefix, 10)).start()

# Display cache status (for debugging, can be removed in production)
cache_status = f"Cached steps: {len(st.session_state.cached_steps)} steps ahead"
st.sidebar.write(cache_status)
if st.sidebar.button("Force Precompute"):
    st.session_state.precomputing = True
    start_prefix = st.session_state.prefix_size
    threading.Thread(target=background_precompute, args=(st.session_state.sample, start_prefix, 10)).start()
    st.rerun()

# Display article title in sidebar
st.sidebar.markdown(f"### Article: {st.session_state.article['title']}")

# Display current prefix with better styling
prefix_text = ''.join(st.session_state.sample[:st.session_state.prefix_size])
st.markdown("### What comes next?")
st.markdown(f"""
<div style="
    border: 2px solid grey;
    border-radius: 5px;
    padding: 15px;
    font-family: monospace;
    font-size: 16px;
    margin-bottom: 20px;
    white-space: pre-wrap;
">
{prefix_text}
</div>
""", unsafe_allow_html=True)

# Buttons for interaction
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Show/Hide Predictions", type="primary"):
        st.session_state.show_predictions = not st.session_state.show_predictions
        # Use cached results if available, otherwise compute
        if st.session_state.prefix_size in st.session_state.cached_steps:
            st.session_state.step_results = st.session_state.cached_steps[st.session_state.prefix_size]
        else:
            st.session_state.step_results = step(st.session_state.sample, st.session_state.prefix_size)

with col2:
    if st.button("Reveal Next Token & Advance", type="secondary"):
        # Use cached results if available, otherwise compute
        if st.session_state.prefix_size in st.session_state.cached_steps:
            st.session_state.step_results = st.session_state.cached_steps[st.session_state.prefix_size]
        else:
            st.session_state.step_results = step(st.session_state.sample, st.session_state.prefix_size)
        st.session_state.show_actual = True

with col3:
    if st.button("New Article"):
        st.session_state.article = get_random_wikipedia_article()
        st.session_state.sample = get_random_text_sample(st.session_state.article['text'], minimum_sample_length=40)
        st.session_state.prefix_size = 10
        st.session_state.show_predictions = False
        st.session_state.show_actual = False
        st.session_state.step_results = None
        st.session_state.cached_steps = {}
        st.session_state.precomputing = False
        st.rerun()

# Get predictions if needed
if st.session_state.show_predictions and not st.session_state.step_results:
    # Use cached results if available, otherwise compute
    if st.session_state.prefix_size in st.session_state.cached_steps:
        st.session_state.step_results = st.session_state.cached_steps[st.session_state.prefix_size]
    else:
        st.session_state.step_results = step(st.session_state.sample, st.session_state.prefix_size)

# Show predictions if toggled
if st.session_state.show_predictions and st.session_state.step_results:
    st.markdown("### Model Predictions")
    
    # Create columns for each model
    col1, col2 = st.columns(2)
    
    # GPT-2
    with col1:
        st.markdown("#### GPT-2")
        for pred in st.session_state.step_results["predictions"]["gpt2"]:
            st.markdown(f"**{pred['probability']:.3f}:** `{pred['token']}`")
    
    # Llama 3.1
    with col2:
        st.markdown("#### Llama 3.1")
        if "llama3" in st.session_state.step_results["predictions"]:
            for pred in st.session_state.step_results["predictions"]["llama3"]:
                if "error" in pred:
                    st.error(f"Error: {pred['error']}")
                else:
                    st.markdown(f"**{pred['probability']:.3f}:** `{pred['token']}`")
        else:
            st.write("Not available")

# Show actual next token if revealed
if st.session_state.show_actual and st.session_state.step_results:
    st.markdown("### Actual Next Token")
    st.markdown(f"## `{st.session_state.step_results['next_actual_token']}`")
    
    # Advance after showing
    if st.button("Continue to Next Token"):
        st.session_state.prefix_size += 1
        st.session_state.show_actual = False
        
        # Use cached results for the next step if available
        if st.session_state.prefix_size in st.session_state.cached_steps:
            st.session_state.step_results = st.session_state.cached_steps[st.session_state.prefix_size]
        else:
            st.session_state.step_results = None
            
        # Trigger precomputation if cache is getting low
        if not st.session_state.precomputing and len(st.session_state.cached_steps) < 5:
            st.session_state.precomputing = True
            start_prefix = max(st.session_state.prefix_size, max(st.session_state.cached_steps.keys()) + 1) if st.session_state.cached_steps else st.session_state.prefix_size
            threading.Thread(target=background_precompute, args=(st.session_state.sample, start_prefix, 10)).start()
            
        st.rerun()

# Add some styling
st.markdown("""
<style>
    .stTextArea textarea {
        font-family: monospace;
        font-size: 16px;
    }
    
    .stMarkdown code {
        font-size: 18px;
        padding: 2px 5px;
        background-color: #f0f0f0;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)