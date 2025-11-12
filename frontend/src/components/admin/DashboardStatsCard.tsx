/**
 * Reusable stats card component.
 * Displays a single metric with title and subtitle.
 */

interface DashboardStatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  icon?: string;
  gradient?: string;
}

export function DashboardStatsCard({ title, value, subtitle, trend, icon, gradient = "from-blue-500 to-blue-600" }: DashboardStatsCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 hover:shadow-xl transition-shadow duration-200">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            {icon && <span className="text-2xl">{icon}</span>}
            <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">{title}</p>
          </div>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-2 font-medium">{subtitle}</p>}
        </div>
        {trend && (
          <div className={`flex items-center space-x-1 px-3 py-1 rounded-full text-sm font-bold ${
            trend.isPositive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            <span>{trend.isPositive ? '↑' : '↓'}</span>
            <span>{trend.isPositive ? '+' : ''}{trend.value}%</span>
          </div>
        )}
        {!trend && (
          <div className={`w-16 h-16 rounded-lg bg-gradient-to-br ${gradient} opacity-10`}></div>
        )}
      </div>
    </div>
  );
}

