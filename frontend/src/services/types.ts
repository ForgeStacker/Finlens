// Real data types matching backend structure
export interface BackendAccount {
  profile: string;
  regions: string[];
  totalServices: number;
  totalResources: number;
  lastScan?: string;
}

export interface BackendRegion {
  code: string;
  name: string;
  services: BackendServiceSummary[];
  totalResources: number;
  lastScan?: string;
}

export interface BackendServiceSummary {
  serviceName: string;
  category: string;
  resourceCount: number;
  scanStatus: 'success' | 'failed' | 'partial';
  lastUpdated: string;
}

export type ServiceResource = Record<string, unknown>;

export type ServiceSummary = {
  resource_count: number;
  scan_status: string;
} & Record<string, unknown>;

export type ServiceMetadata = {
  service_name: string;
  region: string;
  profile: string;
} & Record<string, unknown>;

export interface BackendServiceDetail {
  schema_version: string;
  generated_at: string;
  service: ServiceMetadata;
  summary: ServiceSummary;
  resources: ServiceResource[];
}
// Frontend types (enhanced from existing)
export interface AWSAccount {
  id: string;
  name: string;
  accountId: string;
  environment: "Production" | "Development" | "Staging" | "Testing";
  status: "active" | "inactive";
  regions?: string[];
  totalServices?: number;
  totalResources?: number;
  lastScan?: string;
}

export interface AWSRegion {
  code: string;
  name: string;
  flag: string;
  category: string;
  serviceCount: number;
  resourceCount: number;
  active: boolean;
  services?: BackendServiceSummary[];
}

export interface AWSService {
  id: string;
  serviceName: string;
  categoryKey: string;
  name: string;
  description: string;
  category: string;
  resourceCount: number;
  activeCount: number;
  healthPercent: number;
  status: "healthy" | "warning" | "critical";
  costEstimate?: number;
  costTrend?: number;
  icon: string;
  scanStatus: 'success' | 'failed' | 'partial';
  lastUpdated: string;
}

export interface ServiceCategory {
  key: string;
  name: string;
  services: AWSService[];
  totalResources: number;
}
