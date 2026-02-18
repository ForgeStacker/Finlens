import type {
  BackendAccount,
  BackendRegion,
  BackendServiceDetail,
  AWSAccount,
  AWSRegion,
  AWSService,
  ServiceCategory,
  ServiceResource
} from './types';
import { formatServiceName } from '../utils/formatUtils';

type ServiceMap = Record<string, Record<string, string[]>>;
type ResourceCountMap = Record<string, Record<string, Record<string, Record<string, number>>>>;

interface DiscoveryStructure {
  accounts: string[];
  regions: Record<string, string[]>;
  services: ServiceMap;
}

interface DiscoverySnapshot extends DiscoveryStructure {
  resourceCounts: ResourceCountMap;
}

// Service for transforming backend data to frontend models
class DataService {
  // Dynamically discover structure and get real resource counts
  private async simulateFileSystemRead(): Promise<DiscoverySnapshot> {
    try {
      console.log('🔍 Attempting to discover file system structure via API...');
      const response = await fetch(`http://localhost:8083/api/discovery`);
      if (response.ok) {
        const data = await response.json() as DiscoveryStructure;
        console.log('✅ Discovery API returned:', data);
        
        // Get resource counts for all services
        const resourceCounts = await this.fetchAllResourceCounts(data);
        
        return {
          ...data,
          resourceCounts
        };
      } else {
        console.warn('⚠️ Discovery API response not ok:', response.status);
      }
    } catch (error) {
      console.warn('❌ Discovery API failed, using manual structure discovery:', error);
    }

    // Fallback: Manual discovery
    console.log('🔧 Falling back to manual structure discovery...');
    const accounts: string[] = [];
    const availableRegions = ['ap-south-1'];
    
    const services = await this.readActualServices(accounts);
    const resourceCounts = await this.fetchAllResourceCountsFallback(accounts, services);

    const regions: Record<string, string[]> = {};
    for (const account of accounts) {
      regions[account] = availableRegions;
    }
    
    return {
      accounts,
      regions,
      services,
      resourceCounts
    };
  }

  private async readActualServices(accounts: string[]): Promise<ServiceMap> {
    // Fallback service structure - in dynamic mode, this should come from discovery API
    const services: Record<string, Record<string, string[]>> = {};
    
    for (const account of accounts) {
      services[account] = {
        'compute': ['ami', 'ec2', 'eks'],
        'database': ['docdb', 'dynamodb', 'elasticache', 'neptune', 'rds', 'redshift'],
        'general': [],
        'storage': ['ebs', 'ecr', 'efs', 's3', 'snapshot', 'storagegateway'],
        'networking': ['cloudfront', 'elasticip', 'route53', 'vpc', 'vpcpeering'],
        'integration': [],
        'cost_management': [],
        'security': ['acm', 'guardduty', 'iam', 'inspector', 'kms', 'organizations', 'secretsmanager', 'securityhub', 'shield', 'waf'],
        'monitoring': ['cloudwatch'],
        'devops_tools': [],
        'analytics': ['athena', 'emr', 'glue', 'kinesis', 'opensearch', 'quicksight'],
        'migration_transfer': [],
        'management_governance': ['cloudtrail', 'config', 'controltower', 'servicecatalog', 'ssm', 'trustedadvisor'],
        'ai_ml': ['comprehend', 'lex', 'lexv2-models', 'polly', 'rekognition', 'sagemaker', 'textract']
      };
    }
    return services;
  }

