'use client';

/**
 * Simple bar chart for leads by status/trade.
 * Uses Recharts for visualization.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface LeadsByStatusChartProps {
  data: Record<string, number>;
}

export function LeadsByStatusChart({ data }: LeadsByStatusChartProps) {
  const chartData = Object.entries(data).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="value" fill="#0ea5e9" />
      </BarChart>
    </ResponsiveContainer>
  );
}

