// LLM Prediction Viewer
// A minimal React application to view model predictions

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

  // Handle navigation between samples
  const goToNextSample = () => {
    if (data && currentSampleIndex < data.length - 1) {
      setCurrentSampleIndex(currentSampleIndex + 1);
      setCurrentStepIndex(0);
      setShowPredictions(false);
      setShowActualToken(false);
    }
  };

  const goToPreviousSample = () => {
    if (data && currentSampleIndex > 0) {
      setCurrentSampleIndex(currentSampleIndex - 1);
      setCurrentStepIndex(0);
      setShowPredictions(false);
      setShowActualToken(false);
    }
  };

  // Handle navigation between steps
  const goToNextStep = () => {
    const currentSample = data[currentSampleIndex];
    if (currentSample && currentStepIndex < currentSample.steps.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
      setShowPredictions(false);
      setShowActualToken(false);
    }
  };

  const goToPreviousStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
      setShowPredictions(false);
      setShowActualToken(false);
    }
  };

  // Toggle predictions visibility
  const togglePredictions = () => {
    setShowPredictions(!showPredictions);
  };

  // Reveal actual token and prepare for next step
  const revealAndAdvance = () => {
    setShowActualToken(true);
  };

  // Continue to next step after revealing token
  const continueToNextStep = () => {
    const currentSample = data[currentSampleIndex];
    if (currentSample && currentStepIndex < currentSample.steps.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
      setShowPredictions(false);
      setShowActualToken(false);
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

  return (
    React.createElement("div", { className: "app-container" },
      React.createElement("div", { className: "navigation-controls" },
        React.createElement("div", { className: "sample-navigation" },
          React.createElement("button", { onClick: goToPreviousSample, disabled: currentSampleIndex === 0 }, "←"),
          React.createElement("span", { className: "sample-info" }, 
            currentSample.article_title, " (", currentSampleIndex + 1, "/", data.length, ")"
          ),
          React.createElement("button", { onClick: goToNextSample, disabled: currentSampleIndex === data.length - 1 }, "→")
        ),

        React.createElement("div", { className: "step-navigation" },
          React.createElement("button", { onClick: goToPreviousStep, disabled: currentStepIndex === 0 }, "←"),
          React.createElement("span", { className: "step-info" },
            "Step ", currentStepIndex + 1, "/", currentSample.steps.length
          ),
          React.createElement("button", { onClick: goToNextStep, disabled: currentStepIndex === currentSample.steps.length - 1 }, "→")
        )
      ),

      React.createElement("div", { className: "content-container" },
        React.createElement("div", { className: "prefix-container" },
          React.createElement("div", { className: "prefix-text" }, currentStep.prefix)
        ),

        React.createElement("div", { className: "action-buttons" },
          React.createElement("button", { className: "primary-button", onClick: togglePredictions },
            showPredictions ? "Hide" : "Show"
          ),
          React.createElement("button", { className: "secondary-button", onClick: revealAndAdvance }, "Reveal")
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
            React.createElement("div", { className: "actual-token" }, currentStep.next_actual_token),
            React.createElement("button", { className: "continue-button", onClick: continueToNextStep }, "Next")
          )
      )
    )
  );
}

// Render the app
ReactDOM.render(React.createElement(App), document.getElementById('root')); 