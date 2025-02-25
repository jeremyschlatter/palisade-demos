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
        // Check if we're at the last phase of the last step of the last sample
        const isLastPhase = data && 
                           currentSampleIndex === data.length - 1 && 
                           currentStepIndex === data[currentSampleIndex].steps.length - 1 && 
                           showPredictions && 
                           showActualToken;
        
        // Only call handleForward if we're not at the last phase
        if (!isLastPhase) {
          handleForward();
        }
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
      <div className="loading-container">
        <div className="loading-spinner" />
        <p>Loading prediction data...</p>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="error-container">
        <h2>Error Loading Data</h2>
        <p>{error}</p>
        <p>Make sure prediction_data.json is available in the same directory as this HTML file.</p>
      </div>
    );
  }

  // Render when no data is available
  if (!data || data.length === 0) {
    return (
      <div className="error-container">
        <h2>No Data Available</h2>
        <p>No prediction data was found. Please generate data using generate.py first.</p>
      </div>
    );
  }

  // Get current sample and step
  const currentSample = data[currentSampleIndex];
  const currentStep = currentSample.steps[currentStepIndex];

  // Get minimal progress info
  const progressText = `${currentSampleIndex + 1}.${currentStepIndex + 1}`;

  // Format probability as percentage with 2 significant figures
  const formatProbability = (prob) => {
    const percentage = prob * 100;
    if (percentage >= 10) {
      return `${Math.round(percentage)}%`;
    } else if (percentage >= 1) {
      return `${percentage.toFixed(1)}%`;
    } else {
      return `${percentage.toFixed(2)}%`;
    }
  };

  // Check if a prediction matches the actual token
  const isCorrectPrediction = (token) => {
    return token === currentStep.next_actual_token;
  };

  // Render prefix with a styled blank marker
  const renderPrefix = () => {
    if (showActualToken) {
      return (
        <React.Fragment>
          {currentStep.prefix}
          <span className="filled-blank">{currentStep.next_actual_token}</span>
        </React.Fragment>
      );
    } else {
      return (
        <React.Fragment>
          {currentStep.prefix}
          <span className="blank-marker">{"\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0"}</span>
        </React.Fragment>
      );
    }
  };

  return (
    <div className="app-container">
      <div className="status-bar">
        <button 
          className="nav-button" 
          onClick={handleBackward}
          disabled={currentSampleIndex === 0 && currentStepIndex === 0 && !showPredictions && !showActualToken}
        >
          ←
        </button>
        <span className="status-text">{progressText}</span>
        <button 
          className="nav-button forward-button" 
          onClick={handleForward}
          disabled={currentSampleIndex === data.length - 1 && 
                   currentStepIndex === currentSample.steps.length - 1 && 
                   showPredictions && showActualToken}
        >
          →
        </button>
      </div>

      <div className="content-container">
        <div className="prefix-container">
          <div className="prefix-text">{renderPrefix()}</div>
        </div>

        <div className="predictions-container">
          {showPredictions ? (
            <div className="models-grid">
              <div className="model-predictions">
                <h3>GPT-2</h3>
                <h4>1.5B params, 2019</h4>
                <ul className="prediction-list">
                  {currentStep.predictions.gpt2.map((pred, index) => (
                    <li 
                      key={`gpt2-${index}`} 
                      className={`prediction-item ${showActualToken && isCorrectPrediction(pred.token) ? "correct-prediction" : ""}`}
                    >
                      <span className="probability">{formatProbability(pred.probability)}</span>
                      <span 
                        className={`token ${showActualToken && isCorrectPrediction(pred.token) ? "correct-token" : ""}`}
                      >
                        {pred.token}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="model-predictions">
                <h3>Llama 3.1</h3>
                <h4>405B params, 2024</h4>
                <ul className="prediction-list">
                  {currentStep.predictions.llama3.map((pred, index) => (
                    <li 
                      key={`llama3-${index}`} 
                      className={`prediction-item ${showActualToken && !pred.error && isCorrectPrediction(pred.token) ? "correct-prediction" : ""}`}
                    >
                      {pred.error ? (
                        <span className="error">{pred.error}</span>
                      ) : (
                        <React.Fragment>
                          <span className="probability">{formatProbability(pred.probability)}</span>
                          <span 
                            className={`token ${showActualToken && isCorrectPrediction(pred.token) ? "correct-token" : ""}`}
                          >
                            {pred.token}
                          </span>
                        </React.Fragment>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="placeholder-content">
              <div className="models-grid">
                <div className="model-predictions">
                  <h3>GPT-2</h3>
                  <h4>1.5B params, 2019</h4>
                  <div className="prediction-placeholder"></div>
                </div>
                <div className="model-predictions">
                  <h3>Llama 3.1</h3>
                  <h4>405B params, 2024</h4>
                  <div className="prediction-placeholder"></div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="actual-token-container">
          {showActualToken ? (
            <div className="actual-token">{currentStep.next_actual_token}</div>
          ) : (
            <div className="actual-token-placeholder"></div>
          )}
        </div>
      </div>
    </div>
  );
}

// Render the app
ReactDOM.render(<App />, document.getElementById('root')); 