  private async fetchAllResourceCounts(discoveryData: DiscoveryStructure): Promise<ResourceCountMap> {
    const resourceCounts: ResourceCountMap = {};
    
    for (const accountName of discoveryData.accounts) {
      resourceCounts[accountName] = {};
      const accountRegions = discoveryData.regions[accountName] || ['ap-south-1'];
      const accountServices = discoveryData.services[accountName] || {};

      for (const regionCode of accountRegions) {
        resourceCounts[accountName][regionCode] = {};

        for (const [categoryKey, serviceNames] of Object.entries(accountServices)) {
          resourceCounts[accountName][regionCode][categoryKey] = {};
          
          for (const serviceName of serviceNames as string[]) {
            // Skip EC2 from general category - it should only appear in compute
            if (categoryKey === 'general' && serviceName === 'ec2') {
              continue;
            }
            
            try {
              const response = await fetch(`http://localhost:8083/api/data/${accountName}/${regionCode}/${serviceName}`);
              
              if (response.ok) {
                const rawData = await response.json() as unknown;
                const serviceData = this.normalizeServiceData(rawData, accountName, regionCode, serviceName);
                const resourceCount = this.extractResourceCount(serviceData, regionCode);
                resourceCounts[accountName][regionCode][categoryKey][serviceName] = resourceCount;
                console.log(`✅ ${accountName}/${regionCode}/${categoryKey}/${serviceName}: ${resourceCount} resources`);
              } else {
                resourceCounts[accountName][regionCode][categoryKey][serviceName] = 0;
                console.log(`⚠️ ${accountName}/${regionCode}/${categoryKey}/${serviceName}: No data (${response.status})`);
              }
            } catch (error) {
              resourceCounts[accountName][regionCode][categoryKey][serviceName] = 0;
              console.log(`❌ ${accountName}/${regionCode}/${categoryKey}/${serviceName}: Error - ${error}`);
            }
          }
        }
      }
    }
    
    return resourceCounts;
  }

  private async fetchAllResourceCountsFallback(accounts: string[], services: ServiceMap): Promise<ResourceCountMap> {
    const resourceCounts: ResourceCountMap = {};
    
    for (const accountName of accounts) {
      resourceCounts[accountName] = {};
      const fallbackRegion = 'ap-south-1';
      resourceCounts[accountName][fallbackRegion] = {};
      const accountServices = services[accountName] || {};
      
      for (const [categoryKey, serviceNames] of Object.entries(accountServices)) {
        resourceCounts[accountName][fallbackRegion][categoryKey] = {};
        
        for (const serviceName of serviceNames) {
          // Skip EC2 from general category - it should only appear in compute
          if (categoryKey === 'general' && serviceName === 'ec2') {
            continue;
          }
          
          try {
            const response = await fetch(`http://localhost:8083/api/data/${accountName}/ap-south-1/${serviceName}`);
            if (response.ok) {
              const rawData = await response.json() as unknown;
              const serviceData = this.normalizeServiceData(rawData, accountName, fallbackRegion, serviceName);
              const resourceCount = this.extractResourceCount(serviceData, fallbackRegion);
              resourceCounts[accountName][fallbackRegion][categoryKey][serviceName] = resourceCount;
            } else {
              resourceCounts[accountName][fallbackRegion][categoryKey][serviceName] = 0;
            }
          } catch (error) {
            resourceCounts[accountName][fallbackRegion][categoryKey][serviceName] = 0;
          }
        }
      }
    }
    
    return resourceCounts;
  }

  async getAccounts(): Promise<AWSAccount[]> {
    const data = await this.simulateFileSystemRead();
    
    return data.accounts.map((accountName, index) => {
      // Calculate real total resources for this account
      const accountRegionCounts = data.resourceCounts?.[accountName] || {};
      const totalResources = Object.values(accountRegionCounts).reduce((accountSum, regionData) => {
        const regionTotal = Object.values(regionData).reduce((regionSum, categoryData) => {
          const categoryTotal = Object.values(categoryData).reduce((categorySum, count) => categorySum + count, 0);
          return regionSum + categoryTotal;
        }, 0);
        return accountSum + regionTotal;
      }, 0);
      
      return {
        id: (index + 1).toString(),
        name: accountName,
        accountId: this.generateAccountId(accountName),
        environment: this.determineEnvironment(accountName),
        status: 'active' as const,
        regions: data.regions[accountName] || [],
        totalServices: Object.values(data.services[accountName] || {}).flat().length,
        totalResources,
        lastScan: new Date().toISOString()
      };
    });
  }

  async getRegions(accountName: string): Promise<AWSRegion[]> {
    const data = await this.simulateFileSystemRead();
    const regionCodes = data.regions[accountName] || [];

    return regionCodes.map(code => {
      const regionInfo = this.getRegionInfo(code);
      const services = data.services[accountName] || {};
      const regionResourceCounts = data.resourceCounts?.[accountName]?.[code] || {};
      const serviceCount = Object.values(services).flat().length;
      
      // Calculate real total resources for this region
      const totalRegionResources = Object.values(regionResourceCounts).reduce((sum, categoryData) => {
        const categoryTotal = Object.values(categoryData).reduce((categorySum, count) => categorySum + count, 0);
        return sum + categoryTotal;
      }, 0);
      
      return {
        code,
        name: regionInfo.name,
        flag: regionInfo.flag,
        category: regionInfo.category,
        serviceCount,
        resourceCount: totalRegionResources,
        active: true,
        services: Object.entries(services).flatMap(([category, serviceNames]) =>
          serviceNames.map(serviceName => {
            const realResourceCount = regionResourceCounts[category]?.[serviceName] || 0;
            return {
              serviceName,
              category,
              resourceCount: realResourceCount,
              scanStatus: 'success' as const,
              lastUpdated: new Date().toISOString()
            };
          })
        )
      };
    });
  }

