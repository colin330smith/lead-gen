/**
 * Admin analytics page.
 * Performance metrics, score accuracy, feature importance.
 */

'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { formatPercent } from '@/lib/utils';
import { AnalyticsChart } from '@/components/admin/AnalyticsChart';

export default function AdminAnalyticsPage() {
  const [selectedTrade, setSelectedTrade] = useState<string>('');

  const { data: scoreAccuracy, isLoading: accuracyLoading } = useQuery({
    queryKey: ['score-accuracy', selectedTrade],
    queryFn: () => api.getScoreAccuracy(selectedTrade || undefined),
  });

  const { data: featureImportance, isLoading: featureLoading } = useQuery({
    queryKey: ['feature-importance', selectedTrade],
    queryFn: () => api.getFeatureImportance(selectedTrade || undefined),
  });

  const { data: modelPerformance, isLoading: performanceLoading } = useQuery({
    queryKey: ['model-performance', selectedTrade],
    queryFn: () => api.getModelPerformance(selectedTrade || undefined),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics & Performance</h1>
          <p className="text-gray-600 mt-2">Model performance and conversion analytics</p>
        </div>
        <select
          value={selectedTrade}
          onChange={(e) => setSelectedTrade(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-md"
        >
          <option value="">All Trades</option>
          <option value="roofing">Roofing</option>
          <option value="hvac">HVAC</option>
          <option value="siding">Siding</option>
          <option value="electrical">Electrical</option>
        </select>
      </div>

      {/* Score Accuracy */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Score Accuracy Analysis</h2>
        {accuracyLoading ? (
          <div className="text-gray-500">Loading...</div>
        ) : scoreAccuracy?.error ? (
          <div className="text-red-600">{scoreAccuracy.error}</div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Overall Conversion Rate</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatPercent(scoreAccuracy?.overall_conversion_rate)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Data Points</p>
                <p className="text-2xl font-bold text-gray-900">{scoreAccuracy?.data_points || 0}</p>
              </div>
            </div>
            {scoreAccuracy?.calibration_data && (
              <AnalyticsChart data={scoreAccuracy.calibration_data} />
            )}
          </div>
        )}
      </div>

      {/* Feature Importance */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Feature Importance</h2>
        {featureLoading ? (
          <div className="text-gray-500">Loading...</div>
        ) : featureImportance?.error ? (
          <div className="text-red-600">{featureImportance.error}</div>
        ) : (
          <div className="space-y-4">
            {featureImportance?.feature_importance && (
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(featureImportance.feature_importance).map(([feature, data]: [string, any]) => (
                  <div key={feature} className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-gray-700 mb-2 capitalize">{feature.replace('_', ' ')}</p>
                    <p className="text-xs text-gray-500">Difference: {data.difference?.toFixed(4) || 'N/A'}</p>
                    <p className="text-xs text-gray-500">
                      Converted Avg: {data.converted_avg?.toFixed(2) || 'N/A'}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Model Performance Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Model Performance Summary</h2>
        {performanceLoading ? (
          <div className="text-gray-500">Loading...</div>
        ) : (
          <div className="text-sm text-gray-600">
            <p>Trade: {modelPerformance?.trade || 'All'}</p>
            <p>Data points: {modelPerformance?.score_accuracy?.data_points || 0}</p>
          </div>
        )}
      </div>
    </div>
  );
}

