/**
 * Admin dashboard home page.
 * Displays system overview and key metrics.
 */

'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { formatNumber, formatPercent, formatCurrency } from '@/lib/utils';
import { DashboardStatsCard } from '@/components/admin/DashboardStatsCard';
import { LeadsByStatusChart } from '@/components/admin/LeadsByStatusChart';
import { RecentLeadsTable } from '@/components/admin/RecentLeadsTable';

export default function AdminDashboardPage() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.getDashboardStats(),
  });

  const { data: recentLeads } = useQuery({
    queryKey: ['recent-leads'],
    queryFn: () => api.listLeads({ limit: 10, offset: 0 }),
    enabled: !isLoading,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading dashboard data. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl p-6 border border-primary-100">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-3">
          <span className="text-4xl">📊</span>
          <span>Dashboard</span>
        </h1>
        <p className="text-gray-600 mt-2 font-medium">System overview and key metrics</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardStatsCard
          title="Total Leads"
          value={formatNumber(stats?.total_leads)}
          subtitle="All time"
          icon="🎯"
          gradient="from-blue-500 to-blue-600"
        />
        <DashboardStatsCard
          title="Conversion Rate"
          value={formatPercent(stats?.conversion_rate)}
          subtitle="Overall"
          icon="📈"
          gradient="from-green-500 to-green-600"
        />
        <DashboardStatsCard
          title="Recent Leads (7d)"
          value={formatNumber(stats?.recent_leads_7d)}
          subtitle="Last week"
          icon="⚡"
          gradient="from-purple-500 to-purple-600"
        />
        <DashboardStatsCard
          title="Avg Intent Score"
          value={stats?.avg_intent_score?.toFixed(2) || 'N/A'}
          subtitle="All leads"
          icon="⭐"
          gradient="from-orange-500 to-orange-600"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <span className="text-2xl">📊</span>
            <h2 className="text-lg font-bold text-gray-900">Leads by Status</h2>
          </div>
          <LeadsByStatusChart data={stats?.leads_by_status || {}} />
        </div>

        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <span className="text-2xl">🏗️</span>
            <h2 className="text-lg font-bold text-gray-900">Leads by Trade</h2>
          </div>
          <LeadsByStatusChart data={stats?.leads_by_trade || {}} />
        </div>
      </div>

      {/* Recent Leads */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-6 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">⚡</span>
            <h2 className="text-lg font-bold text-gray-900">Recent Leads</h2>
          </div>
        </div>
        <RecentLeadsTable leads={recentLeads?.leads || []} />
      </div>
    </div>
  );
}

