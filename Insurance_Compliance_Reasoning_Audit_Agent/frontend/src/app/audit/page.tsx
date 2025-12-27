'use client';
import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Navbar from '@/components/Navbar';
import { api } from '@/lib/api';

function AuditContent() {
  const searchParams = useSearchParams();
  const [workflowId, setWorkflowId] = useState(searchParams.get('id') || '');
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedDecision, setSelectedDecision] = useState<any>(null);
  const [workflowEvent, setWorkflowEvent] = useState<any>(null);

  useEffect(() => {
    const id = searchParams.get('id');
    if (id) {
      setWorkflowId(id);
      fetchDecisions(id);
    } else {
      fetchAllDecisions();
    }
  }, [searchParams]);

  const fetchAllDecisions = async () => {
    setLoading(true);
    try {
      const response = await api.getAllDecisions();
      if (response.ok) {
        const data = await response.json();
        setDecisions(data);
      }
    } catch (err) {
      setError('Failed to load audit trail');
    } finally {
      setLoading(false);
    }
  };

  const fetchDecisions = async (id: string) => {
    setLoading(true);
    setError('');
    try {
      const response = await api.getDecisions(id);
      if (response.ok) {
        const data = await response.json();
        setDecisions(data);
        if (data.length === 0) {
          setError('No decisions found for this workflow');
        }
      } else {
        setError('No decisions found for this workflow');
      }
    } catch (err) {
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (decision: any) => {
    setSelectedDecision(decision);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/workflows/${decision.workflow_id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        // Find the event that matches the decision time or is just before it
        setWorkflowEvent(data[0]); // For now just take the first one
      }
    } catch (err) {
      console.error('Failed to fetch workflow event', err);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workflowId.trim()) {
      fetchAllDecisions();
      return;
    }
    fetchDecisions(workflowId);
  };

  const handleReplay = async (wfId: string, decisionId: number) => {
    try {
      const response = await api.replayDecision(wfId, decisionId);
      if (response.ok) {
        if (workflowId) {
          fetchDecisions(workflowId);
        } else {
          fetchAllDecisions();
        }
        alert('Replay successful. New decision added to trail.');
      } else {
        alert('Replay failed');
      }
    } catch (err) {
      alert('Failed to connect to server');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="container mx-auto p-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-8">Audit Trail & Replay</h1>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200 mb-8">
          <form onSubmit={handleSearch} className="flex gap-4">
            <input
              type="text"
              placeholder="Enter Workflow ID (leave empty to see all)"
              value={workflowId}
              onChange={(e) => setWorkflowId(e.target.value)}
              className="flex-1 rounded-md border-slate-300 shadow-sm p-2 border"
            />
            <button
              type="submit"
              className="bg-slate-900 text-white px-6 py-2 rounded-md hover:bg-slate-800 transition-colors font-medium"
              disabled={loading}
            >
              {loading ? 'Searching...' : 'Search Audit Trail'}
            </button>
          </form>
        </div>

        {error && <p className="text-red-500 mb-4">{error}</p>}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Decisions List */}
          <div className="lg:col-span-1 space-y-4 overflow-y-auto max-h-[calc(100vh-300px)]">
            {decisions.map((decision: any) => (
              <div 
                key={decision.id} 
                onClick={() => handleViewDetails(decision)}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  selectedDecision?.id === decision.id 
                    ? 'bg-indigo-50 border-indigo-200 shadow-sm' 
                    : 'bg-white border-slate-200 hover:border-indigo-200'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-bold text-slate-400 uppercase">ID: {decision.id}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    decision.decision === 'COMPLIANT' ? 'bg-green-100 text-green-800' :
                    decision.decision === 'NON_COMPLIANT' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {decision.decision}
                  </span>
                </div>
                <p className="text-sm font-semibold text-slate-900 truncate">Workflow: {decision.workflow_id}</p>
                <p className="text-xs text-slate-500 mt-1">{new Date(decision.created_at).toLocaleString()}</p>
              </div>
            ))}
          </div>

          {/* Detail View */}
          <div className="lg:col-span-2">
            {selectedDecision ? (
              <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200 sticky top-8">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900">Audit Detail</h2>
                    <p className="text-slate-500">Workflow ID: {selectedDecision.workflow_id}</p>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => handleReplay(selectedDecision.workflow_id, selectedDecision.id)}
                      className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 text-sm font-medium transition-colors"
                    >
                      Replay Audit
                    </button>
                  </div>
                </div>

                <div className="space-y-8">
                  {/* Event Data */}
                  <div>
                    <h3 className="text-sm font-semibold text-slate-500 uppercase mb-3 border-b pb-1">Workflow Event Data</h3>
                    {workflowEvent ? (
                      <div className="bg-slate-50 p-4 rounded border border-slate-100 space-y-3">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-xs text-slate-400 font-medium uppercase">Type</p>
                            <p className="text-sm font-medium">{workflowEvent.workflow_type}</p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-400 font-medium uppercase">Actor</p>
                            <p className="text-sm font-medium">{workflowEvent.actor_id}</p>
                          </div>
                        </div>
                        <div>
                          <p className="text-xs text-slate-400 font-medium uppercase mb-1">Attributes</p>
                          <pre className="text-xs bg-white p-3 rounded border border-slate-200 overflow-x-auto font-mono">
                            {JSON.stringify(workflowEvent.attributes, null, 2)}
                          </pre>
                        </div>
                      </div>
                    ) : (
                      <div className="animate-pulse bg-slate-100 h-32 rounded"></div>
                    )}
                  </div>

                  {/* Reasoning Trace */}
                  <div>
                    <h3 className="text-sm font-semibold text-slate-500 uppercase mb-3 border-b pb-1">AI Reasoning Trace</h3>
                    <div className="space-y-4">
                      {selectedDecision.reasoning_trace.map((trace: any, idx: number) => (
                        <div key={idx} className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                          <div className="flex justify-between items-center mb-3">
                            <p className="font-bold text-slate-800">{trace.rule_id}</p>
                            <span className="text-xs text-slate-400">v{selectedDecision.rule_versions[trace.rule_id]}</span>
                          </div>
                          <div className="space-y-3">
                            {trace.steps?.map((s: any, sIdx: number) => (
                              <div key={sIdx} className="flex gap-3">
                                <div className="flex flex-col items-center">
                                  <div className={`w-2 h-2 rounded-full mt-1.5 ${
                                    s.result.includes('Failed') || s.result.includes('Violation') ? 'bg-red-500' : 'bg-green-500'
                                  }`}></div>
                                  {sIdx < trace.steps.length - 1 && <div className="w-0.5 flex-1 bg-slate-100 my-1"></div>}
                                </div>
                                <div className="pb-2">
                                  <p className="text-xs font-bold text-slate-700">{s.step}</p>
                                  <p className={`text-xs font-medium ${
                                    s.result.includes('Failed') || s.result.includes('Violation') ? 'text-red-600' : 'text-green-600'
                                  }`}>{s.result}</p>
                                  {s.detail && <p className="text-xs text-slate-500 mt-0.5 italic">{s.detail}</p>}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Final Decision */}
                  <div className={`p-4 rounded-lg border-2 ${
                    selectedDecision.decision === 'COMPLIANT' ? 'bg-green-50 border-green-200' :
                    selectedDecision.decision === 'NON_COMPLIANT' ? 'bg-red-50 border-red-200' :
                    'bg-yellow-50 border-yellow-200'
                  }`}>
                    <p className="text-xs font-bold uppercase text-slate-500 mb-1">Final Compliance Decision</p>
                    <p className={`text-2xl font-black ${
                      selectedDecision.decision === 'COMPLIANT' ? 'text-green-700' :
                      selectedDecision.decision === 'NON_COMPLIANT' ? 'text-red-700' :
                      'text-yellow-700'
                    }`}>
                      {selectedDecision.decision}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white p-12 rounded-lg border border-dashed border-slate-300 flex flex-col items-center justify-center text-slate-400">
                <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-lg font-medium">Select an audit from the list to view details</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default function AuditPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Loading Audit Trail...</div>}>
      <AuditContent />
    </Suspense>
  );
}
