import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Activity, AlertCircle, TrendingDown, TrendingUp, Zap, CheckCircle } from "lucide-react";

interface LambdaOptimization {
  is_idle: boolean;
  invocations: number;
  avg_duration_ms: number;
  max_duration_ms: number;
  errors: number;
  throttles: number;
  error_rate: number;
  memory_status: 'optimal' | 'over_provisioned' | 'under_provisioned';
  memory_utilization_percent: number;
  high_error_rate: boolean;
  arm_candidate: boolean;
  potential_savings: number;
  recommendations: string[];
}

interface LambdaFunction {
  function_name: string;
  runtime: string;
  memory_size: number;
  timeout: number;
  architecture: string;
  trigger_types: string[];
  optimization?: LambdaOptimization;
}

interface LambdaFunctionCardProps {
  func: LambdaFunction;
}

export function LambdaFunctionCard({ func }: LambdaFunctionCardProps) {
  const opt = func.optimization;
  
  if (!opt) {
    return (
      <Card className="p-4">
        <div className="font-medium">{func.function_name}</div>
        <div className="text-sm text-muted-foreground mt-1">
          {func.runtime} • {func.memory_size}MB • {func.architecture}
        </div>
      </Card>
    );
  }

  // Determine status badge
  const getStatusBadge = () => {
    if (opt.is_idle) {
      return <Badge variant="destructive" className="gap-1"><Activity className="w-3 h-3" /> Idle</Badge>;
    }
    if (opt.memory_status === 'over_provisioned') {
      return <Badge variant="outline" className="gap-1 border-amber-500 text-amber-500"><TrendingDown className="w-3 h-3" /> Over-provisioned</Badge>;
    }
    if (opt.memory_status === 'under_provisioned') {
      return <Badge variant="outline" className="gap-1 border-purple-500 text-purple-500"><TrendingUp className="w-3 h-3" /> Under-provisioned</Badge>;
    }
    if (opt.high_error_rate) {
      return <Badge variant="outline" className="gap-1 border-orange-500 text-orange-500"><AlertCircle className="w-3 h-3" /> High Errors</Badge>;
    }
    return <Badge variant="outline" className="gap-1 border-green-500 text-green-500"><CheckCircle className="w-3 h-3" /> Optimized</Badge>;
  };

  return (
    <Card className="p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-medium truncate">{func.function_name}</h3>
          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
            <span>{func.runtime}</span>
            <span>•</span>
            <span>{func.memory_size}MB</span>
            <span>•</span>
            <span>{func.architecture}</span>
          </div>
        </div>
        {getStatusBadge()}
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-2 mb-3 text-sm">
        <div>
          <div className="text-muted-foreground text-xs">Invocations (30d)</div>
          <div className="font-semibold">{opt.invocations.toLocaleString()}</div>
        </div>
        <div>
          <div className="text-muted-foreground text-xs">Avg Duration</div>
          <div className="font-semibold">{opt.avg_duration_ms.toFixed(0)}ms</div>
        </div>
        <div>
          <div className="text-muted-foreground text-xs">Error Rate</div>
          <div className="font-semibold">{opt.error_rate.toFixed(2)}%</div>
        </div>
        <div>
          <div className="text-muted-foreground text-xs">Potential Savings</div>
          <div className="font-semibold text-green-600">${opt.potential_savings.toFixed(2)}/mo</div>
        </div>
      </div>

      {/* Recommendations */}
      {opt.recommendations && opt.recommendations.length > 0 && (
        <div className="space-y-1">
          <div className="text-xs font-medium text-muted-foreground">Recommendations:</div>
          {opt.recommendations.map((rec, idx) => (
            <div key={idx} className="text-xs text-muted-foreground flex items-start gap-1">
              <span className="text-primary mt-0.5">•</span>
              <span className="flex-1">{rec}</span>
            </div>
          ))}
        </div>
      )}

      {/* ARM Migration */}
      {opt.arm_candidate && (
        <div className="mt-2 pt-2 border-t border-border/50">
          <div className="flex items-center gap-2 text-xs">
            <Zap className="w-3 h-3 text-blue-500" />
            <span className="text-blue-500 font-medium">ARM/Graviton migration ready</span>
          </div>
        </div>
      )}
    </Card>
  );
}
