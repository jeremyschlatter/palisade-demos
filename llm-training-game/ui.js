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

// Format probability as percentage with 2 significant figures
function formatProbability (prob) {
  const percentage = prob * 100;
  if (percentage >= 10) {
    return `${Math.round(percentage)}%`;
  } else if (percentage >= 1) {
    return `${percentage.toFixed(1)}%`;
  } else {
    return `${percentage.toFixed(2)}%`;
  }
};


// Replace with a single data structure
const DATASET_INFO = [
  { path: 'wikipedia.json', title: 'wikipedia' },
  { path: 'addition.json', title: 'addition' },
  { path: 'multiply.json', title: 'multiplication' },
  { path: 'specification-gaming.json', title: 'specification gaming paper' },
];

// Define action types for reducer
const ACTION_TYPES = {
  SET_DATASETS: 'SET_DATASETS',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CHANGE_DATASET: 'CHANGE_DATASET',
  FORWARD: 'FORWARD',
  BACKWARD: 'BACKWARD',
  RESET_STATE: 'RESET_STATE',
  NEXT_DATASET: 'NEXT_DATASET',
  PREV_DATASET: 'PREV_DATASET'
};

// Initial state
const initialState = {
  datasets: {},
  currentDatasetIndex: 0,
  loading: true,
  error: null,
  currentSampleIndex: 0,
  currentStepIndex: 0,
  showPredictions: false,
  showActualToken: false
};

