// Simple test component
const TestIndex = () => {
  console.log('TestIndex rendering...');
  console.log('Document ready state:', document.readyState);
  
  return (
    <>
      <div id="test-content" style={{ 
        padding: '20px', 
        backgroundColor: '#ff0000', // Bright red to ensure visibility
        color: 'white', 
        minHeight: '100vh',
        fontSize: '24px',
        border: '5px solid yellow'
      }}>
        <h1 style={{ fontSize: '48px', margin: '0 0 20px 0' }}>FinLens Test Page</h1>
        <p style={{ fontSize: '24px', margin: '10px 0' }}>If you can see this, React is working!</p>
        <p style={{ fontSize: '18px', margin: '10px 0' }}>Time: {new Date().toLocaleString()}</p>
        <button 
          onClick={() => alert('Button clicked!')}
          style={{ 
            padding: '10px 20px', 
            fontSize: '18px', 
            backgroundColor: 'blue', 
            color: 'white', 
            border: 'none',
            borderRadius: '5px'
          }}
        >
          Test Button
        </button>
      </div>
    </>
  );
};

export default TestIndex;