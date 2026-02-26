import { motion } from "framer-motion";
import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  TrendingUp, TrendingDown, Filter, X, Loader2
} from "lucide-react";
import { useAppStore } from "@/store/appStore";
import { AwsIcon } from "@/components/AwsIcon";
import { CategoryIcon } from "@/components/CategoryIcon";
import { formatServiceName } from "@/utils/formatUtils";
import type { AWSService } from "@/services/types";

const statusColors = {
  healthy: "bg-success",
  warning: "bg-warning",
  critical: "bg-destructive",
};

const scanStatusColors = {
  success: "bg-success/10 text-success",
  failed: "bg-destructive/10 text-destructive", 
  partial: "bg-warning/10 text-warning",
};

function ServiceCard({ service, index }: { service: AWSService; index: number }) {
  const navigate = useNavigate();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      onClick={() =>
        navigate(
          `/service/${encodeURIComponent(service.categoryKey)}/${encodeURIComponent(service.serviceName)}`
        )
      }
      className="liquid-glass rounded-2xl border border-border p-6 cursor-pointer group hover:border-primary/40 hover:glow-primary transition-all duration-500 hover:-translate-y-1"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <AwsIcon service={service.serviceName} size={44} className="rounded-2xl text-primary flex-shrink-0" />
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold">{formatServiceName(service.name)}</h3>
              <span className={`w-2 h-2 rounded-full ${statusColors[service.status]}`} />
            </div>
            <p className="text-xs text-muted-foreground">{service.description}</p>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="flex items-center gap-4 mb-3">
        <div>
          <span className="text-xl font-bold">{service.resourceCount}</span>
          <span className="text-xs text-muted-foreground ml-1">{service.resourceCount === 1 ? 'Resource' : 'Resources'}</span>
        </div>
      </div>

      {/* Active Bar */}
      {service.resourceCount > 0 ? (
        <div className="mb-3">
          <div className="flex items-center justify-between text-[10px] mb-1">
            <span className="text-muted-foreground">Active</span>
            <span className="font-medium">{service.healthPercent}%</span>
          </div>
          <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${service.healthPercent}%` }}
              transition={{ delay: index * 0.05 + 0.3, duration: 0.6 }}
              className={`h-full rounded-full ${
                service.healthPercent >= 90
                  ? "bg-success"
                  : service.healthPercent >= 70
                  ? "bg-warning"
                  : "bg-destructive"
              }`}
            />
          </div>
        </div>
      ) : (
        <div className="mb-3">
          <div className="flex items-center justify-between text-[10px] mb-1">
            <span className="text-muted-foreground">Active</span>
            <span className="font-medium text-muted-foreground">No resources</span>
          </div>
          <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
            <div className="h-full rounded-full bg-muted" />
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-border">
        <span className={`text-xs px-2 py-1 rounded ${scanStatusColors[service.scanStatus]}`}>
          {service.scanStatus}
        </span>
        {service.costEstimate && service.costEstimate > 0 && (
          <div className="text-right">
            <div className="flex items-center gap-1">
              <span className="text-sm font-semibold">${service.costEstimate.toFixed(2)}</span>
              {service.costTrend && service.costTrend !== 0 && (
                <span className={`text-xs ${service.costTrend > 0 ? 'text-destructive' : 'text-success'}`}>
                  {service.costTrend > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                </span>
              )}
            </div>
            <span className="text-[10px] text-muted-foreground">Monthly est.</span>
          </div>
        )}
      </div>
    </motion.div>
  );
}

export function ServiceGrid() {
  const { serviceCategories, selectedRegion, loading } = useAppStore();
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);

  // Initialize selected categories with all categories when data loads
  useMemo(() => {
    if (serviceCategories.length > 0 && selectedCategories.length === 0) {
      setSelectedCategories(serviceCategories.map(cat => cat.key));
    }
  }, [serviceCategories, selectedCategories.length]);

  if (!selectedRegion) {
    return (
      <div className="glass rounded-xl p-6 text-center">
        <p className="text-muted-foreground">Select a region to view services</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="glass rounded-xl p-6 text-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-2" />
        <p className="text-muted-foreground">Loading services...</p>
      </div>
    );
  }

  if (serviceCategories.length === 0) {
    return (
      <div className="glass rounded-xl p-6 text-center">
        <p className="text-muted-foreground">No services found for {selectedRegion.name}</p>
      </div>
    );
  }

  // Individual service priority — lower number appears first
  const SERVICE_PRIORITY: Record<string, number> = {
    rds: 1,
    ec2: 2,
    lambda: 3,
    eks: 4,
    s3: 5,
    iam: 6,
    vpc: 7,
    elb: 8,
    ecr: 9,
    cloudwatchlogs: 10,
    cloudwatchalarm: 11,
    apigateway: 12,
    sqs: 13,
    sns: 14,
    elasticache: 15,
    secretsmanager: 16,
    kms: 17,
    kinesis: 18,
    dms: 19,
    cloudwatchevent: 20,
    ecs: 21,
    asg: 22,
    ami: 23,
    ebs: 24,
    cloudwatch: 25,
    snapshot: 26,
    efs: 27,
    dynamodb: 28,
    redshift: 29,
    cloudfront: 30,
    route53: 31,
    elasticip: 32,
    acm: 33,
    waf: 34,
    guardduty: 35,
    inspector: 36,
    cloudtrail: 37,
    config: 38,
    cloudformation: 39,
    ssm: 40,
    controltower: 41,
    eventbridge: 42,
    stepfunctions: 43,
    ses: 44,
    athena: 45,
    glue: 46,
    emr: 47,
    opensearch: 48,
    costexplorer: 49,
    budgets: 50,
    cur: 51,
    savingsplans: 52,
    reservedinstances: 53,
    computeoptimizer: 54,
    codecommit: 55,
    codebuild: 56,
    codedeploy: 57,
    codepipeline: 58,
    migrationhub: 59,
    datasync: 60,
    mgn: 61,
    docdb: 62,
    neptune: 63,
    aurora: 64,
    msk: 65,
    organizations: 66,
    servicecatalog: 67,
    elasticbeanstalk: 68,
    fargate: 69,
  };

  const getPriority = (name: string) =>
    SERVICE_PRIORITY[name.toLowerCase()] ?? 999;

  // Flatten all services, filter by selected categories, then sort by priority
  const allServices = serviceCategories
    .flatMap(category =>
      selectedCategories.includes(category.key) ? category.services : []
    )
    .sort((a, b) => getPriority(a.serviceName) - getPriority(b.serviceName));

  const totalServicesCount = serviceCategories.reduce((sum, cat) => sum + cat.services.length, 0);
  const activeCategoriesCount = serviceCategories.filter(cat => selectedCategories.includes(cat.key)).length;

  const toggleCategory = (categoryKey: string) => {
    setSelectedCategories(prev => 
      prev.includes(categoryKey) 
        ? prev.filter(key => key !== categoryKey)
        : [...prev, categoryKey]
    );
  };

  const selectAllCategories = () => {
    setSelectedCategories(serviceCategories.map(cat => cat.key));
  };

  const clearAllCategories = () => {
    setSelectedCategories([]);
  };

  return (
    <div>
      {/* Header with filter */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold">Services</h2>
          <p className="text-xs text-muted-foreground mt-1">
            Showing {allServices.length} of {totalServicesCount} services from {activeCategoriesCount} categories
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary border border-border text-sm hover:bg-secondary/80 transition-colors"
        >
          <Filter className="w-4 h-4" />
          Filter Categories
          {selectedCategories.length < serviceCategories.length && (
            <span className="bg-primary text-primary-foreground text-xs px-1.5 py-0.5 rounded-full">
              {selectedCategories.length}
            </span>
          )}
        </button>
      </div>

      {/* Category Filter */}
      {showFilters && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="liquid-glass rounded-2xl border border-border p-6 mb-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold">Filter by Categories</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={selectAllCategories}
                className="text-xs text-primary hover:text-primary/80 transition-colors"
              >
                Select All
              </button>
              <span className="text-xs text-muted-foreground">|</span>
              <button
                onClick={clearAllCategories}
                className="text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                Clear All
              </button>
              <button
                onClick={() => setShowFilters(false)}
                className="ml-2 p-1 hover:bg-secondary rounded transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
            {serviceCategories.map((category) => (
              <label
                key={category.key}
                className="flex items-center gap-2 p-2 rounded-lg cursor-pointer hover:bg-secondary/50 transition-colors"
              >
                <input
                  type="checkbox"
                  checked={selectedCategories.includes(category.key)}
                  onChange={() => toggleCategory(category.key)}
                  className="accent-primary"
                />
                <CategoryIcon category={category.key} size={18} className="text-primary flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <span className="text-sm font-medium block truncate">{category.name}</span>
                  <span className="text-xs text-muted-foreground">{category.services.length} services</span>
                </div>
              </label>
            ))}
          </div>
        </motion.div>
      )}

      {/* Services Grid */}
      {allServices.length === 0 ? (
        <div className="glass rounded-xl p-6 text-center">
          <p className="text-muted-foreground">No services found for selected categories</p>
          <button
            onClick={selectAllCategories}
            className="mt-2 text-sm text-primary hover:text-primary/80 transition-colors"
          >
            Show all categories
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {allServices.map((service, index) => (
            <ServiceCard key={service.id} service={service} index={index} />
          ))}
        </div>
      )}
    </div>
  );
}
