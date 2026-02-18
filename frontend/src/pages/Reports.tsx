import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3, PieChart, TrendingUp, Shield, Server, Database, 
  CloudLightning, Activity, Users, MapPin, Calendar, Download,
  RefreshCw, Filter, Search, ChevronDown, AlertTriangle, CheckCircle,
  XCircle, Clock, Zap
} from 'lucide-react';
import { Header } from '@/components/Header';import { CategoryIcon } from "@/components/CategoryIcon";import { useAppStore } from '@/store/appStore';
import { dataService } from '@/services/dataService';
import { AwsIcon } from '@/components/AwsIcon';

// Types for report data
interface ResourceSummary {
  totalResources: number;
  totalServices: number;
  totalAccounts: number;
  activeServices: number;
}

interface ServiceMetrics {
  serviceName: string;
  category: string;
  resourceCount: number;
  healthPercent: number;
  status: string;
}

interface AccountMetrics {
  accountName: string;
  totalResources: number;
  activeServices: number;
  categories: Record<string, number>;
}

function MetricCard({ 
  title, 
  value, 
  icon: Icon, 
  trend, 
  color = "primary",
  subtitle 
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  trend?: string;
  color?: string;
  subtitle?: string;
}) {
  const colorClasses = {
    primary: "bg-primary/10 text-primary",
    success: "bg-success/10 text-success", 
    warning: "bg-warning/10 text-warning",
    destructive: "bg-destructive/10 text-destructive",
    secondary: "bg-secondary/50 text-foreground"
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="liquid-glass rounded-2xl border border-border p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${colorClasses[color as keyof typeof colorClasses]}`}>
          <Icon className="w-6 h-6" />
        </div>
        {trend && (
          <span className="text-xs text-success flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            {trend}
          </span>
        )}
      </div>
      <div className="space-y-1">
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-sm font-medium text-foreground">{title}</p>
        {subtitle && (
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        )}
      </div>
    </motion.div>
  );
}