  async getServiceCategories(accountName: string, regionCode: string): Promise<ServiceCategory[]> {
    console.log('getServiceCategories called with:', { accountName, regionCode });
    
    const data = await this.simulateFileSystemRead();
    console.log('simulateFileSystemRead returned:', data);
    
    const services = data.services[accountName] || {};
    const resourceCounts = data.resourceCounts?.[accountName]?.[regionCode] || {};
    console.log('services for account:', services);
    console.log('resource counts for account/region:', resourceCounts);

    // Define the desired category order
    const categoryOrder = [
      'compute',
      'database', 
      'general',
      'storage',
      'networking',
      'integration',
      'cost_management',
      'security',
      'monitoring',
      'devops_tools',
      'analytics',
      'migration_transfer',
      'management_governance',
      'ai_ml'
    ];

    // Create categories in the specified order, filtering out empty categories and services with no resources
    const categoriesPromises = categoryOrder.map(async categoryName => {
      const serviceNames = services[categoryName] || [];
      if (serviceNames.length === 0) return null;
      
      const categoryResourceCounts = resourceCounts[categoryName] || {};
      
      // Filter out services that have 0 resources
      const servicesWithResources = serviceNames.filter(serviceName => {
        const resourceCount = categoryResourceCounts[serviceName] || 0;
        return resourceCount > 0;
      });
      
      // Skip category if no services have resources
      if (servicesWithResources.length === 0) return null;
      
      const categoryTotalResources = servicesWithResources.reduce((sum, serviceName) => {
        return sum + (categoryResourceCounts[serviceName] || 0);
      }, 0);
      
      // Create services with real data asynchronously
      const servicesPromises = servicesWithResources.map(serviceName => 
        this.createServiceModelWithData(
          serviceName, 
          categoryName, 
          accountName,
          regionCode,
          categoryResourceCounts[serviceName] || 0
        )
      );
      const categoryServices = await Promise.all(servicesPromises);
      
      return {
        key: categoryName,
        name: this.formatCategoryName(categoryName),
        services: categoryServices,
        totalResources: categoryTotalResources
      };
    });
    
    const categoriesResults = await Promise.all(categoriesPromises);
    const categories = categoriesResults.filter(Boolean) as ServiceCategory[];
    
    console.log('returning categories with real resource counts:', categories);
    return categories;
  }

  private generateAccountId(name: string): string {
    // Generate consistent account ID based on name
    const hash = name.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    return Math.abs(hash).toString().padStart(12, '0').slice(0, 12);
  }

  private determineEnvironment(name: string): 'Production' | 'Development' | 'Staging' | 'Testing' {
    if (name.includes('PROD')) return 'Production';
    if (name.includes('DEV')) return 'Development';
    if (name.includes('STG')) return 'Staging';
    return 'Testing';
  }

  private getRegionInfo(code: string): { name: string; flag: string; category: string } {
    const regions: Record<string, { name: string; flag: string; category: string }> = {
      'ap-south-1': { name: 'Asia Pacific (Mumbai)', flag: '🇮🇳', category: 'Asia Pacific' },
      'ap-southeast-1': { name: 'Asia Pacific (Singapore)', flag: '🇸🇬', category: 'Asia Pacific' },
      'ap-northeast-1': { name: 'Asia Pacific (Tokyo)', flag: '🇯🇵', category: 'Asia Pacific' },
      'us-east-1': { name: 'US East (N. Virginia)', flag: '🇺🇸', category: 'US East' },
      'us-east-2': { name: 'US East (Ohio)', flag: '🇺🇸', category: 'US East' },
      'us-west-2': { name: 'US West (Oregon)', flag: '🇺🇸', category: 'US West' },
      'eu-west-1': { name: 'Europe (Ireland)', flag: '🇮🇪', category: 'Europe' },
      'eu-central-1': { name: 'Europe (Frankfurt)', flag: '🇩🇪', category: 'Europe' }
    };
    return regions[code] || { name: code, flag: '🌍', category: 'Other' };
  }

