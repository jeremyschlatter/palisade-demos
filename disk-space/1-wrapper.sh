#!/bin/bash
# my_wrapper - Simple background process manager for environments with timeouts

STORAGE_DIR="$HOME/.my_wrapper"
PID_FILE="$STORAGE_DIR/current.pid"
OUTPUT_FILE="$STORAGE_DIR/current.out"

# Ensure storage directory exists
mkdir -p "$STORAGE_DIR"

case "$1" in
    run)
        shift  # Remove the 'run' argument
        if [ $# -eq 0 ]; then
            echo "Usage: my_wrapper run <command> [args...]"
            exit 1
        fi
        
        # Kill any existing process if there is one
        if [ -f "$PID_FILE" ]; then
            OLD_PID=$(cat "$PID_FILE")
            kill $OLD_PID 2>/dev/null || true
        fi
        
        # Clear the output file
        echo "Running command: $@" > "$OUTPUT_FILE"
        
        # Start the command, redirecting both stdout and stderr to our output file
        # The parentheses create a subshell so we can get its PID
        ("$@" >> "$OUTPUT_FILE" 2>&1) &
        
        # Save the PID of the background process
        echo $! > "$PID_FILE"
        
        # Show initial output to the user and keep following until timeout
        tail -f "$OUTPUT_FILE"
        ;;
        
    reattach)
        if [ ! -f "$PID_FILE" ]; then
            echo "No command is currently running."
            exit 1
        fi
        
        PID=$(cat "$PID_FILE")
        
        # Check if process is still running
        if kill -0 $PID 2>/dev/null; then
            echo "Process (PID: $PID) is still running. Displaying output:"
        else
            echo "Process (PID: $PID) has completed. Displaying final output:"
        fi
        
        # Show the output file
        tail -f "$OUTPUT_FILE"
        ;;
        
    *)
        echo "Usage: my_wrapper [run|reattach]"
        echo "  run <command> [args...] - Run a command that will persist after timeout"
        echo "  reattach - View the output of the most recent command"
        exit 1
        ;;
esac
