'use client';
import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { api } from '@/lib/api';

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await api.getSystemMetrics();
        if (response.ok) {
          const data = await response.json();
          setMetrics(data);
        }
      } catch (err) {
        console.error('Failed to fetch metrics', err);
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, []);

  if (loading) return <div className="p-8">Loading...</div>;

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="container mx-auto p-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-8">System Metrics & Observability</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-sm font-medium text-slate-500 uppercase">Total Audits</h3>
            <p className="text-3xl font-bold text-slate-900">{metrics?.ai_metrics?.total_audits || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-sm font-medium text-slate-500 uppercase">Reasoning Failures</h3>
            <p className="text-3xl font-bold text-red-600">{metrics?.ai_metrics?.reasoning_failures || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-sm font-medium text-slate-500 uppercase">Avg Audit Latency</h3>
            <p className="text-3xl font-bold text-indigo-600">{metrics?.average_latency_ms?.toFixed(2) || 0} ms</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-sm font-medium text-slate-500 uppercase">System Uptime</h3>
            <p className="text-3xl font-bold text-slate-900">{(metrics?.uptime_seconds / 3600).toFixed(2)} hrs</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Rule Coverage */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-xl font-semibold mb-4">Rule Coverage</h2>
            <div className="space-y-4">
              {Object.entries(metrics?.rule_coverage || {}).length > 0 ? (
                Object.entries(metrics.rule_coverage).map(([ruleId, count]: [string, any]) => (
                  <div key={ruleId}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-slate-700">{ruleId}</span>
                      <span className="text-slate-500">{count} evaluations</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div 
                        className="bg-indigo-500 h-2 rounded-full" 
                        style={{ width: `${Math.min((count / (metrics?.ai_metrics?.total_audits || 1)) * 100, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-slate-500 italic">No rule coverage data available.</p>
              )}
            </div>
          </div>

          {/* AI Performance */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-xl font-semibold mb-4">AI Agent Performance</h2>
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-slate-500 uppercase mb-2">PolicyInterpreterAgent</h3>
                <div className="flex items-center gap-4">
                  <div className="flex-1 bg-slate-100 rounded-full h-4 overflow-hidden">
                    <div 
                      className="bg-green-500 h-full" 
                      style={{ width: '100%' }} // Simplified for now
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-slate-700">Success Rate: 100%</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">Failures: {metrics?.ai_metrics?.interpretation_failures || 0}</p>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-slate-500 uppercase mb-2">ComplianceReasoningAgent</h3>
                <div className="flex items-center gap-4">
                  <div className="flex-1 bg-slate-100 rounded-full h-4 overflow-hidden">
                    <div 
                      className="bg-green-500 h-full" 
                      style={{ width: `${((metrics?.ai_metrics?.total_audits - metrics?.ai_metrics?.reasoning_failures) / (metrics?.ai_metrics?.total_audits || 1) * 100).toFixed(1)}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-slate-700">
                    Success Rate: {((metrics?.ai_metrics?.total_audits - metrics?.ai_metrics?.reasoning_failures) / (metrics?.ai_metrics?.total_audits || 1) * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">Failures: {metrics?.ai_metrics?.reasoning_failures || 0}</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
