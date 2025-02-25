#!/bin/bash

# LLM Prediction Viewer Runner Script
# This script helps users run the LLM Prediction Viewer application

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}LLM Prediction Viewer${NC}"
echo "This script will help you run the application."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if prediction_data.json exists
if [ ! -f "prediction_data.json" ]; then
    echo -e "${YELLOW}Warning: prediction_data.json not found.${NC}"
    echo "Would you like to generate prediction data now? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${GREEN}Running generate.py...${NC}"
        python3 generate.py
        if [ $? -ne 0 ]; then
            echo -e "${RED}Error: Failed to generate prediction data.${NC}"
            echo "Please check the error message above and try again."
            exit 1
        fi
    else
        echo "You can generate prediction data later by running: python3 generate.py"
    fi
fi

# Start the server
echo -e "${GREEN}Starting the server...${NC}"
echo "The application will open in your default web browser."
echo "Press Ctrl+C to stop the server when you're done."
echo

# Check if serve.py exists, otherwise use Python's built-in HTTP server
if [ -f "serve.py" ]; then
    python3 serve.py
else
    # Open the browser
    if command -v open &> /dev/null; then
        open http://localhost:8000
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8000
    elif command -v start &> /dev/null; then
        start http://localhost:8000
    fi
    
    # Start the server
    python3 -m http.server 8000
fi 