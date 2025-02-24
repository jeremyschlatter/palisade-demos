import requests
from bs4 import BeautifulSoup
import random
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch.nn.functional as F
import torch
import tiktoken
import os
import openai
import sys
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Button, Static, Header, Footer
from textual.reactive import reactive

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

class NextTokenPredictor(App):
    """A Textual app to predict the next token in a text sequence."""
    
    CSS = """
    #prefix {
        margin: 1 0;
        padding: 1;
        background: $surface;
        border: solid $accent;
        height: auto;
    }
    
    #predictions {
        margin: 1 0;
        padding: 1;
        background: $surface;
        border: solid $accent;
        height: auto;
        display: none;
    }
    
    #predictions.visible {
        display: block;
    }
    
    #actual {
        margin: 1 0;
        padding: 1;
        background: $surface;
        border: solid $accent;
        height: auto;
        display: none;
    }
    
    #actual.visible {
        display: block;
    }
    
    Button {
        margin: 1 1;
    }
    
    .model-name {
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    
    #title {
        background: $boost;
        color: $text;
        padding: 1;
        text-align: center;
        text-style: bold;
    }
    
    Footer {
        background: $boost;
        color: $text;
    }
    """
    
    TITLE = "Next Token Predictor"
    SUB_TITLE = "Compare language model predictions"
    
    show_predictions = reactive(False)
    show_actual = reactive(False)
    
    def __init__(self):
        super().__init__()
        self.article = get_random_wikipedia_article()
        self.sample = get_random_text_sample(self.article['text'], minimum_sample_length=30)
        self.prefix_size = 10
        self.step_results = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Container(
            Static(id="title"),
            Static(id="prefix"),
            Button("Show/Hide Predictions", id="toggle_predictions", variant="primary"),
            Static(id="predictions"),
            Button("Reveal Next Token & Advance", id="next_token", variant="success"),
            Static(id="actual"),
            Button("New Article", id="new_article", variant="warning"),
            Footer(),
        )
    
    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.update_display()
    
    def update_display(self) -> None:
        """Update the display with current data."""
        # Update title
        self.query_one("#title").update(f"Article: {self.article['title']}")
        
        # Update prefix
        prefix_text = ''.join(self.sample[:self.prefix_size])
        self.query_one("#prefix").update(f"Current Prefix:\n{prefix_text}")
        
        # Get predictions
        self.step_results = step(self.sample, self.prefix_size)
        
        # Update predictions
        predictions_text = "Model Predictions:\n\n"
        
        # GPT-2
        predictions_text += "[b][u]GPT-2:[/u][/b]\n"
        for pred in self.step_results["predictions"]["gpt2"]:
            predictions_text += f"{pred['probability']:.3f}: {pred['token']}\n"
        
        # Llama-2
        predictions_text += "\n[b][u]Llama-2:[/u][/b]\n"
        if "llama2" in self.step_results["predictions"]:
            for pred in self.step_results["predictions"]["llama2"]:
                if "error" in pred:
                    predictions_text += f"Error: {pred['error']}\n"
                else:
                    predictions_text += f"{pred['probability']:.3f}: {pred['token']}\n"
        else:
            predictions_text += "Not available\n"
        
        # Llama 3.1
        predictions_text += "\n[b][u]Llama 3.1:[/u][/b]\n"
        for pred in self.step_results["predictions"]["llama3"]:
            if "error" in pred:
                predictions_text += f"Error: {pred['error']}\n"
            else:
                predictions_text += f"{pred['probability']:.3f}: {pred['token']}\n"
        
        self.query_one("#predictions").update(predictions_text)
        
        # Update actual next token
        actual_text = f"Actual Next Token: {self.step_results['next_actual_token']}"
        self.query_one("#actual").update(actual_text)
        
        # Apply visibility based on reactive variables
        predictions = self.query_one("#predictions")
        predictions.set_class(self.show_predictions, "visible")
        
        actual = self.query_one("#actual")
        actual.set_class(self.show_actual, "visible")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when a button is pressed."""
        if event.button.id == "toggle_predictions":
            self.show_predictions = not self.show_predictions
            predictions = self.query_one("#predictions")
            predictions.set_class(self.show_predictions, "visible")
        
        elif event.button.id == "next_token":
            self.show_actual = True
            actual = self.query_one("#actual")
            actual.set_class(self.show_actual, "visible")
            
            # Wait a moment before advancing
            def advance():
                self.prefix_size += 1
                self.show_actual = False
                self.update_display()
            
            self.set_timer(2, advance)
            
        elif event.button.id == "new_article":
            self.article = get_random_wikipedia_article()
            self.sample = get_random_text_sample(self.article['text'], minimum_sample_length=30)
            self.prefix_size = 10
            self.show_predictions = False
            self.show_actual = False
            self.update_display()

if __name__ == "__main__":
    app = NextTokenPredictor()
    
    # Check if we should run as a web app
    if len(sys.argv) > 1 and sys.argv[1] == "--web":
        # Run as a web app
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        app.run(port=port, web_browser=True, log="textual.log")
    else:
        # Run as a terminal app
        print("Running in terminal mode. Use --web to run as a web app.")
        app.run()
