'use client';
import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { api } from '@/lib/api';

export default function RulesPage() {
  const [rules, setRules] = useState([]);
  const [newRule, setNewRule] = useState({
    rule_id: '',
    category: 'PRIVACY',
    rule_text: '',
    severity: 'MEDIUM',
    version: '1.0.0'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedRule, setSelectedRule] = useState<any>(null);
  const [structuredRules, setStructuredRules] = useState<any[]>([]);

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      const response = await api.getRules();
      if (response.ok) {
        const data = await response.json();
        setRules(data);
      }
    } catch (err) {
      setError('Failed to load rules');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (rule: any) => {
    setSelectedRule(rule);
    try {
      const response = await api.getStructuredRules(rule.rule_id);
      if (response.ok) {
        const data = await response.json();
        setStructuredRules(data);
      }
    } catch (err) {
      console.error('Failed to load structured rules', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const response = await api.createRule(newRule);
      if (response.ok) {
        loadRules();
        setNewRule({
          rule_id: '',
          category: 'PRIVACY',
          rule_text: '',
          severity: 'MEDIUM',
          version: '1.0.0'
        });
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to create rule');
      }
    } catch (err) {
      setError('Failed to connect to server');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="container mx-auto p-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-8">Rule Management</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
              <h2 className="text-xl font-semibold mb-4 text-gray-900">Create New Rule</h2>
              {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Rule ID</label>
                  <input
                    type="text"
                    value={newRule.rule_id}
                    onChange={(e) => setNewRule({...newRule, rule_id: e.target.value})}
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm p-2 border text-gray-900"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Category</label>
                  <select
                    value={newRule.category}
                    onChange={(e) => setNewRule({...newRule, category: e.target.value})}
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm p-2 border text-gray-600"
                  >
                    <option value="PRIVACY">PRIVACY</option>
                    <option value="SECURITY">SECURITY</option>
                    <option value="OPERATIONAL">OPERATIONAL</option>
                    <option value="FINANCIAL">FINANCIAL</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 ">Severity</label>
                  <select
                    value={newRule.severity}
                    onChange={(e) => setNewRule({...newRule, severity: e.target.value})}
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm p-2 border text-gray-600"
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Version</label>
                  <input
                    type="text"
                    value={newRule.version}
                    onChange={(e) => setNewRule({...newRule, version: e.target.value})}
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm p-2 border text-gray-600"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Rule Text</label>
                  <textarea
                    value={newRule.rule_text}
                    onChange={(e) => setNewRule({...newRule, rule_text: e.target.value})}
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm p-2 border h-32"
                    required
                  />
                </div>
                <button
                  type="submit"
                  className="w-full bg-slate-900 text-white p-2 rounded-md hover:bg-slate-800 transition-colors font-medium"
                >
                  Deploy Rule
                </button>
              </form>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Rule ID</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Category</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Severity</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Version</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                  {rules.map((rule: any) => (
                    <tr key={rule.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900">{rule.rule_id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">{rule.category}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          rule.severity === 'HIGH' ? 'bg-red-100 text-red-800' : 
                          rule.severity === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' : 
                          'bg-green-100 text-green-800'
                        }`}>
                          {rule.severity}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">{rule.version}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">{rule.status}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-indigo-600 font-semibold hover:text-indigo-900 cursor-pointer" onClick={() => handleViewDetails(rule)}>
                        View Details
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {selectedRule && (
              <div className="mt-8 bg-white p-6 rounded-lg shadow-sm border border-slate-200">
                <div className="flex justify-between items-start mb-4">
                  <h2 className="text-2xl font-bold text-slate-900">Rule Details: {selectedRule.rule_id}</h2>
                  <button onClick={() => setSelectedRule(null)} className="text-slate-600 hover:text-slate-900 font-bold">✕</button>
                </div>
                
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-bold text-slate-600 uppercase mb-2">Human-Readable Text</h3>
                    <p className="text-slate-800 bg-slate-50 p-4 rounded border border-slate-100">{selectedRule.rule_text}</p>
                  </div>

                  {structuredRules.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold text-slate-500 uppercase mb-2">AI Structured Interpretation (Latest)</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-4 bg-blue-50 rounded border border-blue-100">
                          <h4 className="font-medium text-blue-900 mb-1">Applicability</h4>
                          <ul className="text-sm text-blue-800 list-disc list-inside">
                            {structuredRules[structuredRules.length - 1].applicability_conditions.map((c: string, i: number) => (
                              <li key={i}>{c}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="p-4 bg-green-50 rounded border border-green-100">
                          <h4 className="font-medium text-green-900 mb-1">Obligations</h4>
                          <ul className="text-sm text-green-800 list-disc list-inside">
                            {structuredRules[structuredRules.length - 1].obligations.map((o: string, i: number) => (
                              <li key={i}>{o}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="p-4 bg-amber-50 rounded border border-amber-100">
                          <h4 className="font-medium text-amber-900 mb-1">Exceptions</h4>
                          <ul className="text-sm text-amber-800 list-disc list-inside">
                            {structuredRules[structuredRules.length - 1].exceptions.map((e: string, i: number) => (
                              <li key={i}>{e}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}

                  <div>
                    <h3 className="text-sm font-semibold text-slate-500 uppercase mb-2">Version History</h3>
                    <div className="space-y-2">
                      {structuredRules.map((sr: any) => (
                        <div key={sr.id} className="flex justify-between items-center text-sm p-2 border-b border-slate-100">
                          <span className="font-medium">v{sr.version}</span>
                          <span className="text-slate-500">{new Date(sr.created_at).toLocaleDateString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
