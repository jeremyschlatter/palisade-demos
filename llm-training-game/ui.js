// LLM Prediction Viewer
// Ultra-minimal React application to view model predictions

// Main App component
function App() {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [currentSampleIndex, setCurrentSampleIndex] = React.useState(0);
  const [currentStepIndex, setCurrentStepIndex] = React.useState(0);
  const [showPredictions, setShowPredictions] = React.useState(false);
  const [showActualToken, setShowActualToken] = React.useState(false);

  // Load data on component mount
  React.useEffect(() => {
    fetch('prediction_data.json')
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(jsonData => {
        setData(jsonData);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Handle keyboard events
  React.useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'ArrowRight') {
        handleForward();
      } else if (event.key === 'ArrowLeft') {
        handleBackward();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [data, currentSampleIndex, currentStepIndex, showPredictions, showActualToken]);

  // Handle forward action (progression: show predictions -> show answer -> advance)
  const handleForward = () => {
    if (!data) return;
    
    if (!showPredictions) {
      // First step: Show predictions
      setShowPredictions(true);
    } else if (!showActualToken) {
      // Second step: Show actual token
      setShowActualToken(true);
    } else {
      // Third step: Advance to next step or sample
      const currentSample = data[currentSampleIndex];
      
      if (currentStepIndex < currentSample.steps.length - 1) {
        // Move to next step in current sample
        setCurrentStepIndex(currentStepIndex + 1);
      } else if (currentSampleIndex < data.length - 1) {
        // Move to first step of next sample
        setCurrentSampleIndex(currentSampleIndex + 1);
        setCurrentStepIndex(0);
      }
      
      // Reset visibility states
      setShowPredictions(false);
      setShowActualToken(false);
    }
  };

  // Handle backward action
  const handleBackward = () => {
    if (!data) return;
    
    if (showActualToken) {
      // If showing answer, go back to just showing predictions
      setShowActualToken(false);
    } else if (showPredictions) {
      // If showing predictions, hide them
      setShowPredictions(false);
    } else {
      // Go to previous step or sample
      if (currentStepIndex > 0) {
        // Go to previous step in current sample
        setCurrentStepIndex(currentStepIndex - 1);
        // Show the answer for the previous step
        setShowPredictions(true);
        setShowActualToken(true);
      } else if (currentSampleIndex > 0) {
        // Go to last step of previous sample
        const prevSample = data[currentSampleIndex - 1];
        setCurrentSampleIndex(currentSampleIndex - 1);
        setCurrentStepIndex(prevSample.steps.length - 1);
        // Show the answer for the last step of previous sample
        setShowPredictions(true);
        setShowActualToken(true);
      }
    }
  };

  // Render loading state
  if (loading) {
    return (
      React.createElement("div", { className: "loading-container" },
        React.createElement("div", { className: "loading-spinner" }),
        React.createElement("p", null, "Loading prediction data...")
      )
    );
  }

  // Render error state
  if (error) {
    return (
      React.createElement("div", { className: "error-container" },
        React.createElement("h2", null, "Error Loading Data"),
        React.createElement("p", null, error),
        React.createElement("p", null, "Make sure prediction_data.json is available in the same directory as this HTML file.")
      )
    );
  }

  // Render when no data is available
  if (!data || data.length === 0) {
    return (
      React.createElement("div", { className: "error-container" },
        React.createElement("h2", null, "No Data Available"),
        React.createElement("p", null, "No prediction data was found. Please generate data using generate.py first.")
      )
    );
  }

  // Get current sample and step
  const currentSample = data[currentSampleIndex];
  const currentStep = currentSample.steps[currentStepIndex];

  // Get minimal progress info
  const progressText = `${currentSampleIndex + 1}.${currentStepIndex + 1}`;

  return (
    React.createElement("div", { className: "app-container" },
      React.createElement("div", { className: "status-bar" },
        React.createElement("span", { className: "status-text" }, progressText)
      ),

      React.createElement("div", { className: "content-container" },
        React.createElement("div", { className: "prefix-container" },
          React.createElement("div", { className: "prefix-text" }, currentStep.prefix)
        ),

        showPredictions && 
          React.createElement("div", { className: "predictions-container" },
            React.createElement("div", { className: "models-grid" },
              React.createElement("div", { className: "model-predictions" },
                React.createElement("h3", null, "GPT-2"),
                React.createElement("ul", { className: "prediction-list" },
                  currentStep.predictions.gpt2.map((pred, index) => 
                    React.createElement("li", { key: `gpt2-${index}`, className: "prediction-item" },
                      React.createElement("span", { className: "probability" }, pred.probability.toFixed(3)),
                      React.createElement("span", { className: "token" }, pred.token)
                    )
                  )
                )
              ),

              React.createElement("div", { className: "model-predictions" },
                React.createElement("h3", null, "Llama 3.1"),
                React.createElement("ul", { className: "prediction-list" },
                  currentStep.predictions.llama3.map((pred, index) => 
                    React.createElement("li", { key: `llama3-${index}`, className: "prediction-item" },
                      pred.error 
                        ? React.createElement("span", { className: "error" }, pred.error)
                        : React.createElement(React.Fragment, null,
                            React.createElement("span", { className: "probability" }, pred.probability.toFixed(3)),
                            React.createElement("span", { className: "token" }, pred.token)
                          )
                    )
                  )
                )
              )
            )
          ),

        showActualToken && 
          React.createElement("div", { className: "actual-token-container" },
            React.createElement("div", { className: "actual-token" }, currentStep.next_actual_token)
          ),
          
        React.createElement("div", { className: "navigation-buttons" },
          React.createElement("button", { 
            className: "nav-button", 
            onClick: handleBackward,
            disabled: currentSampleIndex === 0 && currentStepIndex === 0 && !showPredictions && !showActualToken
          }, "←"),
          React.createElement("button", { 
            className: "nav-button forward-button", 
            onClick: handleForward,
            disabled: currentSampleIndex === data.length - 1 && 
                     currentStepIndex === currentSample.steps.length - 1 && 
                     showPredictions && showActualToken
          }, "→")
        )
      )
    )
  );
}

// Render the app
ReactDOM.render(React.createElement(App), document.getElementById('root')); 