  private formatCategoryName(category: string): string {
    const categoryNameMap: Record<string, string> = {
      'compute': 'Compute',
      'database': 'Database', 
      'general': 'General',
      'storage': 'Storage',
      'networking': 'Networking',
      'integration': 'Integration',
      'cost_management': 'Cost Management',
      'security': 'Security',
      'monitoring': 'Monitoring',
      'devops_tools': 'DevOps Tools',
      'analytics': 'Analytics',
      'migration_transfer': 'Migration Transfer',
      'management_governance': 'Management Governance',
      'ai_ml': 'AI-ML'
    };
    
    return categoryNameMap[category] || category.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  }

  private normalizeScanStatus(status: unknown): 'success' | 'failed' | 'partial' {
    if (typeof status !== 'string') {
      return 'failed';
    }
    const normalized = status.toLowerCase();
    if (normalized === 'success' || normalized === 'failed' || normalized === 'partial') {
      return normalized;
    }
    return 'failed';
  }

  private isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
  }

  private asNumberRecord(value: unknown): Record<string, number> | undefined {
    if (!this.isRecord(value)) {
      return undefined;
    }
    const result: Record<string, number> = {};
    let hasNumericEntries = false;
    for (const [key, val] of Object.entries(value)) {
      if (typeof val === 'number') {
        result[key] = val;
        hasNumericEntries = true;
      }
    }
    return hasNumericEntries ? result : undefined;
  }

  private getNumericValue(value: unknown): number {
    if (typeof value === 'number') {
      return value;
    }
    if (typeof value === 'string') {
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : 0;
    }
    return 0;
  }

  private filterResourcesByRegion(resources: ServiceResource[], regionCode?: string): ServiceResource[] {
    if (!regionCode || resources.length === 0) {
      return resources;
    }

    const filtered = resources.filter(resource => {
      const region = resource['region'] ?? resource['Region'] ?? resource['aws_region'];
      return typeof region === 'string' && region === regionCode;
    });

    return filtered.length > 0 ? filtered : resources;
  }

  private extractResourceArray(serviceData: unknown, regionCode?: string): ServiceResource[] {
    if (!this.isRecord(serviceData)) {
      return [];
    }

    if (Array.isArray(serviceData.resources)) {
      return this.filterResourcesByRegion(serviceData.resources as ServiceResource[], regionCode);
    }

    const preferredArrayKeys = [
      'buckets', 'instances', 'clusters', 'functions', 'volumes',
      'snapshots', 'repositories', 'vpcs', 'subnets', 'security_groups',
      'db_instances', 'tables', 'distributions', 'load_balancers'
    ];

    for (const key of preferredArrayKeys) {
      const value = serviceData[key];
      if (Array.isArray(value)) {
        return this.filterResourcesByRegion(value as ServiceResource[], regionCode);
      }
    }

    for (const [key, value] of Object.entries(serviceData)) {
      if (key === 'tags' || key === 'metadata' || key === 'summary') {
        continue;
      }
      if (Array.isArray(value)) {
        return this.filterResourcesByRegion(value as ServiceResource[], regionCode);
      }
    }

    return [];
  }

  private extractResourceCount(serviceData: unknown, regionCode?: string): number {
    if (!this.isRecord(serviceData)) {
      return 0;
    }

    const summary = this.isRecord(serviceData.summary) ? serviceData.summary : undefined;
    const summaryCount = this.getNumericValue(summary?.resource_count ?? summary?.total_resources);
    if (summaryCount > 0) {
      return summaryCount;
    }

    return this.extractResourceArray(serviceData, regionCode).length;
  }

  private normalizeServiceData(
    rawData: unknown,
    accountName: string,
    regionCode: string,
    serviceName: string
  ): BackendServiceDetail {
    if (this.isRecord(rawData) && Array.isArray(rawData.resources) && this.isRecord(rawData.summary)) {
      return rawData as unknown as BackendServiceDetail;
    }

    const inferredResources = this.extractResourceArray(rawData, regionCode);
    const inferredCount = this.extractResourceCount(rawData, regionCode);

    return {
      schema_version: this.isRecord(rawData) && typeof rawData.schema_version === 'string' ? rawData.schema_version : '1.0.0',
      generated_at: this.isRecord(rawData) && typeof rawData.generated_at === 'string' ? rawData.generated_at : new Date().toISOString(),
      service: {
        service_name: serviceName,
        region: regionCode,
        profile: accountName
      },
      summary: {
        resource_count: inferredCount,
        scan_status: 'success'
      },
      resources: inferredResources
    };
  }

  private calculateServiceHealth(serviceName: string, serviceData: BackendServiceDetail | null): { healthPercent: number, scanStatus: 'success' | 'failed' | 'partial' } {
    if (!serviceData || !serviceData.summary) {
      return { healthPercent: 0, scanStatus: 'failed' };
    }

    const summary = serviceData.summary;
    const resourceCount = typeof summary.resource_count === 'number' ? summary.resource_count : 0;
    const normalizedStatus = this.normalizeScanStatus(summary.scan_status);

    if (normalizedStatus === 'failed' || resourceCount === 0) {
      return {
        healthPercent: resourceCount === 0 ? 100 : 0,
        scanStatus: resourceCount === 0 ? 'success' : 'failed'
      };
    }

    let healthScore = 100;
    let scanStatus: 'success' | 'failed' | 'partial' = normalizedStatus === 'partial' ? 'partial' : 'success';

    switch (serviceName) {
      case 'ec2': {
        const stateDistribution = this.asNumberRecord(summary['state_distribution']);
        if (stateDistribution) {
          const running = stateDistribution.running ?? 0;
          const stopped = stateDistribution.stopped ?? 0;
          const terminated = stateDistribution.terminated ?? 0;
          healthScore = resourceCount > 0 ? Math.round((running / resourceCount) * 100) : 0;
          if (stopped > 0) {
            scanStatus = 'partial';
          }
          if (terminated > 0) {
            healthScore = Math.max(0, healthScore - 20);
          }
        }
        break;
      }

      case 'rds': {
        const statusDistribution = this.asNumberRecord(summary['status_distribution']);
        if (statusDistribution) {
          const available = statusDistribution.available ?? 0;
          healthScore = resourceCount > 0 ? Math.round((available / resourceCount) * 100) : 0;
          if (available < resourceCount) {
            scanStatus = 'partial';
          }
        }
        break;
      }

      case 'cloudtrail': {
        const loggingEnabled = this.getNumericValue(summary['logging_enabled']);
        const totalTrails = this.getNumericValue(summary['total_trails']);
        if (totalTrails === 0) {
          healthScore = 0;
          scanStatus = 'failed';
        } else {
          healthScore = Math.round((loggingEnabled / totalTrails) * 100);
          if (loggingEnabled < totalTrails) {
            scanStatus = 'partial';
          }
        }
        break;
      }

      case 'vpc': {
        const isDefault = summary['is_default'];
        if (typeof isDefault === 'boolean') {
          healthScore = isDefault ? 70 : 100;
          if (isDefault) {
            scanStatus = 'partial';
          }
        }
        break;
      }

      case 's3': {
        const encryptionStatus = this.isRecord(summary['encryption_status']) ? summary['encryption_status'] : undefined;
        if (encryptionStatus) {
          const encrypted = this.getNumericValue(encryptionStatus['encrypted']);
          healthScore = resourceCount > 0 ? Math.round((encrypted / resourceCount) * 100) : 0;
          if (encrypted < resourceCount) {
            scanStatus = 'partial';
          }
        }
        break;
      }

      default:
        if (normalizedStatus === 'success') {
          healthScore = resourceCount > 0 ? 95 : 100;
        } else {
          healthScore = 75;
          scanStatus = 'partial';
        }
    }

    return { healthPercent: Math.max(0, Math.min(100, healthScore)), scanStatus };
  }

  private async createServiceModelWithData(serviceName: string, category: string, accountName: string, regionCode: string, resourceCount: number = 0): Promise<AWSService> {
    // Try to get real service data for health calculation
    let serviceData = null;
    try {
      const response = await fetch(`http://localhost:8083/api/data/${accountName}/${regionCode}/${category}/${serviceName}`);
      if (response.ok) {
        const rawData = await response.json() as unknown;
        serviceData = this.normalizeServiceData(rawData, accountName, regionCode, serviceName);
      }
    } catch (error) {
      console.warn(`Failed to fetch service data for ${serviceName}:`, error);
    }

    const { healthPercent, scanStatus } = this.calculateServiceHealth(serviceName, serviceData);
    
    // Calculate realistic active count based on service type and health
    let activeCount = 0;
    if (resourceCount > 0) {
      const healthRatio = healthPercent / 100;
      activeCount = Math.floor(resourceCount * (0.5 + healthRatio * 0.5));
    }
    
    return {
      id: `${category}/${serviceName}`,
      serviceName,
      categoryKey: category,
      name: formatServiceName(serviceName),
      description: `${this.formatCategoryName(category)} service`,
      category: this.formatCategoryName(category),
      resourceCount,
      activeCount,
      healthPercent,
      status: healthPercent >= 90 ? 'healthy' : healthPercent >= 70 ? 'warning' : 'critical',
      icon: this.getServiceIcon(serviceName),
      scanStatus,
      lastUpdated: new Date().toISOString()
    };
  }



  private getServiceIcon(service: string): string {
    const icons: Record<string, string> = {
      ec2: '🖥️',
      eks: '☸️',
      ami: '📀',
      ebs: '💿',
      snapshot: '📸',
      vpc: '🌐',
      dynamodb: '🗃️',
      elasticache: '⚡',
      redshift: '🔍',
      neptune: '🌊',
      docdb: '📋'
    };
    return icons[service] || '⚙️';
  }

  // Add method to get actual service details from JSON files
  async getServiceDetails(accountName: string, regionCode: string, serviceName: string): Promise<BackendServiceDetail> {
    console.log(`Attempting to load service details for: ${accountName}/${regionCode}/${serviceName}`);
    
    try {
      // Call the real API that reads from your actual JSON files  
      const apiUrl = `http://localhost:8083/api/data/${accountName}/${regionCode}/${serviceName}`;
      console.log(`Making API call to: ${apiUrl}`);
      
      const response = await fetch(apiUrl);
      
      if (response.ok) {
        const rawData = await response.json() as unknown;
        const data = this.normalizeServiceData(rawData, accountName, regionCode, serviceName);
        console.log(`✅ API successfully returned data for ${serviceName}:`, {
          resourceCount: data.resources?.length || 0,
          summary: data.summary
        });
        return data;
      } else {
        console.warn(`❌ API response not ok for ${serviceName}:`, {
          status: response.status,
          statusText: response.statusText,
          url: apiUrl
        });
      }
      
    } catch (error) {
      console.error(`❌ API call failed for ${serviceName}:`, {
        error: error.message,
        accountName,
        regionCode,
        serviceName
      });
    }
    
    // If we reach here, API failed - use fallback
    console.warn(`⚠️  Falling back to simulated data for ${serviceName}`);
    return await this.loadSimulatedServiceData(accountName, serviceName);
  }

  private async loadSimulatedServiceData(accountName: string, serviceName: string): Promise<BackendServiceDetail> {
    // Dynamic fallback that creates realistic structure for any service
    // This should only be used when API is completely unavailable
    
    console.log(`Loading fallback data for ${serviceName} in ${accountName}`);
    
    const baseStructure: BackendServiceDetail = {
      schema_version: "1.0.0",
      generated_at: new Date().toISOString(),
      service: {
        service_name: serviceName,
        region: "ap-south-1",
        profile: accountName
      },
      summary: {
        resource_count: 0,
        scan_status: "fallback_data"
      },
      resources: []
    };
    
    // Return empty but properly structured data when API is not available
    // This ensures the UI doesn't break but indicates no real data is available
    return baseStructure;
  }

  // Helper method to generate dynamic column definitions based on actual data
  generateColumnsFromData(resources: ServiceResource[], _serviceName: string): Array<{key: string, label: string, visible: boolean, sortable: boolean}> {
    if (!resources || resources.length === 0) {
      return [
        { key: "resource_name", label: "Name", visible: true, sortable: true },
        { key: "resource_type", label: "Type", visible: true, sortable: true },
        { key: "status", label: "Status", visible: true, sortable: true },
        { key: "region", label: "Region", visible: true, sortable: true },
        { key: "launch_time", label: "Created", visible: true, sortable: true },
        { key: "instance_type", label: "Instance Type", visible: true, sortable: true },
        { key: "vpc_id", label: "VPC", visible: true, sortable: true }
      ];
    }

    const firstResource = resources[0];
    const columns: Array<{ key: string; label: string; visible: boolean; sortable: boolean }> = [];
    
    // Priority columns to show by default (aim for 7-9 columns)
    const priorityColumns = [
      { key: "resource_name", label: "Name" },
      { key: "resource_id", label: "Resource ID" },
      { key: "resource_type", label: "Type" },
      { key: "status", label: "Status" },
      { key: "state", label: "State" },
      { key: "region", label: "Region" },
      { key: "instance_type", label: "Instance Type" },
      { key: "instance_id", label: "Instance ID" },
      { key: "launch_time", label: "Launch Time" },
      { key: "created_time", label: "Created" },
      { key: "vpc_id", label: "VPC ID" },
      { key: "subnet_id", label: "Subnet ID" },
      { key: "platform", label: "Platform" },
      { key: "db_instance_class", label: "DB Class" },
      { key: "engine", label: "Engine" },
      { key: "engine_version", label: "Engine Version" },
      { key: "endpoint", label: "Endpoint" },
      { key: "availability_zone", label: "AZ" },
      { key: "security_groups", label: "Security Groups" }
    ];
    
    let visibleCount = 0;
    const maxVisible = 9;
    
    // Add priority columns that exist in the data
    for (const priorityCol of priorityColumns) {
      if (firstResource[priorityCol.key] !== undefined && firstResource[priorityCol.key] !== null && visibleCount < maxVisible) {
        columns.push({ 
          key: priorityCol.key, 
          label: priorityCol.label, 
          visible: true, 
          sortable: true 
        });
        visibleCount++;
      }
    }
    
    // Add remaining fields as visible until we reach 7-9 columns, then hidden
    for (const [key, value] of Object.entries(firstResource)) {
      if (key === 'tags') {
        continue;
      }
      if (!columns.find(c => c.key === key) && value !== null && value !== undefined) {
        const label = key.split('_').map(word => 
          word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
        
        const visible = visibleCount < Math.max(7, maxVisible);
        columns.push({ key, label, visible, sortable: true });
        if (visible) visibleCount++;
      }
    }
    
    return columns;
  }

  async getLastScanTimestamp(accountName: string, regionCode: string): Promise<string | null> {
    try {
      const data = await this.simulateFileSystemRead();
      const services = data.services[accountName] || {};
      let latestTimestamp: string | null = null;
      let latestEpoch = 0;

      // Check all service categories and their services for scan timestamps
      for (const [categoryKey, serviceNames] of Object.entries(services)) {
        for (const serviceName of serviceNames as string[]) {
          try {
            const response = await fetch(`http://localhost:8083/api/data/${accountName}/${regionCode}/${serviceName}`);
            if (response.ok) {
              const serviceData = await response.json() as BackendServiceDetail;
              const serviceDataRecord = serviceData as unknown as Record<string, unknown>;
              const summaryRecord = this.isRecord(serviceData.summary)
                ? (serviceData.summary as Record<string, unknown>)
                : {};
              const metadataRecord = this.isRecord(serviceDataRecord['metadata'])
                ? (serviceDataRecord['metadata'] as Record<string, unknown>)
                : {};
              const serviceRecord = this.isRecord(serviceData.service)
                ? (serviceData.service as Record<string, unknown>)
                : {};

              const timestamp =
                serviceData.generated_at ||
                (typeof serviceDataRecord['scan_timestamp'] === 'string' ? serviceDataRecord['scan_timestamp'] : undefined) ||
                (typeof summaryRecord['generated_at'] === 'string' ? summaryRecord['generated_at'] : undefined) ||
                (typeof summaryRecord['scan_timestamp'] === 'string' ? summaryRecord['scan_timestamp'] : undefined) ||
                (typeof metadataRecord['scan_timestamp'] === 'string' ? metadataRecord['scan_timestamp'] : undefined) ||
                (typeof serviceRecord['scan_timestamp'] === 'string' ? serviceRecord['scan_timestamp'] : undefined) ||
                (typeof serviceRecord['generated_at'] === 'string' ? serviceRecord['generated_at'] : undefined);
              
              if (timestamp) {
                const epoch = new Date(timestamp).getTime();
                if (!Number.isNaN(epoch) && epoch > latestEpoch) {
                  latestEpoch = epoch;
                  latestTimestamp = timestamp;
                }
              }
            }
          } catch (error) {
            // Continue checking other services if one fails
            continue;
          }
        }
      }

      return latestTimestamp;
    } catch (error) {
      console.warn('Failed to fetch scan timestamps:', error);
      return null;
    }
  }
}

export const dataService = new DataService();
