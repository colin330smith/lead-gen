'use client';

/**
 * Filter bar for leads management.
 * Provides efficient filtering and search capabilities.
 */

interface LeadsFilterBarProps {
  filters: {
    trade: string;
    status: string;
    contractor_id: string;
    min_score: number;
    limit: number;
  };
  onFilterChange: (filters: Partial<LeadsFilterBarProps['filters']>) => void;
}

const TRADES = ['roofing', 'hvac', 'siding', 'electrical'];
const STATUSES = ['generated', 'assigned', 'delivered', 'converted', 'expired'];

export function LeadsFilterBar({ filters, onFilterChange }: LeadsFilterBarProps) {
  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
        <button
          onClick={() => onFilterChange({ trade: '', status: '', contractor_id: '', min_score: 0.0 })}
          className="text-sm text-primary-600 hover:text-primary-700 font-medium"
        >
          Clear All
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">Trade</label>
          <select
            value={filters.trade}
            onChange={(e) => onFilterChange({ trade: e.target.value })}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all bg-white hover:border-gray-400"
          >
            <option value="">All Trades</option>
            {TRADES.map((trade) => (
              <option key={trade} value={trade}>
                {trade.charAt(0).toUpperCase() + trade.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">Status</label>
          <select
            value={filters.status}
            onChange={(e) => onFilterChange({ status: e.target.value })}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all bg-white hover:border-gray-400"
          >
            <option value="">All Statuses</option>
            {STATUSES.map((status) => (
              <option key={status} value={status}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">Min Score</label>
          <input
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={filters.min_score}
            onChange={(e) => onFilterChange({ min_score: parseFloat(e.target.value) || 0 })}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all bg-white hover:border-gray-400"
            placeholder="0.0"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">Limit</label>
          <select
            value={filters.limit}
            onChange={(e) => onFilterChange({ limit: parseInt(e.target.value) })}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all bg-white hover:border-gray-400"
          >
            <option value="50">50</option>
            <option value="100">100</option>
            <option value="250">250</option>
            <option value="500">500</option>
          </select>
        </div>
      </div>
    </div>
  );
}

