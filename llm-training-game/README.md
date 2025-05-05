(This README was written 3 months ago and mostly by Claude -- it probably has a number of mistakes.)

# LLM Prediction Viewer

This application allows you to view and compare predictions from different language models (GPT-2, Llama 3.1, and optionally Llama-2) on random Wikipedia text samples. The application is split into two components:

1. **Data Generation** (`generate.py`): Fetches random Wikipedia articles and generates model predictions
2. **User Interface**: Multiple options available:
   - Web UI (`index.html` and `ui.js`): A browser-based interface
   - Terminal UI (`tui.py`): A text-based interface using Textual

## Setup and Usage

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

#### Option 1: Web Interface

You can use any static file server:

```bash
python -m http.server

# Then open http://localhost:8000 in your browser
```

#### Option 2: Terminal Interface

(This is an experimental interface that I've mostly abandoned.)

For a terminal-based interface, run:

```bash
python tui.py
```

Terminal UI keyboard shortcuts:
- `q`: Quit the application
- `p`: Toggle predictions visibility
- `r`: Reveal the next token
- `n`: Reveal next token or advance to next step if token is already revealed
- Arrow keys: Navigate between samples and steps
  - `←` / `→`: Previous/Next step
  - `↑` / `↓`: Previous/Next sample

You can also run the terminal UI as a web app:

```bash
python tui.py --web
```

## File Structure

- `generate.py`: Script for generating prediction data
- `ui.js`: React component for the web user interface
- `index.html`: HTML file that hosts the React application
- `tui.py`: Terminal-based user interface using Textual
- `serve.py`: Helper script to run a local server
- `prediction_data.json`: Generated prediction data (created after running `generate.py`)
- `requirements.txt`: Python dependencies
