'use client';

/**
 * Analytics chart component.
 * Displays calibration data visualization.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface AnalyticsChartProps {
  data: Record<string, {
    total_leads: number;
    converted: number;
    conversion_rate: number;
    expected_rate: number;
  }>;
}

export function AnalyticsChart({ data }: AnalyticsChartProps) {
  const chartData = Object.entries(data).map(([range, stats]) => ({
    range,
    actual: stats.conversion_rate,
    expected: stats.expected_rate,
    total: stats.total_leads,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="range" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="actual" fill="#0ea5e9" name="Actual Rate" />
        <Bar dataKey="expected" fill="#94a3b8" name="Expected Rate" />
      </BarChart>
    </ResponsiveContainer>
  );
}

