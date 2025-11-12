/**
 * Model refinement and calibration page.
 * A/B testing, calibration, performance monitoring.
 */

'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { formatPercent } from '@/lib/utils';

export default function AdminModelPage() {
  const queryClient = useQueryClient();
  const [selectedTrade, setSelectedTrade] = useState<string>('');

  const { data: calibration, isLoading: calibrationLoading } = useQuery({
    queryKey: ['calibration-adjustments', selectedTrade],
    queryFn: () => api.getCalibrationAdjustments(selectedTrade || undefined),
  });

  const { data: recommendations } = useQuery({
    queryKey: ['calibration-recommendations', selectedTrade],
    queryFn: () => api.getCalibrationRecommendations(selectedTrade || undefined),
  });

  const { data: modelPerformance } = useQuery({
    queryKey: ['model-performance-check'],
    queryFn: () => api.checkModelPerformance('v1.0'),
  });

  const refinementCheckMutation = useMutation({
    mutationFn: () => api.runRefinementCheck(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['model-performance-check'] });
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Model Refinement</h1>
          <p className="text-gray-600 mt-2">Score calibration and model optimization</p>
        </div>
        <div className="flex space-x-3">
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
          <button
            onClick={() => refinementCheckMutation.mutate()}
            disabled={refinementCheckMutation.isPending}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
          >
            {refinementCheckMutation.isPending ? 'Checking...' : 'Run Refinement Check'}
          </button>
        </div>
      </div>

      {/* Model Performance Status */}
      {modelPerformance && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Model Performance Status</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Conversion Rate</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatPercent(modelPerformance.conversion_rate)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Needs Refinement</p>
              <p
                className={`text-2xl font-bold ${
                  modelPerformance.needs_refinement ? 'text-red-600' : 'text-green-600'
                }`}
              >
                {modelPerformance.needs_refinement ? 'Yes' : 'No'}
              </p>
            </div>
          </div>
          {modelPerformance.recommendations && modelPerformance.recommendations.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-sm font-medium text-gray-700">Recommendations:</p>
              {modelPerformance.recommendations.map((rec: any, idx: number) => (
                <div key={idx} className="bg-yellow-50 border border-yellow-200 rounded p-3">
                  <p className="text-sm text-yellow-800">{rec.message}</p>
                  <p className="text-xs text-yellow-600 mt-1">{rec.action}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Calibration Adjustments */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Calibration Adjustments</h2>
        {calibrationLoading ? (
          <div className="text-gray-500">Loading...</div>
        ) : calibration?.error ? (
          <div className="text-red-600">{calibration.error}</div>
        ) : calibration?.adjustments ? (
          <div className="space-y-3">
            {Object.entries(calibration.adjustments).map(([range, data]: [string, any]) => (
              <div key={range} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">Score Range: {range}</p>
                    <p className="text-sm text-gray-500">
                      Expected: {formatPercent(data.expected_rate)} | Actual: {formatPercent(data.actual_rate)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">Adjustment Factor</p>
                    <p className="text-lg font-bold text-gray-900">{data.adjustment_factor.toFixed(3)}x</p>
                    <p className="text-xs text-gray-500">{data.adjustment > 0 ? '+' : ''}{data.adjustment}%</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-500">No calibration data available</div>
        )}
      </div>

      {/* Recommendations */}
      {recommendations && recommendations.recommendations && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Calibration Recommendations</h2>
          <div className="space-y-3">
            {recommendations.recommendations.map((rec: any, idx: number) => (
              <div
                key={idx}
                className={`border rounded-lg p-4 ${
                  rec.priority === 'high' ? 'border-red-200 bg-red-50' : 'border-yellow-200 bg-yellow-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{rec.score_range}</p>
                    <p className="text-sm text-gray-700 mt-1">{rec.issue}</p>
                    <p className="text-sm font-medium text-gray-900 mt-2">{rec.recommendation}</p>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded ${
                      rec.priority === 'high' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {rec.priority}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

