import React, { useState } from 'react';
import './BulkImport.css';

const BulkImport = () => {
  const [file, setFile] = useState(null);
  const [topic, setTopic] = useState('');
  const [username, setUsername] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a file');
      return;
    }
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('topic', topic || 'bulk');
    formData.append('username', username || 'bulk');

    try {
      const response = await fetch('/upload_questions', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ success: false, message: 'Upload failed' });
    }
    setLoading(false);
  };

  return (
    <div className="bulk-import">
      <h2>Bulk Import Questions</h2>
      <p>Upload AMC-TXT (.txt) or LaTeX (.tex) file containing questions.</p>
      <div className="upload-section">
        <input type="file" accept=".txt,.tex" onChange={handleFileChange} />
        <input
          type="text"
          placeholder="Topic (optional)"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        />
        <input
          type="text"
          placeholder="Username (optional)"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <button onClick={handleUpload} disabled={loading}>
          {loading ? 'Uploading...' : 'Import'}
        </button>
      </div>
      {result && (
        <div className="result">
          {result.success ? (
            <div>
              <p>Imported {result.imported} questions successfully.</p>
                <table border="1" cellPadding="8" cellSpacing="0" style={{width: '100%', borderCollapse: 'collapse', marginTop: '10px'}}>
                    <thead style={{background: '#e8eaf6'}}>
                        <tr>
                        <th style={{width: '60px'}}>#</th>
                        <th>Content</th>
                        <th style={{width: '90px'}}>Type</th>
                        <th style={{width: '80px'}}>Correct</th>
                        </tr>
                    </thead>
                    <tbody>
                        {result.questions.map((q, idx) => (
                        <tr key={idx} style={{background: idx % 2 === 0 ? '#fff' : '#f5f5f5'}}>
                            <td style={{fontFamily: 'monospace', fontSize: '11px', color: '#888'}}>{q.id}</td>
                            <td>{q.questionText}</td>
                            <td style={{textAlign: 'center'}}>
                            <span>{q.type}</span>
                            </td>
                            <td style={{textAlign: 'center', color: '#2e7d32', fontWeight: '500'}}>{q.correct_count}</td>
                        </tr>
                        ))}
                    </tbody>
                </table>
              {result.errors.length > 0 && (
                <div>
                  <h3>Errors:</h3>
                  <ul>
                    {result.errors.map((err, idx) => (
                      <li key={idx}>
                        Question {err.question}: {err.error}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p>Error: {result.message}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default BulkImport;