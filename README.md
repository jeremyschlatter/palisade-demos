# LLM Prediction Viewer

This application allows you to view and compare predictions from different language models (GPT-2, Llama 3.1, and optionally Llama-2) on random Wikipedia text samples. The application is split into two components:

1. **Data Generation** (`generate.py`): Fetches random Wikipedia articles and generates model predictions
2. **User Interface** (`ui.js` and `index.html`): A web-based interface to view and interact with the predictions

## Setup and Usage

### Prerequisites

- Python 3.8 or higher
- Required Python packages (install with `pip install -r requirements.txt`):
  - requests
  - beautifulsoup4
  - transformers
  - torch
  - tiktoken
  - openai
  - tqdm

### Step 1: Generate Prediction Data

Run the data generation script to fetch Wikipedia articles and generate model predictions:

```bash
python generate.py
```

Options:
- `--num_samples`: Number of Wikipedia samples to generate (default: 10)
- `--steps_per_sample`: Number of prediction steps per sample (default: 10)
- `--output`: Output JSON file name (default: prediction_data.json)

Example with custom parameters:
```bash
python generate.py --num_samples 5 --steps_per_sample 15 --output custom_predictions.json
```

### Step 2: View the Predictions

You can use the included server script to easily view the application:

```bash
python serve.py
```

This will start a local server and open your browser automatically.

Alternatively, you can use any static file server or simply open the HTML file directly in your browser:

```bash
# If you have Python installed, you can use a simple HTTP server
python -m http.server

# Then open http://localhost:8000 in your browser
```

## Features

- **Navigation**: Browse through different Wikipedia samples and prediction steps
- **Model Comparison**: View and compare predictions from different language models side by side
- **Interactive UI**: Toggle prediction visibility and reveal actual tokens
- **Responsive Design**: Works on desktop and mobile devices

## File Structure

- `generate.py`: Script for generating prediction data
- `ui.js`: React component for the user interface
- `index.html`: HTML file that hosts the React application
- `serve.py`: Helper script to run a local server
- `prediction_data.json`: Generated prediction data (created after running `generate.py`)
- `requirements.txt`: Python dependencies

## Customization

You can modify the `generate.py` script to include additional models or change the sampling parameters. The UI will automatically adapt to display the available models in the generated data.

## Troubleshooting

- If you see an error about missing prediction data, make sure you've run `generate.py` first.
- If the models take too long to generate predictions, consider reducing the number of samples or steps per sample.
- For issues with the OpenAI API, ensure your API key is correctly set in your environment variables.