function ServiceDistributionChart({ data }: { data: Array<{ category: string; count: number; categoryKey: string }> }) {
  const total = data.reduce((sum, item) => sum + item.count, 0);
  
  return (
    <div className="liquid-glass rounded-2xl border border-border p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Service Distribution</h3>
        <PieChart className="w-5 h-5 text-muted-foreground" />
      </div>
      
      <div className="space-y-4">
        {data.map((item, index) => {
          const percentage = total > 0 ? (item.count / total * 100) : 0;
          return (
            <div key={item.category} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CategoryIcon category={item.categoryKey} size={16} className="text-primary" />
                  <span className="text-sm font-medium">{item.category}</span>
                </div>
                <span className="text-sm text-muted-foreground">
                  {item.count} ({percentage.toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${percentage}%` }}
                  transition={{ delay: index * 0.1, duration: 0.6 }}
                  className="h-2 bg-primary rounded-full"
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TopServicesTable({ services }: { services: ServiceMetrics[] }) {
  return (
    <div className="liquid-glass rounded-2xl border border-border p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Top Services by Resources</h3>
        <BarChart3 className="w-5 h-5 text-muted-foreground" />
      </div>
      
      <div className="overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-3 text-muted-foreground font-medium">Service</th>
              <th className="text-left py-3 text-muted-foreground font-medium">Category</th>
              <th className="text-right py-3 text-muted-foreground font-medium">Resources</th>
              <th className="text-right py-3 text-muted-foreground font-medium">Health</th>
              <th className="text-center py-3 text-muted-foreground font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {services.slice(0, 8).map((service, index) => (
              <motion.tr
                key={service.serviceName}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="border-b border-border/50 hover:bg-secondary/20"
              >
                <td className="py-3 font-medium">{service.serviceName.toUpperCase()}</td>
                <td className="py-3 text-muted-foreground">{service.category}</td>
                <td className="py-3 text-right font-medium">{service.resourceCount}</td>
                <td className="py-3 text-right">
                  <span className={`px-2 py-1 rounded text-xs ${
                    service.healthPercent >= 90 ? 'bg-success/20 text-success' :
                    service.healthPercent >= 70 ? 'bg-warning/20 text-warning' :
                    'bg-destructive/20 text-destructive'
                  }`}>
                    {service.healthPercent}%
                  </span>
                </td>
                <td className="py-3 text-center">
                  {service.status === 'healthy' ? (
                    <CheckCircle className="w-4 h-4 text-success mx-auto" />
                  ) : service.status === 'warning' ? (
                    <AlertTriangle className="w-4 h-4 text-warning mx-auto" />
                  ) : (
                    <XCircle className="w-4 h-4 text-destructive mx-auto" />
                  )}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AccountComparisonChart({ accounts }: { accounts: AccountMetrics[] }) {
  const maxResources = Math.max(...accounts.map(acc => acc.totalResources));
  
  return (
    <div className="liquid-glass rounded-2xl border border-border p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Account Resource Comparison</h3>
        <Users className="w-5 h-5 text-muted-foreground" />
      </div>
      
      <div className="space-y-4">
        {accounts.map((account, index) => (
          <div key={account.accountName} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{account.accountName}</span>
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span>{account.totalResources} resources</span>
                <span>{account.activeServices} services</span>
              </div>
            </div>
            <div className="w-full bg-secondary rounded-full h-3">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${maxResources > 0 ? (account.totalResources / maxResources * 100) : 0}%` }}
                transition={{ delay: index * 0.2, duration: 0.8 }}
                className="h-3 bg-gradient-to-r from-primary to-primary/60 rounded-full"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Reports() {
  const { selectedAccount, selectedRegion, serviceCategories } = useAppStore();
  const [summary, setSummary] = useState<ResourceSummary>({
    totalResources: 0,
    totalServices: 0,
    totalAccounts: 0,
    activeServices: 0
  });
  const [serviceMetrics, setServiceMetrics] = useState<ServiceMetrics[]>([]);
  const [accountMetrics, setAccountMetrics] = useState<AccountMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  useEffect(() => {
    loadReportData();
  }, []);

  const loadReportData = async () => {
    try {
      setLoading(true);
      
      // Load accounts and calculate metrics
      const accounts = await dataService.getAccounts();
      const allServiceMetrics: ServiceMetrics[] = [];
      const accountMetricsData: AccountMetrics[] = [];
      
      for (const account of accounts) {
        const categories = await dataService.getServiceCategories(account.name, 'ap-south-1');
        const accountServices = categories.flatMap(cat => cat.services);
        
        // Collect service metrics
        accountServices.forEach(service => {
          allServiceMetrics.push({
            serviceName: service.serviceName,
            category: service.category,
            resourceCount: service.resourceCount,
            healthPercent: service.healthPercent,
            status: service.status
          });
        });
        
        // Calculate account metrics
        const categoryBreakdown: Record<string, number> = {};
        categories.forEach(cat => {
          categoryBreakdown[cat.name] = cat.totalResources;
        });
        
        accountMetricsData.push({
          accountName: account.name,
          totalResources: account.totalResources,
          activeServices: accountServices.filter(s => s.resourceCount > 0).length,
          categories: categoryBreakdown
        });
      }
      
      // Sort services by resource count
      allServiceMetrics.sort((a, b) => b.resourceCount - a.resourceCount);
      
      // Calculate summary
      const totalResources = accountMetricsData.reduce((sum, acc) => sum + acc.totalResources, 0);
      const totalServices = allServiceMetrics.length;
      const activeServices = allServiceMetrics.filter(s => s.resourceCount > 0).length;
      
      setSummary({
        totalResources,
        totalServices,
        totalAccounts: accounts.length,
        activeServices
      });
      
      setServiceMetrics(allServiceMetrics);
      setAccountMetrics(accountMetricsData);
      setLastUpdated(new Date());
      
    } catch (error) {
      console.error('Failed to load report data:', error);
    } finally {
      setLoading(false);
    }
  };

  const categoryDistribution = serviceCategories.map(category => ({
    category: category.name,
    count: category.totalResources,
    categoryKey: category.key
  })).filter(item => item.count > 0);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto p-6">
          <div className="flex items-center justify-center h-64">
            <div className="flex items-center gap-3 text-muted-foreground">
              <RefreshCw className="w-6 h-6 animate-spin" />
              <span>Loading reports...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Reports Dashboard</h1>
            <p className="text-muted-foreground mt-1">
              Real-time insights from your AWS infrastructure
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Clock className="w-4 h-4" />
              Last updated: {lastUpdated.toLocaleTimeString()}
            </div>
            <button
              onClick={loadReportData}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary text-sm font-medium hover:bg-secondary/80 transition-colors">
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
        </div>

        {/* Summary Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Total Resources"
            value={summary.totalResources}
            icon={Server}
            color="primary"
            subtitle="Across all accounts"
          />
          <MetricCard
            title="Active Services"
            value={`${summary.activeServices}/${summary.totalServices}`}
            icon={Zap}
            color="success"
            subtitle="Services with resources"
          />
          <MetricCard
            title="AWS Accounts"
            value={summary.totalAccounts}
            icon={Users}
            color="secondary"
            subtitle="Connected accounts"
          />
          <MetricCard
            title="Categories"
            value={categoryDistribution.length}
            icon={Database}
            color="warning"
            subtitle="Active service categories"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ServiceDistributionChart data={categoryDistribution} />
          <AccountComparisonChart accounts={accountMetrics} />
        </div>

        {/* Top Services Table */}
        <TopServicesTable services={serviceMetrics} />

        {/* Additional Insights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-card rounded-xl border border-border p-6">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-semibold">Security Services</h3>
            </div>
            <div className="space-y-3">
              {serviceMetrics
                .filter(s => s.category === 'Security')
                .slice(0, 3)
                .map(service => (
                  <div key={service.serviceName} className="flex items-center justify-between">
                    <span className="text-sm">{service.serviceName.toUpperCase()}</span>
                    <span className="text-xs text-muted-foreground">{service.resourceCount} resources</span>
                  </div>
                ))}
            </div>
          </div>

          <div className="glass-card rounded-xl border border-border p-6">
            <div className="flex items-center gap-3 mb-4">
              <Activity className="w-5 h-5 text-success" />
              <h3 className="text-lg font-semibold">System Health</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Healthy Services</span>
                <span className="text-sm font-medium text-success">
                  {serviceMetrics.filter(s => s.status === 'healthy').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Warning Services</span>
                <span className="text-sm font-medium text-warning">
                  {serviceMetrics.filter(s => s.status === 'warning').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Critical Services</span>
                <span className="text-sm font-medium text-destructive">
                  {serviceMetrics.filter(s => s.status === 'critical').length}
                </span>
              </div>
            </div>
          </div>

          <div className="glass-card rounded-xl border border-border p-6">
            <div className="flex items-center gap-3 mb-4">
              <MapPin className="w-5 h-5 text-warning" />
              <h3 className="text-lg font-semibold">Regional Coverage</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Primary Region</span>
                <span className="text-sm font-medium">ap-south-1</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Total Regions</span>
                <span className="text-sm font-medium">1</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Multi-Region Services</span>
                <span className="text-sm font-medium">0</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}