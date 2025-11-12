/**
 * Type-safe API client for Local Lift backend.
 * 
 * This is the single source of truth for all API interactions.
 * All endpoints from Phases 1-5 are integrated here.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Debug logging
if (typeof window !== 'undefined') {
  console.log('API Base URL:', API_BASE_URL);
}

// Create axios instance with defaults
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth tokens (if needed)
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    if (typeof window !== 'undefined') {
      console.log('API Response:', response.config.url, response.status);
    }
    return response;
  },
  (error: AxiosError) => {
    // Centralized error handling
    if (error.response) {
      // Server responded with error
      const status = error.response.status;
      const data = error.response.data as { detail?: string; error?: string; message?: string };
      
      console.error(`API Error [${status}]:`, data.detail || data.error || data.message || 'Unknown error');
    } else if (error.request) {
      // Request made but no response
      console.error('API Error: No response from server', error.request);
    } else {
      // Error setting up request
      console.error('API Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Type definitions for API responses
export interface ApiResponse<T> {
  data: T;
  total?: number;
  limit?: number;
  offset?: number;
}

export interface Lead {
  id: number;
  prop_id: number;
  trade: string;
  intent_score: number;
  quality_score: number | null;
  status: string;
  zip_code: string | null;
  market_value: number | null;
  signal_count: number | null;
  violation_count: number | null;
  request_count: number | null;
  generated_at: string;
  assigned_at: string | null;
  delivered_at: string | null;
  converted_at: string | null;
  contractor_id: number | null;
}

export interface Contractor {
  id: number;
  company_name: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  trades: string;
  subscription_tier: string;
  status: string;
  created_at: string;
}

export interface DashboardStats {
  leads_by_status: Record<string, number>;
  leads_by_trade: Record<string, number>;
  recent_leads_7d: number;
  conversion_rate: number;
  avg_intent_score: number;
  total_leads: number;
}

export interface ScoreResult {
  prop_id: number;
  score: number;
  components: Record<string, number>;
  address: string | null;
  zip_code: string | null;
  market_value: number | null;
}

// API Client Class
export class LocalLiftAPI {
  // ===== SCORING API (Phase 2) =====
  async getPropertyScore(propId: number, trade?: string): Promise<ScoreResult> {
    const response = await apiClient.get<ScoreResult>(`/scoring/property/${propId}`, {
      params: { trade },
    });
    return response.data;
  }

  async batchScoreProperties(propIds: number[], trade?: string, limit?: number): Promise<ScoreResult[]> {
    const response = await apiClient.post<ApiResponse<ScoreResult[]>>('/scoring/batch', propIds, {
      params: { trade, limit },
    });
    return response.data.results || [];
  }

  async getHighIntentProperties(
    minScore: number = 0.6,
    trade?: string,
    limit: number = 100
  ): Promise<Lead[]> {
    const response = await apiClient.get<ApiResponse<Lead[]>>('/scoring/high-intent', {
      params: { min_score: minScore, trade, limit },
    });
    return response.data.properties || [];
  }

  // ===== LEADS API (Phase 3) =====
  async listLeads(params: {
    trade?: string;
    status?: string;
    contractor_id?: number;
    min_score?: number;
    limit?: number;
    offset?: number;
  }): Promise<{ leads: Lead[]; total: number; limit: number; offset: number }> {
    const response = await apiClient.get<{ leads: Lead[]; total: number; limit: number; offset: number }>('/leads/', { params });
    return response.data;
  }

  async getLead(leadId: number): Promise<Lead> {
    const response = await apiClient.get<Lead>(`/leads/${leadId}`);
    return response.data;
  }

  async generateLeads(
    trade: string,
    minScore: number = 0.6,
    maxLeads?: number,
    zipCodes?: string[]
  ): Promise<{ generated: number; trade: string; leads: Lead[] }> {
    const response = await apiClient.post<{ generated: number; trade: string; leads: Lead[] }>(
      '/leads/generate',
      null,
      {
        params: { trade, min_score: minScore, max_leads: maxLeads, zip_codes: zipCodes },
      }
    );
    return response.data;
  }

  async assignLead(leadId: number, contractorId: number, assignedBy: string = 'system'): Promise<Lead> {
    const response = await apiClient.post<Lead>(`/leads/${leadId}/assign`, null, {
      params: { contractor_id: contractorId, assigned_by: assignedBy },
    });
    return response.data;
  }

  async deliverLead(leadId: number, deliveryMethod: string = 'api'): Promise<Lead> {
    const response = await apiClient.post<Lead>(`/leads/${leadId}/deliver`, null, {
      params: { delivery_method: deliveryMethod },
    });
    return response.data;
  }

  async convertLead(leadId: number, conversionValue?: number): Promise<Lead> {
    const response = await apiClient.post<Lead>(`/leads/${leadId}/convert`, null, {
      params: { conversion_value: conversionValue },
    });
    return response.data;
  }

  // ===== CONTRACTORS API (Phase 3) =====
  async listContractors(params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<ApiResponse<Contractor[]>> {
    const response = await apiClient.get<ApiResponse<Contractor[]>>('/contractors', { params });
    return response.data;
  }

  async getContractor(contractorId: number): Promise<Contractor> {
    const response = await apiClient.get<Contractor>(`/contractors/${contractorId}`);
    return response.data;
  }

  async createContractor(data: {
    company_name: string;
    contact_name?: string;
    email?: string;
    phone?: string;
    trades: string;
    subscription_tier?: string;
  }): Promise<Contractor> {
    const response = await apiClient.post<Contractor>('/contractors', null, { params: data });
    return response.data;
  }

  async assignTerritory(
    contractorId: number,
    zipCode: string,
    trade: string,
    isExclusive: boolean = true
  ): Promise<{ id: number; contractor_id: number; zip_code: string; trade: string }> {
    const response = await apiClient.post(
      `/contractors/${contractorId}/territories`,
      null,
      {
        params: { zip_code: zipCode, trade, is_exclusive: isExclusive },
      }
    );
    return response.data;
  }

  async getContractorTerritories(
    contractorId: number,
    trade?: string,
    activeOnly: boolean = true
  ): Promise<{ contractor_id: number; territories: any[]; total: number }> {
    const response = await apiClient.get(`/contractors/${contractorId}/territories`, {
      params: { trade, active_only: activeOnly },
    });
    return response.data;
  }

  // ===== DASHBOARD API (Phase 3) =====
  async getDashboardStats(contractorId?: number): Promise<DashboardStats> {
    const response = await apiClient.get<DashboardStats>('/dashboard/stats', {
      params: { contractor_id: contractorId },
    });
    return response.data;
  }

  async getVerifiedLeads(params: {
    contractor_id?: number;
    min_verification_score?: number;
    limit?: number;
  }): Promise<{ leads: Lead[]; total: number }> {
    const response = await apiClient.get('/dashboard/leads/verified', { params });
    return response.data;
  }

  async getContractorPerformance(
    contractorId: number,
    days: number = 30
  ): Promise<{
    contractor_id: number;
    company_name: string;
    leads_assigned: number;
    leads_delivered: number;
    leads_converted: number;
    conversion_rate: number;
    total_revenue: number;
  }> {
    const response = await apiClient.get(`/dashboard/contractors/${contractorId}/performance`, {
      params: { days },
    });
    return response.data;
  }

  // ===== DELIVERY API (Phase 4) =====
  async deliverLead(
    leadId: number,
    deliveryMethods?: string[],
    webhookUrl?: string
  ): Promise<{ lead_id: number; contractor_id: number; results: any; success: boolean }> {
    const response = await apiClient.post(`/delivery/lead/${leadId}`, null, {
      params: { delivery_methods: deliveryMethods, webhook_url: webhookUrl },
    });
    return response.data;
  }

  async deliverAssignedLeads(contractorId?: number, limit?: number): Promise<{
    total: number;
    delivered: number;
    failed: number;
  }> {
    const response = await apiClient.post('/delivery/assigned', null, {
      params: { contractor_id: contractorId, limit },
    });
    return response.data;
  }

  async getLeadEngagement(leadId: number): Promise<{
    lead_id: number;
    engagement_counts: Record<string, number>;
    delivery_stats: any;
  }> {
    const response = await apiClient.get(`/delivery/engagement/${leadId}`);
    return response.data;
  }

  // ===== FEEDBACK API (Phase 5) =====
  async submitFeedback(data: {
    lead_id: number;
    contractor_id: number;
    outcome: string;
    converted?: boolean;
    conversion_value?: number;
    lead_quality_rating?: number;
    accuracy_rating?: number;
    contact_quality_rating?: number;
    feedback_text?: string;
    notes?: string;
  }): Promise<{ id: number; lead_id: number; outcome: string }> {
    const response = await apiClient.post(`/feedback/lead/${data.lead_id}`, null, {
      params: data,
    });
    return response.data;
  }

  async getFeedbackStats(params: {
    contractor_id?: number;
    trade?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<{
    total_feedback: number;
    conversion_rate: number;
    outcome_distribution: Record<string, number>;
    avg_ratings: Record<string, number>;
  }> {
    const response = await apiClient.get('/feedback/stats', { params });
    return response.data;
  }

  async getScoreAccuracy(trade?: string, minFeedbackCount: number = 10): Promise<any> {
    const response = await apiClient.get('/feedback/analytics/score-accuracy', {
      params: { trade, min_feedback_count: minFeedbackCount },
    });
    return response.data;
  }

  async getFeatureImportance(trade?: string): Promise<any> {
    const response = await apiClient.get('/feedback/analytics/feature-importance', {
      params: { trade },
    });
    return response.data;
  }

  async getModelPerformance(trade?: string): Promise<any> {
    const response = await apiClient.get('/feedback/analytics/performance', {
      params: { trade },
    });
    return response.data;
  }

  // ===== CALIBRATION API (Phase 5) =====
  async getCalibrationAdjustments(trade?: string): Promise<any> {
    const response = await apiClient.get('/calibration/adjustments', {
      params: { trade },
    });
    return response.data;
  }

  async getCalibrationRecommendations(trade?: string): Promise<any> {
    const response = await apiClient.get('/calibration/recommendations', {
      params: { trade },
    });
    return response.data;
  }

  async checkModelPerformance(modelVersion: string = 'v1.0', minFeedbackCount: number = 50): Promise<any> {
    const response = await apiClient.get('/calibration/model/performance', {
      params: { model_version: modelVersion, min_feedback_count: minFeedbackCount },
    });
    return response.data;
  }

  async runRefinementCheck(): Promise<any> {
    const response = await apiClient.post('/calibration/model/refinement-check');
    return response.data;
  }
}

// Export singleton instance
export const api = new LocalLiftAPI();

// Export types
export type { Lead, Contractor, DashboardStats, ScoreResult };

