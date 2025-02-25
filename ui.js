// LLM Prediction Viewer
// A React application to view model predictions

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
      <div className="loading-container">
        <div className="loading-spinner"></div>
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

  return (
    <div className="app-container">
      <header>
        <h1>LLM Prediction Viewer</h1>
        <p className="subtitle">Compare how different language models predict the next token</p>
      </header>

      <div className="navigation-controls">
        <div className="sample-navigation">
          <button onClick={goToPreviousSample} disabled={currentSampleIndex === 0}>
            ← Previous Article
          </button>
          <span className="sample-info">
            Article {currentSampleIndex + 1} of {data.length}: {currentSample.article_title}
          </span>
          <button onClick={goToNextSample} disabled={currentSampleIndex === data.length - 1}>
            Next Article →
          </button>
        </div>

        <div className="step-navigation">
          <button onClick={goToPreviousStep} disabled={currentStepIndex === 0}>
            ← Previous Step
          </button>
          <span className="step-info">
            Step {currentStepIndex + 1} of {currentSample.steps.length}
          </span>
          <button onClick={goToNextStep} disabled={currentStepIndex === currentSample.steps.length - 1}>
            Next Step →
          </button>
        </div>
      </div>

      <div className="content-container">
        <div className="prefix-container">
          <h2>What comes next?</h2>
          <div className="prefix-text">{currentStep.prefix}</div>
        </div>

        <div className="action-buttons">
          <button className="primary-button" onClick={togglePredictions}>
            {showPredictions ? "Hide Predictions" : "Show Predictions"}
          </button>
          <button className="secondary-button" onClick={revealAndAdvance}>
            Reveal Next Token
          </button>
        </div>

        {showPredictions && (
          <div className="predictions-container">
            <h2>Model Predictions</h2>
            <div className="models-grid">
              <div className="model-predictions">
                <h3>GPT-2</h3>
                <ul className="prediction-list">
                  {currentStep.predictions.gpt2.map((pred, index) => (
                    <li key={`gpt2-${index}`} className="prediction-item">
                      <span className="probability">{pred.probability.toFixed(3)}</span>
                      <span className="token">{pred.token}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="model-predictions">
                <h3>Llama 3.1</h3>
                <ul className="prediction-list">
                  {currentStep.predictions.llama3.map((pred, index) => (
                    <li key={`llama3-${index}`} className="prediction-item">
                      {pred.error ? (
                        <span className="error">{pred.error}</span>
                      ) : (
                        <>
                          <span className="probability">{pred.probability.toFixed(3)}</span>
                          <span className="token">{pred.token}</span>
                        </>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {showActualToken && (
          <div className="actual-token-container">
            <h2>Actual Next Token</h2>
            <div className="actual-token">{currentStep.next_actual_token}</div>
            <button className="continue-button" onClick={continueToNextStep}>
              Continue to Next Step
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Render the app
ReactDOM.render(<App />, document.getElementById('root')); 