// Reducer function to handle all state transitions
function appReducer(state, action) {
  switch (action.type) {
    case ACTION_TYPES.SET_DATASETS:
      return {
        ...state,
        datasets: action.payload
      };

    case ACTION_TYPES.SET_LOADING:
      return {
        ...state,
        loading: action.payload
      };

    case ACTION_TYPES.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        loading: false
      };

    case ACTION_TYPES.CHANGE_DATASET:
      return {
        ...state,
        currentDatasetIndex: action.payload,
        currentSampleIndex: 0,
        currentStepIndex: 0,
        showPredictions: false,
        showActualToken: false
      };

    case ACTION_TYPES.NEXT_DATASET:
      if (state.currentDatasetIndex >= DATASET_INFO.length - 1) {
        return state;
      }
      return {
        ...state,
        currentDatasetIndex: state.currentDatasetIndex + 1,
        currentSampleIndex: 0,
        currentStepIndex: 0,
        showPredictions: false,
        showActualToken: false
      };

    case ACTION_TYPES.PREV_DATASET:
      if (state.currentDatasetIndex <= 0) {
        return state;
      }
      return {
        ...state,
        currentDatasetIndex: state.currentDatasetIndex - 1,
        currentSampleIndex: 0,
        currentStepIndex: 0,
        showPredictions: false,
        showActualToken: false
      };

    case ACTION_TYPES.FORWARD: {
      const currentDataset = getCurrentDatasetFromState(state);
      if (!currentDataset) return state;

      const currentSample = currentDataset[state.currentSampleIndex];
      if (!currentSample || !currentSample.steps) return state;
      
      const currentStep = currentSample.steps[state.currentStepIndex];
      if (!currentStep) return state;

      // If we're not showing predictions yet
      if (!state.showPredictions) {
        // If this dataset has predictions, show them
        if (currentStep.predictions) {
          return {
            ...state,
            showPredictions: true
          };
        } 
        // If no predictions, skip directly to showing the actual token
        else {
          return {
            ...state,
            showActualToken: true
          };
        }
      }
      // If we're showing predictions but not the actual token, show it
      else if (!state.showActualToken) {
        return {
          ...state,
          showActualToken: true
        };
      }
      // If we're showing both (or just the actual token for datasets without predictions), advance to the next step or sample
      else {
        // If we're not at the last step of the current sample, go to next step
        if (state.currentStepIndex < currentSample.steps.length - 1) {
          return {
            ...state,
            currentStepIndex: state.currentStepIndex + 1,
            showPredictions: false,
            showActualToken: false
          };
        }
        // If we're at the last step but not the last sample, go to the first step of the next sample
        else if (state.currentSampleIndex < currentDataset.length - 1) {
          return {
            ...state,
            currentSampleIndex: state.currentSampleIndex + 1,
            currentStepIndex: 0,
            showPredictions: false,
            showActualToken: false
          };
        }
        // If we're at the last step of the last sample, do nothing
        return state;
      }
    }

    case ACTION_TYPES.BACKWARD: {
      const currentDataset = getCurrentDatasetFromState(state);
      if (!currentDataset) return state;

      const currentSample = currentDataset[state.currentSampleIndex];
      if (!currentSample || !currentSample.steps) return state;
      
      const currentStep = currentSample.steps[state.currentStepIndex];
      if (!currentStep) return state;

      const hasPredictions = !!currentStep.predictions;

      // If showing the actual token, go back to just showing predictions (or to initial state if no predictions)
      if (state.showActualToken) {
        if (hasPredictions) {
          return {
            ...state,
            showActualToken: false
          };
        } else {
          return {
            ...state,
            showActualToken: false,
            showPredictions: false
          };
        }
      }
      // If showing predictions but not the actual token, hide predictions
      else if (state.showPredictions) {
        return {
          ...state,
          showPredictions: false
        };
      }
      // If not showing anything, go to the previous step or sample
      else {
        // If we're not at the first step of the current sample, go to previous step
        if (state.currentStepIndex > 0) {
          const prevStep = currentSample.steps[state.currentStepIndex - 1];
          const prevHasPredictions = prevStep && !!prevStep.predictions;
          
          return {
            ...state,
            currentStepIndex: state.currentStepIndex - 1,
            showPredictions: prevHasPredictions,
            showActualToken: true
          };
        }
        // If we're at the first step but not the first sample, go to the last step of the previous sample
        else if (state.currentSampleIndex > 0) {
          const prevSample = currentDataset[state.currentSampleIndex - 1];
          if (!prevSample || !prevSample.steps) return state;

          const prevStep = prevSample.steps[prevSample.steps.length - 1];
          const prevHasPredictions = prevStep && !!prevStep.predictions;
          
          return {
            ...state,
            currentSampleIndex: state.currentSampleIndex - 1,
            currentStepIndex: prevSample.steps.length - 1,
            showPredictions: prevHasPredictions,
            showActualToken: true
          };
        }
        // If we're at the first step of the first sample, do nothing
        return state;
      }
    }

    case ACTION_TYPES.RESET_STATE:
      return {
        ...state,
        currentSampleIndex: 0,
        currentStepIndex: 0,
        showPredictions: false,
        showActualToken: false
      };

    default:
      return state;
  }
}

// Helper function to get current dataset from state
function getCurrentDatasetFromState(state) {
  const currentDatasetInfo = DATASET_INFO[state.currentDatasetIndex];
  const dataset = state.datasets[currentDatasetInfo.path];

  if (!dataset) {
    console.error(`Dataset not found or is null: ${currentDatasetInfo.path}`);
  }

  return dataset;
}

// ModelPredictions component to eliminate duplication
function ModelPredictions({ modelName, subtitle, predictions, showActualToken, actualToken }) {
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

          return (
            <li key={`${modelName}-${index}`} style={{
              padding: '4px',
              borderBottom: index === predictions.length - 1 ? 'none' : '1px solid #eee',
              display: 'flex',
              alignItems: 'center',
              fontSize: '14px',
              backgroundColor: isCorrect ? 'rgba(76, 175, 80, 0.1)' : 'transparent'
            }}>
              <span style={{
                fontWeight: 'bold',
                marginRight: '10px',
                minWidth: '60px',
                color: colors.secondary
              }}>{formatProbability(pred.probability)}</span>
              <span style={{
                fontFamily: 'monospace',
                backgroundColor: isCorrect ? 'rgba(76, 175, 80, 0.3)' : '#f0f0f0',
                padding: isCorrect ? '0px 3px' : '1px 4px',
                borderRadius: '2px',
                border: isCorrect ? `1px solid ${colors.correct}` : 'none'
              }}>{pred.token}</span>
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
        height: '136.5px',
        borderRadius: '3px',
        marginTop: '5px'
      }}></div>
    </div>
  );
}

