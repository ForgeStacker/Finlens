// API service for backend data integration
const API_BASE = '/api';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async fetchJson<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`);
    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  // Account discovery
  async getAccounts(): Promise<string[]> {
    return this.fetchJson<string[]>('/accounts');
  }

  // Region discovery for account
  async getRegions(accountId: string): Promise<string[]> {
    return this.fetchJson<string[]>(`/accounts/${accountId}/regions`);
  }

  // Service categories for account/region
  async getServiceCategories(accountId: string, region: string): Promise<string[]> {
    return this.fetchJson<string[]>(`/accounts/${accountId}/regions/${region}/categories`);
  }

  // Services in category
  async getServices(accountId: string, region: string, category: string): Promise<string[]> {
    return this.fetchJson<string[]>(`/accounts/${accountId}/regions/${region}/categories/${category}/services`);
  }

  // Service detail data
  async getServiceData<T>(accountId: string, region: string, category: string, service: string): Promise<T> {
    return this.fetchJson<T>(`/accounts/${accountId}/regions/${region}/categories/${category}/services/${service}`);
  }

  // Summary endpoints
  async getAccountSummary(accountId: string): Promise<{
    totalRegions: number;
    totalServices: number;
    totalResources: number;
    lastScan?: string;
  }> {
    return this.fetchJson(`/accounts/${accountId}/summary`);
  }

  async getRegionSummary(accountId: string, region: string): Promise<{
    totalCategories: number;
    totalServices: number;
    totalResources: number;
    lastScan?: string;
  }> {
    return this.fetchJson(`/accounts/${accountId}/regions/${region}/summary`);
  }
}

export const apiService = new ApiService();