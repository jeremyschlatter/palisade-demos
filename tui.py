#!/usr/bin/env python3
"""
Terminal UI for LLM Prediction Viewer using Textual.
This app loads pre-generated prediction data from prediction_data.json.
"""

import json
import os
import sys
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Static, Header, Footer, Label
from textual.reactive import reactive
from textual import events
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.console import Group

class PredictionViewer(App):
    """A Textual app to view pre-generated language model predictions."""
    
    CSS = """
    #title {
        background: $boost;
        color: $text;
        padding: 1;
        text-align: center;
        text-style: bold;
        dock: top;
    }
    
    #navigation {
        layout: horizontal;
        background: $panel;
        height: 3;
        padding: 0 1;
        margin: 0 0 1 0;
    }
    
    #sample_nav {
        width: 50%;
        height: 3;
        content-align: left middle;
    }
    
    #step_nav {
        width: 50%;
        height: 3;
        content-align: right middle;
    }
    
    #prefix {
        margin: 1 0;
        padding: 1;
        background: $surface;
        border: solid $accent;
        height: auto;
        min-height: 5;
    }
    
    #predictions {
        margin: 1 0;
        padding: 1;
        background: $surface;
        border: solid $accent;
        height: auto;
        min-height: 10;
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
        min-height: 3;
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
    
    .nav-info {
        padding: 0 1;
    }
    
    .action-buttons {
        layout: horizontal;
        align: center middle;
        height: 3;
    }
    
    Footer {
        background: $boost;
        color: $text;
    }
    """
    
    TITLE = "LLM Prediction Viewer"
    SUB_TITLE = "Compare language model predictions"
    
    show_predictions = reactive(False)
    show_actual = reactive(False)
    current_sample_index = reactive(0)
    current_step_index = reactive(0)
    
    def __init__(self):
        super().__init__()
        self.data = self.load_data()
    
    def load_data(self):
        """Load prediction data from JSON file."""
        try:
            with open('prediction_data.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            return None
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Static(id="title")
        
        yield Container(
            Horizontal(
                Static(id="sample_nav"),
                Static(id="step_nav"),
                id="navigation"
            ),
            Static(id="prefix"),
            Container(
                Button("Show/Hide Predictions", id="toggle_predictions", variant="primary"),
                Button("Reveal Next Token", id="reveal_token", variant="success"),
                classes="action-buttons"
            ),
            Static(id="predictions"),
            Static(id="actual"),
            Container(
                Button("Previous Sample", id="prev_sample", variant="default"),
                Button("Next Sample", id="next_sample", variant="default"),
                Button("Previous Step", id="prev_step", variant="default"),
                Button("Next Step", id="next_step", variant="default"),
                classes="action-buttons"
            ),
        )
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when the app is mounted."""
        if not self.data:
            self.query_one("#title").update("Error: No prediction data found. Run 'python generate.py' first.")
            return
        
        self.update_display()
    
    def update_display(self) -> None:
        """Update the display with current data."""
        if not self.data:
            return
        
        # Get current sample and step
        current_sample = self.data[self.current_sample_index]
        current_step = current_sample["steps"][self.current_step_index]
        
        # Update title
        self.query_one("#title").update(f"Article: {current_sample['article_title']}")
        
        # Update navigation info
        sample_nav = self.query_one("#sample_nav")
        sample_nav.update(f"Sample {self.current_sample_index + 1} of {len(self.data)}")
        
        step_nav = self.query_one("#step_nav")
        step_nav.update(f"Step {self.current_step_index + 1} of {len(current_sample['steps'])}")
        
        # Update prefix
        prefix_text = current_step["prefix"]
        self.query_one("#prefix").update(Panel(prefix_text, title="Current Prefix"))
        
        # Update predictions
        predictions_content = self.format_predictions(current_step["predictions"])
        self.query_one("#predictions").update(predictions_content)
        
        # Update actual next token
        actual_text = Text(f"{current_step['next_actual_token']}", style="bold green")
        self.query_one("#actual").update(Panel(actual_text, title="Actual Next Token"))
        
        # Apply visibility based on reactive variables
        predictions = self.query_one("#predictions")
        predictions.set_class(self.show_predictions, "visible")
        
        actual = self.query_one("#actual")
        actual.set_class(self.show_actual, "visible")
        
        # Update button states
        self.query_one("#prev_sample").disabled = self.current_sample_index == 0
        self.query_one("#next_sample").disabled = self.current_sample_index >= len(self.data) - 1
        self.query_one("#prev_step").disabled = self.current_step_index == 0
        self.query_one("#next_step").disabled = self.current_step_index >= len(current_sample["steps"]) - 1
    
    def format_predictions(self, predictions):
        """Format predictions for display."""
        tables = []
        
        # Create a table for each model
        for model_name, preds in predictions.items():
            table = Table(title=f"{model_name.upper()} Predictions")
            table.add_column("Probability", style="cyan", justify="right")
            table.add_column("Token", style="green")
            
            for pred in preds:
                if "error" in pred:
                    table.add_row("ERROR", pred["error"])
                else:
                    table.add_row(f"{pred['probability']:.3f}", pred["token"])
            
            tables.append(table)
        
        return Group(*tables)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when a button is pressed."""
        button_id = event.button.id
        
        if button_id == "toggle_predictions":
            self.show_predictions = not self.show_predictions
        
        elif button_id == "reveal_token":
            self.show_actual = True
        
        elif button_id == "prev_sample":
            if self.current_sample_index > 0:
                self.current_sample_index -= 1
                self.current_step_index = 0
                self.show_predictions = False
                self.show_actual = False
        
        elif button_id == "next_sample":
            if self.current_sample_index < len(self.data) - 1:
                self.current_sample_index += 1
                self.current_step_index = 0
                self.show_predictions = False
                self.show_actual = False
        
        elif button_id == "prev_step":
            if self.current_step_index > 0:
                self.current_step_index -= 1
                self.show_predictions = False
                self.show_actual = False
        
        elif button_id == "next_step":
            current_sample = self.data[self.current_sample_index]
            if self.current_step_index < len(current_sample["steps"]) - 1:
                self.current_step_index += 1
                self.show_predictions = False
                self.show_actual = False
        
        self.update_display()
    
    def on_key(self, event: events.Key) -> None:
        """Handle key presses."""
        if event.key == "q":
            self.exit()
        elif event.key == "p":
            self.show_predictions = not self.show_predictions
            self.update_display()
        elif event.key == "r":
            self.show_actual = True
            self.update_display()
        elif event.key == "n" and not self.show_actual:
            self.show_actual = True
            self.update_display()
        elif event.key == "n" and self.show_actual:
            current_sample = self.data[self.current_sample_index]
            if self.current_step_index < len(current_sample["steps"]) - 1:
                self.current_step_index += 1
                self.show_predictions = False
                self.show_actual = False
                self.update_display()
        elif event.key == "left":
            if self.current_step_index > 0:
                self.current_step_index -= 1
                # self.show_predictions = False
                self.show_actual = False
                self.update_display()
        elif event.key == "right":
            current_sample = self.data[self.current_sample_index]
            if self.current_step_index < len(current_sample["steps"]) - 1:
                self.current_step_index += 1
                self.show_predictions = False
                self.show_actual = False
                self.update_display()
        elif event.key == "up":
            if self.current_sample_index > 0:
                self.current_sample_index -= 1
                self.current_step_index = 0
                self.show_predictions = False
                self.show_actual = False
                self.update_display()
        elif event.key == "down":
            if self.current_sample_index < len(self.data) - 1:
                self.current_sample_index += 1
                self.current_step_index = 0
                self.show_predictions = False
                self.show_actual = False
                self.update_display()

if __name__ == "__main__":
    app = PredictionViewer()
    
    # Check if we should run as a web app
    if len(sys.argv) > 1 and sys.argv[1] == "--web":
        # Run as a web app
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        app.run(port=port, web_browser=True, log="textual.log")
    else:
        # Run as a terminal app
        app.run() 