// Main App component
function App() {
  // Use reducer for state management
  const [state, dispatch] = React.useReducer(appReducer, initialState);

  // Destructure state for easier access
  const {
    datasets,
    currentDatasetIndex,
    loading,
    error,
    currentSampleIndex,
    currentStepIndex,
    showPredictions,
    showActualToken
  } = state;

  // Load all datasets on component mount
  React.useEffect(() => {
    const fetchPromises = DATASET_INFO.map(dataset =>
      fetch(dataset.path)
        .then(response => {
          if (!response.ok) {
            throw new Error(`Failed to load ${dataset.path}`);
          }
          return response.json();
        })
        .then(data => ({ [dataset.path]: data }))
        .catch(err => {
          console.error(`Error loading ${dataset.path}:`, err);
          return { [dataset.path]: null };
        })
    );

    Promise.all(fetchPromises)
      .then(results => {
        const mergedData = Object.assign({}, ...results);
        dispatch({ type: ACTION_TYPES.SET_DATASETS, payload: mergedData });
        dispatch({ type: ACTION_TYPES.SET_LOADING, payload: false });
      })
      .catch(err => {
        dispatch({
          type: ACTION_TYPES.SET_ERROR,
          payload: "Failed to load datasets: " + err.message
        });
      });
  }, []);

  // Get current dataset
  const getCurrentDataset = () => {
    return getCurrentDatasetFromState(state);
  };

  // Handle dataset change
  const handleDatasetChange = (event) => {
    const selectedTitle = event.target.value;
    const newIndex = DATASET_INFO.findIndex(dataset => dataset.title === selectedTitle);
    
    if (newIndex !== -1 && newIndex !== currentDatasetIndex) {
      dispatch({ type: ACTION_TYPES.CHANGE_DATASET, payload: newIndex });
    }
  };

  // Handle keyboard events
  React.useEffect(() => {
    const handleKeyDown = (event) => {
      const data = getCurrentDataset();
      if (!data) return;

      if (event.key === 'ArrowRight') {
        // Get current sample and step
        const currentSample = data[currentSampleIndex];
        if (!currentSample || !currentSample.steps) return;
        
        const currentStep = currentSample.steps[currentStepIndex];
        if (!currentStep) return;
        
        const hasPredictions = !!currentStep.predictions;

        // Check if we're at the last phase of the last step of the last sample
        const isLastPhase = currentSampleIndex === data.length - 1 &&
                           currentStepIndex === currentSample.steps.length - 1 &&
                           ((hasPredictions && showPredictions && showActualToken) || 
                            (!hasPredictions && showActualToken));

        // Only call handleForward if we're not at the last phase
        if (!isLastPhase) {
          handleForward();
        }
      } else if (event.key === 'ArrowLeft') {
        handleBackward();
      } else if (event.key === 'ArrowUp') {
        // Move to previous dataset
        dispatch({ type: ACTION_TYPES.PREV_DATASET });
      } else if (event.key === 'ArrowDown') {
        // Move to next dataset
        dispatch({ type: ACTION_TYPES.NEXT_DATASET });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [datasets, currentDatasetIndex, currentSampleIndex, currentStepIndex, showPredictions, showActualToken]);

  // Handle forward action (progression: show predictions -> show answer -> advance)
  const handleForward = () => {
    const data = getCurrentDataset();
    if (!data) return;

    dispatch({ type: ACTION_TYPES.FORWARD });
  };

  // Handle backward action
  const handleBackward = () => {
    const data = getCurrentDataset();
    if (!data) return;

    dispatch({ type: ACTION_TYPES.BACKWARD });
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
        <p>Loading datasets...</p>
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
        <p>Make sure the dataset JSON files are available in the same directory as this HTML file.</p>
      </div>
    );
  }

  const data = getCurrentDataset();

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
        <p>No prediction data was found in the selected dataset.</p>
        <p>Please select a different dataset or generate data using generate.py first.</p>
        <div style={{ marginTop: '15px' }}>
          <label htmlFor="dataset-select" style={{ marginRight: '10px' }}>Dataset:</label>
          <select
            id="dataset-select"
            value={DATASET_INFO[currentDatasetIndex].title}
            onChange={handleDatasetChange}
            style={{
              padding: '8px',
              borderRadius: '3px',
              border: `1px solid ${colors.border}`,
              backgroundColor: 'white',
              color: colors.text,
              fontSize: '14px'
            }}
          >
            {DATASET_INFO.map(dataset => (
              <option key={dataset.path} value={dataset.title}>{dataset.title}</option>
            ))}
          </select>
        </div>
      </div>
    );
  }

  // Ensure we have a valid sample and step
  if (currentSampleIndex >= data.length) {
    console.error(`Sample index ${currentSampleIndex} out of bounds (data length: ${data.length})`);
    // Instead of directly setting state, dispatch an action
    setTimeout(() => {
      dispatch({ type: ACTION_TYPES.RESET_STATE });
    }, 0);
    return null; // Return null to prevent rendering until state is updated
  }

  const currentSample = data[currentSampleIndex];

  const currentStep = currentSample.steps[currentStepIndex];

  // Get minimal progress info
  const progressText = `${currentSampleIndex + 1}.${currentStepIndex + 1}`;

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

  // Safely check if we're at the last step
  const isLastStep = currentSample &&
                    currentSample.steps &&
                    currentStepIndex === currentSample.steps.length - 1 &&
                    ((currentStep.predictions && showPredictions && showActualToken) || 
                     (!currentStep.predictions && showActualToken));

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

        <div style={{
          display: 'flex',
          alignItems: 'center',
          flexGrow: 1,
          justifyContent: 'center',
          gap: '15px'
        }}>
          <span style={{
            fontFamily: 'monospace',
            fontWeight: 'bold',
            color: '#777'
          }}>{progressText}</span>

          <select
            value={DATASET_INFO[currentDatasetIndex].title}
            onChange={handleDatasetChange}
            style={{
              padding: '4px 8px',
              borderRadius: '3px',
              border: `1px solid ${colors.border}`,
              backgroundColor: 'white',
              color: colors.text,
              fontSize: '13px',
              fontFamily: 'monospace',
              cursor: 'pointer'
            }}
          >
            {DATASET_INFO.map(dataset => (
              <option key={dataset.path} value={dataset.title}>{dataset.title}</option>
            ))}
          </select>
        </div>

        <button
          style={getNavButtonStyle(true, isLastStep && currentSampleIndex === data.length - 1)}
          onClick={handleForward}
          disabled={isLastStep && currentSampleIndex === data.length - 1}
        >
          →
        </button>
      </div>

      <div style={{ padding: '15px', position: 'relative' }}>
        <div style={{ marginBottom: '15px' }}>
          <h3 style={{ 
            marginBottom: '16px',
            padding: '10px',
            color: colors.text,
            fontSize: '20px',
            fontWeight: '300',
            textAlign: 'center'
          }}>Fill in the blank.</h3>
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
          {currentStep.predictions ? (
            showPredictions ? (
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
                />

                <ModelPredictions
                  modelName="Llama 3.1"
                  subtitle="405B params, 2024"
                  predictions={currentStep.predictions.llama3}
                  showActualToken={showActualToken}
                  actualToken={currentStep.next_actual_token}
                />
              </div>
            ) : (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                gap: '15px',
                marginTop: '10px',
                opacity: currentSampleIndex == 0 && currentStepIndex == 0 ? 0.4 : 1,
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
            )
          ) : (
            <div style={{
              padding: '15px',
              textAlign: 'center',
              color: colors.text
            }}>
              <p>No model predictions available for this dataset.</p>
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
