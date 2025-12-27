'use client';
import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { api } from '@/lib/api';

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.getDashboardStats();
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (err) {
        console.error('Failed to fetch stats', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <div className="p-8">Loading...</div>;

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="container mx-auto p-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-8">Compliance Dashboard</h1>
        
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-sm font-medium text-slate-500 uppercase">Total Audits</h3>
            <p className="text-3xl font-bold text-slate-900">{stats?.total_audits || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-sm font-medium text-slate-500 uppercase">Compliant</h3>
            <p className="text-3xl font-bold text-green-600">
              {stats?.compliance_stats?.COMPLIANT || 0}
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-sm font-medium text-slate-500 uppercase">Non-Compliant</h3>
            <p className="text-3xl font-bold text-red-600">
              {stats?.compliance_stats?.NON_COMPLIANT || 0}
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-sm font-medium text-slate-500 uppercase">Requires Review</h3>
            <p className="text-3xl font-bold text-amber-600">
              {stats?.compliance_stats?.REQUIRES_REVIEW || 0}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Audits */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-xl font-semibold mb-4">Recent Audits</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">Workflow ID</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">Decision</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {stats?.recent_audits?.map((audit: any) => (
                    <tr key={audit.id}>
                      <td className="px-4 py-2 text-sm text-slate-900">{audit.workflow_id}</td>
                      <td className="px-4 py-2 text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          audit.decision === 'COMPLIANT' ? 'bg-green-100 text-green-800' :
                          audit.decision === 'NON_COMPLIANT' ? 'bg-red-100 text-red-800' :
                          'bg-amber-100 text-amber-800'
                        }`}>
                          {audit.decision}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-sm text-slate-500">
                        {new Date(audit.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Alerts / Flags */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-xl font-semibold mb-4 text-red-600">Critical Alerts</h2>
            <div className="space-y-4">
              {stats?.alerts?.length > 0 ? (
                stats.alerts.map((alert: any) => (
                  <div key={alert.id} className="p-4 bg-red-50 border border-red-100 rounded-md">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-semibold text-red-900">Non-Compliant Workflow</p>
                        <p className="text-sm text-red-700">ID: {alert.workflow_id}</p>
                      </div>
                      <a 
                        href={`/audit?id=${alert.workflow_id}`}
                        className="text-xs font-medium text-red-600 hover:underline"
                      >
                        Investigate →
                      </a>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-slate-500 italic">No critical alerts at this time.</p>
              )}
            </div>
          </div>
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-xl font-semibold mb-2">Rule Management</h2>
            <p className="text-slate-600">Manage and version compliance rules.</p>
            <a href="/rules" className="mt-4 inline-block text-indigo-600 hover:underline">View Rules →</a>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-xl font-semibold mb-2">Workflows</h2>
            <p className="text-slate-600">Submit and monitor operational workflows.</p>
            <a href="/workflows" className="mt-4 inline-block text-indigo-600 hover:underline">View Workflows →</a>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-xl font-semibold mb-2">Metrics</h2>
            <p className="text-slate-600">System health and AI performance.</p>
            <a href="/metrics" className="mt-4 inline-block text-indigo-600 hover:underline">View Metrics →</a>
          </div>
        </div>
      </main>
    </div>
  );
}
