/**
 * API Client for backend communication
 * 
 * In development: Uses Vite proxy (/api -> http://localhost:8000)
 * In production: Uses nginx proxy (/api -> http://backend:8000)
 */

const API_BASE_URL = '/api/v1';

// Types based on backend API
export interface FieldValueResponse {
  id: number;
  field_key: string;
  display_name: string;
  placeholder: string;
  current_value: string;
  extracted_value: string | null;
  manual_value: string | null;
  field_value_id: number;
  description?: string;
}

export interface UpdateFieldRequest {
  value: string;  // backend expects { value: string }
}

export interface RegeneratePreviewResponse {
  success: boolean;
  message: string;
  preview_path: string;
}

export interface FirmResponse {
  id: number;
  name: string;
  code: string;
}

export interface CaseTypeResponse {
  id: number;
  name: string;
  code: string;
  description: string | null;
}

export interface SessionListItem {
  uuid: string;
  status: string;
  created_at: string;
  template_name: string | null;
}

export interface ExtractResponse {
  success: boolean;
  message: string;
  extracted_count?: number;
  updated_count?: number;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`,
        }));
        const detail = errorData.detail;
        const message =
          typeof detail === 'string'
            ? detail
            : Array.isArray(detail) && detail.length > 0
              ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ')
              : `Request failed: ${response.statusText}`;
        throw new Error(message);
      }

      // Handle file downloads (preview DOCX)
      if (response.headers.get('content-type')?.includes('application/vnd.openxmlformats')) {
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = response.headers.get('content-disposition')?.split('filename=')[1] || 'preview.docx';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
        return {} as T; // Return empty object for file downloads
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Config endpoints (firms, case types)
  async getFirms(): Promise<FirmResponse[]> {
    return this.request<FirmResponse[]>('/firms');
  }

  async getCaseTypes(): Promise<CaseTypeResponse[]> {
    return this.request<CaseTypeResponse[]>('/case-types');
  }

  // Session endpoints
  async getSessions(limit = 50): Promise<SessionListItem[]> {
    return this.request<SessionListItem[]>(`/sessions?limit=${limit}`);
  }

  async createSession(data: {
    law_firm_code: string;
    case_type_code: string;
  }): Promise<{ uuid: string }> {
    return this.request<{ uuid: string }>('/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /** Run LLM extraction on this session's uploaded PDF(s). Updates field values. */
  async runExtraction(sessionUuid: string): Promise<ExtractResponse> {
    return this.request<ExtractResponse>(`/sessions/${sessionUuid}/extract`, {
      method: 'POST',
    });
  }

  async uploadDocument(
    sessionUuid: string,
    file: File
  ): Promise<{ document_id: number }> {
    const formData = new FormData();
    formData.append('file', file);
    const url = `${this.baseUrl}/sessions/${sessionUuid}/documents`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      // Do not set Content-Type; browser sets multipart boundary
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
    }
    return response.json();
  }

  // Preview endpoints
  /** Fetch preview DOCX as blob (for in-app display, e.g. convert to HTML with mammoth). */
  async getPreviewBlob(sessionUuid: string): Promise<Blob> {
    const url = `${this.baseUrl}/sessions/${sessionUuid}/preview`;
    const response = await fetch(url);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }));
      throw new Error(errorData.detail || `Failed to get preview: ${response.statusText}`);
    }
    return response.blob();
  }

  async getPreview(sessionUuid: string): Promise<void> {
    const url = `${this.baseUrl}/sessions/${sessionUuid}/preview`;
    const response = await fetch(url);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }));
      throw new Error(errorData.detail || `Failed to get preview: ${response.statusText}`);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `session_${sessionUuid}_preview.docx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  async regeneratePreview(sessionUuid: string): Promise<RegeneratePreviewResponse> {
    return this.request<RegeneratePreviewResponse>(
      `/sessions/${sessionUuid}/preview/regenerate`,
      {
        method: 'POST',
      }
    );
  }

  // Field endpoints
  async getSessionFields(sessionUuid: string): Promise<FieldValueResponse[]> {
    return this.request<FieldValueResponse[]>(
      `/sessions/${sessionUuid}/fields`
    );
  }

  async updateField(
    sessionUuid: string,
    fieldValueId: number,
    value: string
  ): Promise<FieldValueResponse> {
    return this.request<FieldValueResponse>(
      `/sessions/${sessionUuid}/fields/${fieldValueId}`,
      {
        method: 'PATCH',
        body: JSON.stringify({ value }),
      }
    );
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch('/health');
    return response.json();
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for testing
export default ApiClient;
