'use client';
import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { api } from '@/lib/api';

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState([]);
  const [newWorkflow, setNewWorkflow] = useState({
    workflow_id: '',
    workflow_type: 'CLAIM_PROCESSING',
    attributes: '{}',
    actor_id: '',
    source_system: 'INTERNAL_PORTAL'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [auditResults, setAuditResults] = useState<any>(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const response = await api.getWorkflows();
      if (response.ok) {
        const data = await response.json();
        setWorkflows(data);
      }
    } catch (err) {
      setError('Failed to load workflows');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const workflowData = {
        ...newWorkflow,
        attributes: JSON.parse(newWorkflow.attributes)
      };
      const response = await api.createWorkflow(workflowData);
      if (response.ok) {
        loadWorkflows();
        setNewWorkflow({
          workflow_id: '',
          workflow_type: 'CLAIM_PROCESSING',
          attributes: '{}',
          actor_id: '',
          source_system: 'INTERNAL_PORTAL'
        });
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to create workflow');
      }
    } catch (err) {
      setError('Invalid JSON in attributes or connection failed');
    }
  };

  const handleAudit = async (workflowId: string) => {
    setAuditResults(null);
    try {
      const response = await api.auditWorkflow(workflowId);
      if (response.ok) {
        const data = await response.json();
        setAuditResults(data);
      } else {
        setError('Audit failed');
      }
    } catch (err) {
      setError('Failed to connect to server');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="container mx-auto p-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-8">Workflow Submission</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
              <h2 className="text-xl font-semibold mb-4">Submit Workflow Event</h2>
              {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Workflow ID</label>
                  <input
                    type="text"
                    value={newWorkflow.workflow_id}
                    onChange={(e) => setNewWorkflow({...newWorkflow, workflow_id: e.target.value})}
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm p-2 border"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Type</label>
                  <select
                    value={newWorkflow.workflow_type}
                    onChange={(e) => setNewWorkflow({...newWorkflow, workflow_type: e.target.value})}
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm p-2 border"
                  >
                    <option value="CLAIM_PROCESSING">CLAIM_PROCESSING</option>
                    <option value="POLICY_ISSUANCE">POLICY_ISSUANCE</option>
                    <option value="DATA_ACCESS_REQUEST">DATA_ACCESS_REQUEST</option>
                    <option value="APPROVAL_ESCALATION">APPROVAL_ESCALATION</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Actor ID</label>
                  <input
                    type="text"
                    value={newWorkflow.actor_id}
                    onChange={(e) => setNewWorkflow({...newWorkflow, actor_id: e.target.value})}
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm p-2 border"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Attributes (JSON)</label>
                  <textarea
                    value={newWorkflow.attributes}
                    onChange={(e) => setNewWorkflow({...newWorkflow, attributes: e.target.value})}
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm p-2 border h-32 font-mono text-sm"
                    required
                  />
                </div>
                <button
                  type="submit"
                  className="w-full bg-slate-900 text-white p-2 rounded-md hover:bg-slate-800 transition-colors font-medium"
                >
                  Submit Event
                </button>
              </form>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden mb-8">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Workflow ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Actor</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Submitted At</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Action</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                  {workflows.map((wf: any) => (
                    <tr key={wf.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900">{wf.workflow_id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">{wf.workflow_type}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">{wf.actor_id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">{new Date(wf.submitted_at).toLocaleString()}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                        <button 
                          onClick={() => handleAudit(wf.workflow_id)}
                          className="text-indigo-600 hover:text-indigo-900 font-medium"
                        >
                          Run Audit
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {auditResults && (
              <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold">Audit Result: {auditResults.workflow_id}</h2>
                  <a 
                    href={`/audit?id=${auditResults.workflow_id}`}
                    className="text-sm text-indigo-600 hover:underline"
                  >
                    View in Audit Trail
                  </a>
                </div>
                <div className={`p-4 rounded-md mb-4 ${
                  auditResults.decision === 'COMPLIANT' ? 'bg-green-50 text-green-800 border border-green-200' :
                  auditResults.decision === 'NON_COMPLIANT' ? 'bg-red-50 text-red-800 border border-red-200' :
                  'bg-yellow-50 text-yellow-800 border border-yellow-200'
                }`}>
                  <p className="font-bold">Decision: {auditResults.decision}</p>
                  {auditResults.violated_rules.length > 0 && (
                    <p className="mt-2">Violated Rules: {auditResults.violated_rules.join(', ')}</p>
                  )}
                </div>
                <h3 className="font-semibold mb-2">Reasoning Trace:</h3>
                <div className="space-y-3">
                  {auditResults.reasoning_trace.map((trace: any, idx: number) => (
                    <div key={idx} className="bg-slate-50 p-3 rounded border border-slate-200">
                      <p className="font-medium text-slate-800 mb-2">Rule: {trace.rule_id}</p>
                      <div className="space-y-2">
                        {trace.steps?.map((s: any, sIdx: number) => (
                          <div key={sIdx} className="text-xs border-l-2 border-slate-300 pl-2">
                            <span className="font-semibold text-slate-700">{s.step}:</span>
                            <span className={`ml-2 ${
                              s.result === 'Applicable' || s.result === 'Conditions Met' || s.result === 'Obligations Fulfilled' || s.result === 'No Violation' ? 'text-green-600' : 
                              s.result === 'Failed' || s.result === 'Violation Detected' ? 'text-red-600' : 'text-slate-600'
                            }`}>
                              {s.result}
                            </span>
                            {s.detail && <p className="text-slate-500 mt-0.5 italic">{s.detail}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
