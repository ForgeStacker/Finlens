import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus, BarChart3, Globe, Layers, Calendar } from "lucide-react";
import { useAppStore } from "@/store/appStore";
import { useMemo } from "react";

interface MetricCardProps {
  title: string;
  value: string | number;
  trend?: number;
  icon: React.ReactNode;
  delay?: number;
}

function MetricCard({ title, value, trend, icon, delay = 0 }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="liquid-glass rounded-2xl border border-border p-6 hover:border-primary/40 hover:glow-primary transition-all duration-500 group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
          {icon}
        </div>
        {trend !== undefined && trend !== 0 && (
          <div className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${
            trend > 0 ? "bg-success/10 text-success" : "bg-destructive/10 text-destructive"
          }`}>
            {trend > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {Math.abs(trend)}%
          </div>
        )}
        {trend === 0 && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground px-2 py-1 rounded-full bg-secondary">
            <Minus className="w-3 h-3" />
            0%
          </div>
        )}
      </div>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs text-muted-foreground mt-1">{title}</p>
    </motion.div>
  );
}

export function MetricCards() {
  const { selectedAccount, selectedRegion, serviceCategories, lastScanTimestamp } = useAppStore();

  const metrics = useMemo(() => {
    if (!selectedAccount || !selectedRegion) {
      return null;
    }

    const totalServices = serviceCategories.reduce((sum, category) => sum + category.services.length, 0);
    const totalResources = serviceCategories.reduce((sum, category) => sum + category.totalResources, 0);
    const activeServices = serviceCategories.reduce(
      (sum, category) => sum + category.services.filter(s => s.status === 'healthy').length, 
      0
    );

    // Format the last scan timestamp from real data
    const lastScan = lastScanTimestamp
      ? formatLastScanDate(lastScanTimestamp)
      : "No scan data";

    return {
      totalResources,
      totalServices,
      activeServices,
      categories: serviceCategories.length,
      lastScan
    };
  }, [selectedAccount, selectedRegion, serviceCategories, lastScanTimestamp]);

  if (!metrics) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        title="Total Resources"
        value={metrics.totalResources}
        icon={<BarChart3 className="w-6 h-6" />}
        delay={0}
      />
      <MetricCard
        title="Service Categories"
        value={metrics.categories}
        icon={<Layers className="w-6 h-6" />}
        delay={0.1}
      />
      <MetricCard
        title="Active Services"
        value={metrics.activeServices}
        icon={<Globe className="w-6 h-6" />}
        delay={0.2}
      />
      <MetricCard
        title="Last Scan"
        value={metrics.lastScan}
        icon={<Calendar className="w-6 h-6" />}
        delay={0.3}
      />
    </div>
  );
}

function formatLastScanDate(timestamp: string): string {
  const normalized = normalizeTimestamp(timestamp);
  if (!normalized) {
    return "No scan data";
  }

  const parsed = Date.parse(normalized);
  if (Number.isNaN(parsed)) {
    return "No scan data";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(new Date(parsed));
}

function normalizeTimestamp(raw: string): string | null {
  const trimmed = raw.trim();
  if (!trimmed) {
    return null;
  }

  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    return `${trimmed}T00:00:00`;
  }

  const hasTime = trimmed.includes("T") || trimmed.includes(" ");
  const replaced = hasTime ? trimmed.replace(" ", "T") : `${trimmed}T00:00:00`;
  return replaced;
}
