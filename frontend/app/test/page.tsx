'use client';

import { useState } from 'react';

export default function TestPage() {
  const [status, setStatus] = useState<string>('Not tested');
  const [incidents, setIncidents] = useState<string[]>([]);
  const [error, setError] = useState<string>('');

  const testHealth = async () => {
    try {
      setStatus('Testing...');
      const response = await fetch('http://localhost:8000/health');
      const health = await response.json();
      setStatus(`✓ Backend healthy! Model: ${health.gemini_model}`);
      setError('');
    } catch (err) {
      setStatus('✗ Backend connection failed');
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const testIncidents = async () => {
    try {
      setStatus('Loading incidents...');
      const response = await fetch('http://localhost:8000/api/incidents/');
      const list = await response.json();
      setIncidents(list);
      setStatus(`✓ Found ${list.length} incident(s)`);
      setError('');
    } catch (err) {
      setStatus('✗ Failed to load incidents');
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">WardenXT API Test</h1>
        
        <div className="space-y-4">
          {/* Health Check */}
          <div className="bg-gray-900 p-6 rounded-lg border border-gray-800">
            <h2 className="text-xl font-semibold mb-4">Backend Health Check</h2>
            <button
              onClick={testHealth}
              className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg font-medium transition-colors"
            >
              Test Backend Connection
            </button>
            <div className="mt-4">
              <p className="text-lg">{status}</p>
              {error && (
                <p className="text-red-500 mt-2">Error: {error}</p>
              )}
            </div>
          </div>

          {/* Incidents List */}
          <div className="bg-gray-900 p-6 rounded-lg border border-gray-800">
            <h2 className="text-xl font-semibold mb-4">Load Incidents</h2>
            <button
              onClick={testIncidents}
              className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded-lg font-medium transition-colors"
            >
              Fetch Incidents
            </button>
            {incidents.length > 0 && (
              <div className="mt-4">
                <p className="font-semibold mb-2">Incidents Found:</p>
                <ul className="space-y-2">
                  {incidents.map((id) => (
                    <li key={id} className="bg-gray-800 p-3 rounded">
                      {id}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Instructions */}
          <div className="bg-blue-950 p-6 rounded-lg border border-blue-800">
            <h3 className="text-lg font-semibold mb-2">📝 Instructions:</h3>
            <ol className="list-decimal list-inside space-y-2 text-gray-300">
              <li>Backend is running on http://localhost:8000 ✓</li>
              <li>Click "Test Backend Connection" to verify API</li>
              <li>Click "Fetch Incidents" to load available incidents</li>
              <li>If both work, you're ready to build the dashboard!</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}