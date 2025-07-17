'use client';

import React, { useState } from 'react';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'upload' | 'analyze'>('analyze');
  const [jobDescription, setJobDescription] = useState('');
  const [files, setFiles] = useState<FileList | null>(null);
  const [conversation, setConversation] = useState<Array<{role: string, content: string}>>([]);
  const [loading, setLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFiles(e.target.files);
  };

  const handleUpload = async () => {
    if (!files || files.length === 0) {
      alert('Please select at least one file');
      return;
    }

    setUploadLoading(true);
    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (!file.name.endsWith('.txt')) {
          setConversation(prev => [
            ...prev,
            { role: 'error', content: `Skipped ${file.name}: Only .txt files are supported` }
          ]);
          continue;
        }

        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch('http://localhost:8000/upload-resume', {
          method: 'POST',
          body: formData,
        });

        const data = await res.json();
        
        setConversation(prev => [
          ...prev,
          { 
            role: 'system', 
            content: `Uploaded ${file.name}: ${data.message} (Resume ID: ${data.resume_id}, ${data.num_chunks} chunks)` 
          }
        ]);
      }
    } catch (err) {
      console.error(err);
      setConversation(prev => [
        ...prev,
        { role: 'error', content: 'Error uploading resume(s)' }
      ]);
    } finally {
      setUploadLoading(false);
      setFiles(null);
    }
  };

  const handleAnalyze = async () => {
    if (!jobDescription) {
      alert('Please enter a question or command');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('input_text', jobDescription);
      
      if (sessionId) {
        formData.append('session_id', sessionId);
      }

      const res = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      
      if (data.session_id) {
        setSessionId(data.session_id);
      }
      
      setConversation(prev => [
        ...prev,
        { role: 'user', content: jobDescription },
        { role: 'assistant', content: data.response }
      ]);
      
      setJobDescription('');
    } catch (err) {
      console.error(err);
      setConversation(prev => [
        ...prev,
        { role: 'user', content: jobDescription },
        { role: 'error', content: 'Error connecting to backend' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-6">
      <div className="bg-white rounded-2xl shadow-md p-8 w-full max-w-2xl text-center">
        {/* Tab Navigation */}
        <div className="flex mb-6 border-b border-gray-200">
          <button
            className={`py-2 px-4 font-medium ${activeTab === 'upload' ? 'text-purple-600 border-b-2 border-purple-600' : 'text-gray-500'}`}
            onClick={() => setActiveTab('upload')}
          >
            Upload
          </button>
          <button
            className={`py-2 px-4 font-medium ${activeTab === 'analyze' ? 'text-purple-600 border-b-2 border-purple-600' : 'text-gray-500'}`}
            onClick={() => setActiveTab('analyze')}
          >
            Analyze
          </button>
        </div>

        {activeTab === 'upload' ? (
          <div className="upload-section">
            <p className="mb-6 text-black">Upload resumes to database</p>
            <div className="border-2 border-dashed border-gray-300 rounded-md p-6 mb-4">
              <input
                type="file"
                accept=".txt"
                multiple
                onChange={handleFileChange}
                className="mb-4"
              />
              <p className="text-sm text-gray-500 mb-4">TXT files only</p>
              <button
                onClick={handleUpload}
                disabled={uploadLoading || !files || files.length === 0}
                className="bg-purple-400 text-white font-semibold py-2 px-6 rounded-md hover:bg-purple-500 transition disabled:opacity-50"
              >
                {uploadLoading ? 'Uploading...' : 'Upload Resumes'}
              </button>
              {files && files.length > 0 && (
                <div className="mt-4 text-sm text-gray-600">
                  Selected: {files.length} file(s)
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="analyze-section">
            <p className="mb-6 text-black">Analyze resumes or query metadata (start with \)</p>
            
            <textarea
              className="w-full border rounded-md p-2 mb-4 text-black"
              rows={5}
              placeholder="Enter your question or command (e.g., \\skills=python min_exp=3)"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleAnalyze();
                }
              }}
            />

            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="bg-purple-400 text-white font-semibold py-2 px-6 rounded-md hover:bg-purple-500 transition"
            >
              {loading ? 'Processing...' : 'Submit'}
            </button>
          </div>
        )}

        {conversation.length > 0 && (
          <div className="mt-6 space-y-4 text-left">
            {conversation.map((msg, index) => (
              <div 
                key={index} 
                className={`p-3 rounded-md ${
                  msg.role === 'user' ? 'bg-blue-50 text-blue-900' : 
                  msg.role === 'error' ? 'bg-red-50 text-red-900' :
                  msg.role === 'system' ? 'bg-green-50 text-green-900' :
                  'bg-gray-100 text-gray-900'
                }`}
              >
                <strong className="capitalize">{msg.role}:</strong> {msg.content}
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}