// LLM Prediction Viewer
// Ultra-minimal React application to view model predictions

// Define colors as variables for reuse
const colors = {
  primary: '#4a6fa5',
  secondary: '#166088',
  accent: '#4caf50',
  background: '#f8f9fa',
  text: '#333',
  border: '#ddd',
  hover: '#e9ecef',
  correct: '#4caf50',
  error: '#d32f2f',
  disabled: '#b0bec5'
};

// Only keep styles that are used across components
const styles = {
  // Reused model header styles
  modelTitle: {
    fontSize: '14px',
    color: colors.primary
  },
  modelSubtitle: {
    fontSize: '11px',
    marginBottom: '8px',
    color: colors.primary
  }
};

// ModelPredictions component to eliminate duplication
function ModelPredictions({ modelName, subtitle, predictions, showActualToken, actualToken, formatProbability }) {
  // Check if a prediction matches the actual token
  const isCorrectPrediction = (token) => {
    return token === actualToken;
  };
  
  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '3px',
      padding: '10px',
      boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
    }}>
      <h3 style={styles.modelTitle}>{modelName}</h3>
      <h4 style={styles.modelSubtitle}>{subtitle}</h4>
      <ul style={{ listStyleType: 'none', marginTop: '5px' }}>
        {predictions.map((pred, index) => {
          const isCorrect = showActualToken && isCorrectPrediction(pred.token);
          const itemStyle = {
            padding: '4px',
            borderBottom: index === predictions.length - 1 ? 'none' : '1px solid #eee',
            display: 'flex',
            alignItems: 'center',
            fontSize: '14px',
            backgroundColor: isCorrect ? 'rgba(76, 175, 80, 0.1)' : 'transparent'
          };
          
          const tokenStyle = {
            fontFamily: 'monospace',
            backgroundColor: isCorrect ? 'rgba(76, 175, 80, 0.3)' : '#f0f0f0',
            padding: '1px 4px',
            borderRadius: '2px',
            border: isCorrect ? `1px solid ${colors.correct}` : 'none'
          };
          
          return (
            <li key={`${modelName}-${index}`} style={itemStyle}>
              <span style={{
                fontWeight: 'bold',
                marginRight: '10px',
                minWidth: '60px',
                color: colors.secondary
              }}>{formatProbability(pred.probability)}</span>
              <span style={tokenStyle}>{pred.token}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// ModelPlaceholder component for when predictions aren't shown
function ModelPlaceholder({ modelName, subtitle }) {
  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '3px',
      padding: '10px',
      boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
    }}>
      <h3 style={styles.modelTitle}>{modelName}</h3>
      <h4 style={styles.modelSubtitle}>{subtitle}</h4>
      <div style={{
        height: '150px',
        backgroundColor: '#f0f0f0',
        borderRadius: '3px',
        marginTop: '5px'
      }}></div>
    </div>
  );
}

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
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh'
      }}>
        <div style={{
          border: '3px solid rgba(0, 0, 0, 0.1)',
          borderRadius: '50%',
          borderTop: `3px solid ${colors.primary}`,
          width: '30px',
          height: '30px',
          animation: 'spin 1s linear infinite',
          marginBottom: '15px'
        }} />
        <p>Loading prediction data...</p>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div style={{
        maxWidth: '500px',
        margin: '50px auto',
        padding: '15px',
        backgroundColor: '#ffebee',
        borderRadius: '3px',
        borderLeft: `3px solid ${colors.error}`
      }}>
        <h2>Error Loading Data</h2>
        <p>{error}</p>
        <p>Make sure prediction_data.json is available in the same directory as this HTML file.</p>
      </div>
    );
  }

  // Render when no data is available
  if (!data || data.length === 0) {
    return (
      <div style={{
        maxWidth: '500px',
        margin: '50px auto',
        padding: '15px',
        backgroundColor: '#ffebee',
        borderRadius: '3px',
        borderLeft: `3px solid ${colors.error}`
      }}>
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

  // Render prefix with a styled blank marker
  const renderPrefix = () => {
    if (showActualToken) {
      return (
        <React.Fragment>
          {currentStep.prefix}
          <span style={{
            backgroundColor: 'rgba(76, 175, 80, 0.2)',
            borderBottom: `2px solid ${colors.accent}`,
            padding: '0 2px',
            display: 'inline-block'
          }}>{currentStep.next_actual_token}</span>
        </React.Fragment>
      );
    } else {
      return (
        <React.Fragment>
          {currentStep.prefix}
          <span style={{
            borderBottom: '2px solid #333',
            display: 'inline-block'
          }}>{"\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0"}</span>
        </React.Fragment>
      );
    }
  };

  // Determine button styles based on state
  const getNavButtonStyle = (isForward, isDisabled) => {
    const baseStyle = {
      backgroundColor: isForward ? colors.primary : colors.secondary,
      color: 'white',
      border: 'none',
      padding: '6px 12px',
      borderRadius: '3px',
      cursor: isDisabled ? 'not-allowed' : 'pointer',
      fontSize: '16px',
      transition: 'background-color 0.2s',
      width: '40px',
      height: '32px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    };
    
    if (isDisabled) {
      baseStyle.backgroundColor = colors.disabled;
    }
    
    return baseStyle;
  };

  return (
    <div style={{
      maxWidth: '900px',
      margin: '0 auto',
      backgroundColor: 'white',
      borderRadius: '4px',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      overflow: 'hidden',
      position: 'relative'
    }}>
      <div style={{
        backgroundColor: '#f1f3f5',
        padding: '8px 15px',
        borderBottom: `1px solid ${colors.border}`,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <button 
          style={getNavButtonStyle(false, currentSampleIndex === 0 && currentStepIndex === 0 && !showPredictions && !showActualToken)}
          onClick={handleBackward}
          disabled={currentSampleIndex === 0 && currentStepIndex === 0 && !showPredictions && !showActualToken}
        >
          ←
        </button>
        <span style={{
          fontFamily: 'monospace',
          fontWeight: 'bold',
          color: '#777',
          flexGrow: 1,
          textAlign: 'center'
        }}>{progressText}</span>
        <button 
          style={getNavButtonStyle(true, currentSampleIndex === data.length - 1 && 
                 currentStepIndex === currentSample.steps.length - 1 && 
                 showPredictions && showActualToken)}
          onClick={handleForward}
          disabled={currentSampleIndex === data.length - 1 && 
                   currentStepIndex === currentSample.steps.length - 1 && 
                   showPredictions && showActualToken}
        >
          →
        </button>
      </div>

      <div style={{ padding: '15px', position: 'relative' }}>
        <div style={{ marginBottom: '15px' }}>
          <div style={{
            fontFamily: 'monospace',
            fontSize: '16px',
            backgroundColor: '#f8f9fa',
            border: '1px solid #ddd',
            borderRadius: '3px',
            padding: '10px',
            whiteSpace: 'pre-wrap'
          }}>{renderPrefix()}</div>
        </div>

        <div style={{
          marginTop: '15px',
          padding: '10px',
          backgroundColor: '#f8f9fa',
          borderRadius: '3px',
          border: `1px solid ${colors.border}`
        }}>
          {showPredictions ? (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '15px',
              marginTop: '10px'
            }}>
              <ModelPredictions 
                modelName="GPT-2"
                subtitle="1.5B params, 2019"
                predictions={currentStep.predictions.gpt2}
                showActualToken={showActualToken}
                actualToken={currentStep.next_actual_token}
                formatProbability={formatProbability}
              />
              
              <ModelPredictions 
                modelName="Llama 3.1"
                subtitle="405B params, 2024"
                predictions={currentStep.predictions.llama3}
                showActualToken={showActualToken}
                actualToken={currentStep.next_actual_token}
                formatProbability={formatProbability}
              />
            </div>
          ) : (
            <div style={{ opacity: 0.4 }}>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                gap: '15px',
                marginTop: '10px'
              }}>
                <ModelPlaceholder 
                  modelName="GPT-2"
                  subtitle="1.5B params, 2019"
                />
                <ModelPlaceholder 
                  modelName="Llama 3.1"
                  subtitle="405B params, 2024"
                />
              </div>
            </div>
          )}
        </div>

        <div style={{
          marginTop: '15px',
          padding: '10px',
          backgroundColor: '#f8f9fa',
          borderRadius: '3px',
          border: `1px solid ${colors.border}`
        }}>
          {showActualToken ? (
            <div style={{
              fontFamily: 'monospace',
              fontSize: '20px',
              backgroundColor: '#e8f5e9',
              border: `1px solid ${colors.accent}`,
              padding: '10px',
              borderRadius: '3px',
              textAlign: 'center'
            }}>{currentStep.next_actual_token}</div>
          ) : (
            <div style={{
              height: '44px',
              backgroundColor: '#f0f0f0',
              borderRadius: '3px'
            }}></div>
          )}
        </div>
      </div>
    </div>
  );
}

// Render the app
ReactDOM.render(<App />, document.getElementById('root')); 