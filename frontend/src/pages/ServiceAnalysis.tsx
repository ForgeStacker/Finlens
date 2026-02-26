import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  TrendingDown,
  TrendingUp,
  Activity,
  DollarSign,
  CheckCircle,
  AlertCircle,
  Zap,
  Info,
  Loader2
} from "lucide-react";
import { Header } from "@/components/Header";
import { AwsIcon } from "@/components/AwsIcon";
import { useAppStore } from "@/store/appStore";
import { dataService } from "@/services/dataService";
import { formatServiceNameUppercase } from "@/utils/formatUtils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function ServiceAnalysis() {
  const { category: categoryParam, serviceName: serviceParam } = useParams();
  const navigate = useNavigate();
  const { selectedAccount, selectedRegion } = useAppStore();
  
  const [loading, setLoading] = useState(true);
  const [serviceData, setServiceData] = useState<any>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);

  useEffect(() => {
    async function loadData() {
      if (!serviceParam) return;
      
      setLoading(true);
      try {
        const accountName = selectedAccount?.name || 'My_Account';
        const regionCode = selectedRegion?.code || 'ap-south-1';
        
        const data = await dataService.getServiceDetails(accountName, regionCode, serviceParam);
        setServiceData(data);
        
        // Extract optimization/analysis data
        if (serviceParam === 'lambda' && data.optimization_summary) {
          setAnalysisData({
            type: 'lambda',
            summary: data.optimization_summary,
            resources: data.resources,
            metricsWindow: data.metrics_window_days || 30
          });
        } else {
          // Generic analysis for other services
          setAnalysisData({
            type: 'generic',
            resourceCount: data.resources?.length || 0,
            resources: data.resources
          });
        }
      } catch (error) {
        console.error('Failed to load analysis data:', error);
      } finally {
        setLoading(false);
      }
    }
    
    loadData();
  }, [serviceParam, selectedAccount, selectedRegion]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
            <p className="text-muted-foreground">Loading analysis...</p>
          </div>
        </div>
      </div>
    );
  }

  const renderLambdaAnalysis = () => {
    if (!analysisData || analysisData.type !== 'lambda') return null;
    
    const summary = analysisData.summary;
    const resources = analysisData.resources || [];
    
    // Calculate additional metrics
    const totalFunctions = summary.total_functions || 0;
    const idleFunctions = summary.idle_functions || 0;
    const overProvisioned = summary.over_provisioned_memory || 0;
    const underProvisioned = summary.under_provisioned_memory || 0;
    const highErrors = summary.high_error_rate || 0;
    const armCandidates = summary.arm_migration_candidates || 0;
    const potentialSavings = summary.potential_monthly_savings || 0;
    
    // Calculate total allocated resources (memory)
    const totalAllocatedMemory = resources.reduce((sum: number, fn: any) => 
      sum + (fn.memory_size || 0), 0);
    
    // Calculate utilization percentage (simplified)
    const activePercentage = totalFunctions > 0 
      ? ((totalFunctions - idleFunctions) / totalFunctions * 100).toFixed(1)
      : 0;
    
    // Get idle and optimization candidates
    const idleFunctionList = resources.filter((fn: any) => fn.optimization?.is_idle);
    const overProvisionedList = resources.filter((fn: any) => fn.optimization?.memory_status === 'over_provisioned');
    const highErrorList = resources.filter((fn: any) => fn.optimization?.high_error_rate);
    const armCandidateList = resources.filter((fn: any) => fn.optimization?.arm_candidate);

    return (
      <>
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Current Resources */}
          <Card className="glass">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Functions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{totalFunctions}</div>
              <p className="text-xs text-muted-foreground mt-1">Lambda functions</p>
            </CardContent>
          </Card>

          {/* Resources Allocated */}
          <Card className="glass">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Memory Allocated</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{(totalAllocatedMemory / 1024).toFixed(1)}</div>
              <p className="text-xs text-muted-foreground mt-1">GB total memory</p>
            </CardContent>
          </Card>

          {/* Utilization */}
          <Card className="glass">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Utilization</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-success">{activePercentage}%</div>
              <p className="text-xs text-muted-foreground mt-1">Active functions</p>
            </CardContent>
          </Card>

          {/* Cost Savings */}
          <Card className="glass">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Potential Savings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-500">${potentialSavings.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground mt-1">per month</p>
            </CardContent>
          </Card>
        </div>

        {/* Issues Overview */}
        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-amber-500" />
              Optimization Opportunities
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {idleFunctions > 0 && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                <div className="flex items-center gap-3">
                  <Activity className="w-5 h-5 text-red-500" />
                  <div>
                    <div className="font-medium text-red-500">Idle Functions</div>
                    <div className="text-sm text-muted-foreground">No invocations in {analysisData.metricsWindow} days</div>
                  </div>
                </div>
                <Badge variant="destructive">{idleFunctions}</Badge>
              </div>
            )}
            
            {overProvisioned > 0 && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <div className="flex items-center gap-3">
                  <TrendingDown className="w-5 h-5 text-amber-500" />
                  <div>
                    <div className="font-medium text-amber-500">Over-provisioned Memory</div>
                    <div className="text-sm text-muted-foreground">Can reduce memory allocation</div>
                  </div>
                </div>
                <Badge variant="outline" className="border-amber-500 text-amber-500">{overProvisioned}</Badge>
              </div>
            )}
            
            {underProvisioned > 0 && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-5 h-5 text-purple-500" />
                  <div>
                    <div className="font-medium text-purple-500">Under-provisioned Memory</div>
                    <div className="text-sm text-muted-foreground">Need more memory for performance</div>
                  </div>
                </div>
                <Badge variant="outline" className="border-purple-500 text-purple-500">{underProvisioned}</Badge>
              </div>
            )}
            
            {highErrors > 0 && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-orange-500/10 border border-orange-500/20">
                <div className="flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 text-orange-500" />
                  <div>
                    <div className="font-medium text-orange-500">High Error Rate</div>
                    <div className="text-sm text-muted-foreground">Functions with &gt;5% error rate</div>
                  </div>
                </div>
                <Badge variant="outline" className="border-orange-500 text-orange-500">{highErrors}</Badge>
              </div>
            )}
            
            {armCandidates > 0 && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                <div className="flex items-center gap-3">
                  <Zap className="w-5 h-5 text-blue-500" />
                  <div>
                    <div className="font-medium text-blue-500">ARM/Graviton Ready</div>
                    <div className="text-sm text-muted-foreground">20% cost reduction opportunity</div>
                  </div>
                </div>
                <Badge variant="outline" className="border-blue-500 text-blue-500">{armCandidates}</Badge>
              </div>
            )}
            
            {idleFunctions === 0 && overProvisioned === 0 && underProvisioned === 0 && highErrors === 0 && armCandidates === 0 && (
              <div className="flex items-center gap-3 p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <div className="text-green-500 font-medium">All functions are optimized!</div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Detailed Recommendations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Idle Functions */}
          {idleFunctionList.length > 0 && (
            <Card className="glass">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="w-4 h-4 text-red-500" />
                  Idle Functions ({idleFunctionList.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {idleFunctionList.slice(0, 10).map((fn: any, idx: number) => (
                    <div key={idx} className="p-2 rounded bg-secondary/50 border border-border">
                      <div className="font-medium text-sm">{fn.resource_name}</div>
                      <div className="text-xs text-muted-foreground">Memory: {fn.memory_size}MB</div>
                      <div className="text-xs text-green-600 mt-1">
                        Savings: ${fn.optimization?.potential_savings?.toFixed(2) || '0.00'}/month
                      </div>
                    </div>
                  ))}
                  {idleFunctionList.length > 10 && (
                    <div className="text-xs text-muted-foreground text-center pt-2">
                      + {idleFunctionList.length - 10} more
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Over-provisioned Functions */}
          {overProvisionedList.length > 0 && (
            <Card className="glass">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <TrendingDown className="w-4 h-4 text-amber-500" />
                  Over-provisioned ({overProvisionedList.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {overProvisionedList.slice(0, 10).map((fn: any, idx: number) => (
                    <div key={idx} className="p-2 rounded bg-secondary/50 border border-border">
                      <div className="font-medium text-sm">{fn.resource_name}</div>
                      <div className="text-xs text-muted-foreground">
                        Memory: {fn.memory_size}MB | Invocations: {fn.optimization?.invocations?.toLocaleString() || 0}
                      </div>
                      {fn.optimization?.recommendations && fn.optimization.recommendations.length > 0 && (
                        <div className="text-xs text-amber-600 mt-1">
                          {fn.optimization.recommendations[0]}
                        </div>
                      )}
                    </div>
                  ))}
                  {overProvisionedList.length > 10 && (
                    <div className="text-xs text-muted-foreground text-center pt-2">
                      + {overProvisionedList.length - 10} more
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* ARM Migration Candidates */}
          {armCandidateList.length > 0 && (
            <Card className="glass">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Zap className="w-4 h-4 text-blue-500" />
                  ARM Migration Ready ({armCandidateList.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {armCandidateList.slice(0, 10).map((fn: any, idx: number) => (
                    <div key={idx} className="p-2 rounded bg-secondary/50 border border-border">
                      <div className="font-medium text-sm">{fn.resource_name}</div>
                      <div className="text-xs text-muted-foreground">
                        Runtime: {fn.runtime} | Architecture: {fn.architecture}
                      </div>
                      <div className="text-xs text-blue-600 mt-1">
                        Migrate to arm64 for ~20% cost reduction
                      </div>
                    </div>
                  ))}
                  {armCandidateList.length > 10 && (
                    <div className="text-xs text-muted-foreground text-center pt-2">
                      + {armCandidateList.length - 10} more
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* High Error Rate */}
          {highErrorList.length > 0 && (
            <Card className="glass">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-orange-500" />
                  High Error Rate ({highErrorList.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {highErrorList.slice(0, 10).map((fn: any, idx: number) => (
                    <div key={idx} className="p-2 rounded bg-secondary/50 border border-border">
                      <div className="font-medium text-sm">{fn.resource_name}</div>
                      <div className="text-xs text-muted-foreground">
                        Error Rate: {fn.optimization?.error_rate?.toFixed(2) || 0}%
                      </div>
                      <div className="text-xs text-orange-600 mt-1">
                        Investigate function reliability
                      </div>
                    </div>
                  ))}
                  {highErrorList.length > 10 && (
                    <div className="text-xs text-muted-foreground text-center pt-2">
                      + {highErrorList.length - 10} more
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </>
    );
  };

  const renderGenericAnalysis = () => {
    if (!analysisData || analysisData.type !== 'generic') return null;
    
    const resourceCount = analysisData.resourceCount || 0;
    
    return (
      <Card className="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="w-5 h-5 text-blue-500" />
            Analysis Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="text-4xl font-bold mb-2">{resourceCount}</div>
            <p className="text-muted-foreground mb-4">Total Resources</p>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <Info className="w-4 h-4 text-blue-500" />
              <span className="text-sm text-blue-500">Detailed analysis coming soon for this service</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm">
          <button 
            onClick={() => navigate(`/service/${categoryParam}/${serviceParam}`)} 
            className="text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to {serviceParam ? formatServiceNameUppercase(serviceParam) : 'Service'}
          </button>
        </div>

        {/* Analysis Header */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-4"
        >
          <AwsIcon service={serviceParam || ''} size={56} className="rounded-2xl text-primary flex-shrink-0" />
          <div>
            <h1 className="text-2xl font-bold">
              {serviceParam ? formatServiceNameUppercase(serviceParam) : 'Service'} Analysis
            </h1>
            <p className="text-sm text-muted-foreground">
              Optimization insights and recommendations
            </p>
          </div>
        </motion.div>

        {/* Analysis Content */}
        {analysisData?.type === 'lambda' ? renderLambdaAnalysis() : renderGenericAnalysis()}
      </div>
    </div>
  );
}
