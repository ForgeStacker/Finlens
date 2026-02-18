import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, TrendingDown, Zap, Activity, DollarSign } from "lucide-react";

interface OptimizationSummary {
  total_functions: number;
  idle_functions: number;
  over_provisioned_memory: number;
  under_provisioned_memory: number;
  high_error_rate: number;
  arm_migration_candidates: number;
  potential_monthly_savings: number;
}

interface LambdaOptimizationProps {
  summary: OptimizationSummary;
}

export function LambdaOptimizationCard({ summary }: LambdaOptimizationProps) {
  const hasSavings = summary.potential_monthly_savings > 0;
  const hasIssues = summary.idle_functions > 0 || 
                    summary.over_provisioned_memory > 0 || 
                    summary.high_error_rate > 0;

  return (
    <Card className="glass">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-amber-500" />
          Lambda Optimization Insights
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Savings Summary */}
        {hasSavings && (
          <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-green-500" />
                <span className="font-semibold text-green-500">Potential Savings</span>
              </div>
              <span className="text-2xl font-bold text-green-500">
                ${summary.potential_monthly_savings.toFixed(2)}/mo
              </span>
            </div>
          </div>
        )}

        {/* Optimization Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {/* Idle Functions */}
          {summary.idle_functions > 0 && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
              <div className="text-sm text-muted-foreground mb-1">Idle Functions</div>
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-red-500" />
                <span className="text-xl font-bold text-red-500">
                  {summary.idle_functions}
                </span>
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                0 invocations
              </div>
            </div>
          )}

          {/* Over-provisioned */}
          {summary.over_provisioned_memory > 0 && (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <div className="text-sm text-muted-foreground mb-1">Over-provisioned</div>
              <div className="flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-amber-500" />
                <span className="text-xl font-bold text-amber-500">
                  {summary.over_provisioned_memory}
                </span>
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Can reduce memory
              </div>
            </div>
          )}

          {/* High Error Rate */}
          {summary.high_error_rate > 0 && (
            <div className="p-3 rounded-lg bg-orange-500/10 border border-orange-500/20">
              <div className="text-sm text-muted-foreground mb-1">High Errors</div>
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-orange-500" />
                <span className="text-xl font-bold text-orange-500">
                  {summary.high_error_rate}
                </span>
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                &gt;5% error rate
              </div>
            </div>
          )}

          {/* ARM Candidates */}
          {summary.arm_migration_candidates > 0 && (
            <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <div className="text-sm text-muted-foreground mb-1">ARM Ready</div>
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-blue-500" />
                <span className="text-xl font-bold text-blue-500">
                  {summary.arm_migration_candidates}
                </span>
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                20% cost reduction
              </div>
            </div>
          )}

          {/* Under-provisioned */}
          {summary.under_provisioned_memory > 0 && (
            <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
              <div className="text-sm text-muted-foreground mb-1">Under-provisioned</div>
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-purple-500" />
                <span className="text-xl font-bold text-purple-500">
                  {summary.under_provisioned_memory}
                </span>
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Need more memory
              </div>
            </div>
          )}
        </div>

        {/* No Issues */}
        {!hasIssues && (
          <div className="text-center py-4 text-muted-foreground">
            <div className="flex items-center justify-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                <span className="text-green-500 text-lg">✓</span>
              </div>
            </div>
            <p className="font-medium">All Lambda functions are optimized</p>
            <p className="text-sm">No optimization opportunities found</p>
          </div>
        )}

        {/* Total Functions */}
        <div className="pt-3 border-t border-border/50">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Total Functions Analyzed</span>
            <span className="font-semibold">{summary.total_functions}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
