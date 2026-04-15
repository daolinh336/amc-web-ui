import React, { useState } from 'react';
import './BulkImport.css';

const BulkImport = () => {
  const [file, setFile] = useState(null);
  const [topic, setTopic] = useState('');
  const [username, setUsername] = useState('');
  const [isPublic, setIsPublic] = useState(true);
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
    if (!username || username.trim() === '') {
      alert('Username is required');
      return;
    }
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('topic', topic || 'bulk');
    formData.append('username', username);
    formData.append('isPublic', isPublic);

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
          placeholder="Username (required)"
          required
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <div style={{ marginTop: '10px', marginBottom: '10px' }}>
          <label style={{ marginRight: '20px' }}>
            <input
              type="radio"
              name="visibility"
              value="public"
              checked={isPublic === true}
              onChange={() => setIsPublic(true)}
            />
            {' '}Public
          </label>
          <label>
            <input
              type="radio"
              name="visibility"
              value="private"
              checked={isPublic === false}
              onChange={() => setIsPublic(false)}
            />
            {' '}Private
          </label>
        </div>
        <button onClick={handleUpload} disabled={loading}>
          {loading ? 'Uploading...' : 'Import'}
        </button>
      </div>
      {result && (
        <div className="result">
          {result.success ? (
            <div>
              <p>✓ Imported {result.imported} questions successfully.</p>
              {result.duplicates && result.duplicates.length > 0 && (
                <p style={{color: '#ff9800', fontWeight: 'bold'}}>
                  ⚠️ {result.duplicates.length} duplicate question(s) were skipped (Questions {result.duplicates.map(i => i + 1).join(', ')})
                </p>
              )}
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