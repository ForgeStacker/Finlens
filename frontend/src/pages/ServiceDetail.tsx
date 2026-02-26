import React, { useState, useMemo, useRef, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Search,
  Download,
  Columns3,
  Copy,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Check,
  Tag,
} from "lucide-react";
import { Header } from "@/components/Header";
import { AwsIcon } from "@/components/AwsIcon";
import { DataPopover } from "@/components/ui/DataPopover";
import { DetailSidebar } from "@/components/ui/DetailSidebar";
import { useAppStore } from "@/store/appStore";
import { format, formatDistanceToNow } from "date-fns";
import { dataService } from "@/services/dataService";
import { formatServiceNameUppercase } from "@/utils/formatUtils";
import type { BackendServiceDetail, ServiceResource } from "@/services/types";

type SortDir = "asc" | "desc" | null;
type TagItem = { Key: string; Value: string };

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const toTagArray = (value: unknown): TagItem[] => {
  // already an array of {Key,Value}
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (isRecord(item)) {
          const key = item["Key"];
          const tagValue = item["Value"];
          if (typeof key === "string" && typeof tagValue === "string") {
            return { Key: key, Value: tagValue };
          }
        }
        return null;
      })
      .filter((item): item is TagItem => item !== null);
  }

  // plain object { key: value }
  if (isRecord(value)) {
    return Object.entries(value)
      .filter(([, tagValue]) => typeof tagValue === "string")
      .map(([key, tagValue]) => ({ Key: key, Value: tagValue as string }));
  }

  // flat CSV string: "KEY=VALUE KEY2=VALUE2 KEY3=value with spaces"
  if (typeof value === "string" && value.trim().length > 0) {
    // Split on whitespace that is followed by a KEY= pattern (key has no spaces)
    const segments = value.trim().split(/\s+(?=[^\s=]+=)/);
    return segments
      .map((seg) => {
        const eqIdx = seg.indexOf("=");
        if (eqIdx === -1) return null;
        const k = seg.slice(0, eqIdx).trim();
        const v = seg.slice(eqIdx + 1).trim();
        return k ? { Key: k, Value: v } : null;
      })
      .filter((item): item is TagItem => item !== null);
  }

  return [];
};

const getStringField = (resource: ServiceResource, field: string): string | undefined => {
  const rawValue = resource[field];
  return typeof rawValue === "string" && rawValue.length > 0 ? rawValue : undefined;
};

const getRowId = (resource: ServiceResource, index: number): string => {
  const candidates = ["instance_id", "resource_id", "id", "resource_name"];
  for (const field of candidates) {
    const value = getStringField(resource, field);
    if (value) {
      return value;
    }
  }
  return index.toString();
};

const stateColors: Record<string, string> = {
  running: "bg-success/15 text-success",
  stopped: "bg-warning/15 text-warning", 
  terminated: "bg-destructive/15 text-destructive",
  active: "bg-success/15 text-success",
  available: "bg-success/15 text-success",
  pending: "bg-warning/15 text-warning",
  failed: "bg-destructive/15 text-destructive",
  error: "bg-destructive/15 text-destructive",
  creating: "bg-warning/15 text-warning",
  deleting: "bg-warning/15 text-warning",
  updating: "bg-warning/15 text-warning",
  healthy: "bg-success/15 text-success",
  unhealthy: "bg-destructive/15 text-destructive",
};

// Function to get state color with fallback for unknown states
function getStateColor(state: string): string {
  const normalizedState = state?.toLowerCase();
  return stateColors[normalizedState] || "bg-secondary/15 text-muted-foreground";
}

interface Column {
  key: string;
  label: string;
  visible: boolean;
  sortable: boolean;
}

/** Convert a snake_case / PascalCase / camelCase key to a human-readable label */
function keyToLabel(key: string): string {
  // Split on underscores, capitals, and digit boundaries
  return key
    .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')   // ABCDef -> ABC Def
    .replace(/([a-z\d])([A-Z])/g, '$1 $2')         // camelCase -> camel Case
    .replace(/_/g, ' ')                             // snake_case -> snake case
    .replace(/\b\w/g, (c) => c.toUpperCase())       // Title Case
    .trim();
}

/** Number of columns visible by default; the rest are toggled via the Columns button. */
const DEFAULT_VISIBLE_COUNT = 13;

/**
 * Build Column[] from the ordered list the API returned (same order as Excel).
 * Only the first DEFAULT_VISIBLE_COUNT columns are shown by default.
 */
function buildColumnsFromApiOrder(apiColumns: string[]): Column[] {
  return apiColumns.map((key, idx) => ({
    key,
    label: keyToLabel(key),
    visible: idx < DEFAULT_VISIBLE_COUNT,
    sortable: true,
  }));
}

// Fallback when API doesn't return columns (old data format)
function generateInitialColumns(): Column[] {
  return [
    { key: "resource_name", label: "Name", visible: true, sortable: true },
    { key: "resource_id", label: "Resource ID", visible: true, sortable: true },
    { key: "resource_type", label: "Type", visible: true, sortable: true },
    { key: "status", label: "Status", visible: true, sortable: true },
    { key: "state", label: "State", visible: true, sortable: true },
    { key: "region", label: "Region", visible: true, sortable: true },
    { key: "instance_type", label: "Instance Type", visible: true, sortable: true },
    { key: "launch_time", label: "Created", visible: true, sortable: true },
    { key: "vpc_id", label: "VPC ID", visible: true, sortable: true },
  ];
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      className="p-1 rounded hover:bg-secondary transition-colors"
      title="Copy"
    >
      {copied ? <Check className="w-3 h-3 text-success" /> : <Copy className="w-3 h-3 text-muted-foreground" />}
    </button>
  );
}

function CellValue({ value, colKey }: { value: unknown; colKey: string }) {
  if (value === null || value === undefined) return <span className="text-muted-foreground">—</span>;

  if (colKey === "state" || colKey === "status") {
    const s = String(value);
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStateColor(s)}`}>
        {s}
      </span>
    );
  }

  if (colKey === "instance_id" || colKey === "resource_id") {
    return (
      <div className="flex items-center gap-1.5">
        <span className="font-mono text-xs text-accent">{String(value)}</span>
        <CopyButton text={String(value)} />
      </div>
    );
  }

  if (colKey === "launch_time" || colKey === "created_time") {
    const d = new Date(String(value));
    return (
      <div className="text-xs">
        <span>{format(d, "MMM d, yyyy")}</span>
        <span className="text-muted-foreground ml-1">({formatDistanceToNow(d, { addSuffix: true })})</span>
      </div>
    );
  }

  // Handle tags object — match "Tags", "tags", "TAGS" etc.
  if (colKey.toLowerCase() === "tags") {
    const tagArray = toTagArray(value);
    if (tagArray.length === 0) return <span className="text-muted-foreground text-xs">—</span>;
    return (
      <div onClick={(e) => e.stopPropagation()}>
        <DataPopover data={tagArray} type="tags" title="Resource Tags" />
      </div>
    );
  }

  // Handle VPC config object
  if (colKey === "vpc_config" && isRecord(value)) {
    return (
      <div onClick={(e) => e.stopPropagation()}>
        <DataPopover data={value} type="vpc_config" title="VPC Configuration" />
      </div>
    );
  }

  // Handle security groups
  if (colKey === "vpc_security_groups" && Array.isArray(value)) {
    return (
      <div onClick={(e) => e.stopPropagation()}>
        <DataPopover data={value} type="security_groups" title="Security Groups" />
      </div>
    );
  }

  // Handle subnets (from db_subnet_group)
  if (colKey === "db_subnet_group" && isRecord(value) && Array.isArray(value.Subnets)) {
    return (
      <div onClick={(e) => e.stopPropagation()}>
        <DataPopover data={value.Subnets} type="subnets" title="Database Subnets" />
      </div>
    );
  }

  // Handle subnet group subnets
  if (colKey === "subnets" && Array.isArray(value)) {
    return (
      <div onClick={(e) => e.stopPropagation()}>
        <DataPopover data={value} type="subnets" title="Subnets" />
      </div>
    );
  }

  // Handle availability zones
  if (colKey === "availability_zones" && Array.isArray(value)) {
    return (
      <div onClick={(e) => e.stopPropagation()}>
        <DataPopover data={value} type="array" title="Availability Zones" />
      </div>
    );
  }

  // Handle CloudWatch logs exports
  if (colKey === "enabled_cloudwatch_logs_exports" && Array.isArray(value)) {
    return (
      <div onClick={(e) => e.stopPropagation()}>
        <DataPopover data={value} type="array" title="CloudWatch Log Exports" />
      </div>
    );
  }

  // Handle endpoint objects
  if (colKey === "endpoint" && isRecord(value)) {
    return (
      <div onClick={(e) => e.stopPropagation()}>
        <DataPopover data={value} type="object" title="Endpoint Details" />
      </div>
    );
  }

  // Handle arrays
  if (Array.isArray(value)) {
    // Skip empty arrays
    if (value.length === 0) {
      return <span className="text-muted-foreground text-xs">—</span>;
    }
    return (
      <div onClick={(e) => e.stopPropagation()}>
        <DataPopover data={value} type="array" title={`${colKey.replace('_', ' ').toUpperCase()}`} />
      </div>
    );
  }

  // Handle complex objects
  if (isRecord(value)) {
    // Skip empty objects
    if (Object.keys(value).length === 0) {
      return <span className="text-muted-foreground text-xs">—</span>;
    }
    return (
      <div onClick={(e) => e.stopPropagation()}>
        <DataPopover data={value} type="object" title={`${colKey.replace('_', ' ').toUpperCase()}`} />
      </div>
    );
  }

  // Handle URLs/endpoints
  if (colKey === "endpoint" || (typeof value === "string" && value.startsWith("https://"))) {
    const url = String(value);
    return (
      <div className="flex items-center gap-1">
        <span className="text-xs text-blue-400 truncate max-w-[200px]" title={url}>
          {url}
        </span>
        <CopyButton text={url} />
      </div>
    );
  }

  return <span className="text-sm">{String(value)}</span>;
}

export default function ServiceDetail() {
  const { category: categoryParam, serviceName: serviceParam, serviceId } = useParams();
  const navigate = useNavigate();
  const { selectedAccount, selectedRegion, serviceCategories, loadServiceCategories, loadAccounts, loadRegions, accounts, regions } = useAppStore();
  
  // Parse route params to get category and service name
  let categoryKey = categoryParam || "";
  let serviceName = serviceParam || "";
  // Backward-compat: handle old /service/{category}-{service} style
  if ((!categoryKey || !serviceName) && serviceId) {
    const [fallbackCategory, ...rest] = serviceId.split("-");
    if (fallbackCategory && rest.length) {
      categoryKey = categoryKey || fallbackCategory;
      serviceName = serviceName || rest.join("-");
    }
  }
  
  const normalizeCategory = (value: string) =>
    value.toLowerCase().replace(/[\s_]+/g, "");
  
  // Debug logging
  console.log('ServiceDetail Debug:', {
    serviceId,
    categoryKey, 
    serviceName,
    serviceCategories,
    selectedAccount,
    selectedRegion
  });
  
  // Find the service from the store data
  const category = serviceCategories.find(cat => 
    cat.key === categoryKey ||
    normalizeCategory(cat.name) === normalizeCategory(categoryKey)
  );
  const service = category?.services.find(s =>
    s.serviceName === serviceName || s.name.toLowerCase() === serviceName.toLowerCase()
  );
  
  console.log('Found category:', category);
  console.log('Found service:', service);

  const [columns, setColumns] = useState(() => generateInitialColumns());
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [showColManager, setShowColManager] = useState(false);
  const [stateFilter, setStateFilter] = useState("all");
  const [serviceData, setServiceData] = useState<BackendServiceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedRowData, setSelectedRowData] = useState<ServiceResource | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // Ref for column manager to detect clicks outside
  const colManagerRef = useRef<HTMLDivElement>(null);

  // Close column manager when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (colManagerRef.current && !colManagerRef.current.contains(event.target as Node)) {
        setShowColManager(false);
      }
    }

    if (showColManager) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [showColManager]);

  // Ensure required data is loaded
  React.useEffect(() => {
    async function ensureDataLoaded() {
      console.log('ensureDataLoaded called with:', {
        selectedAccount: !!selectedAccount,
        selectedRegion: !!selectedRegion,
        serviceCategoriesLength: serviceCategories.length
      });
      
      try {
        // If no accounts are loaded, load them first
        if (!selectedAccount) {
          console.log('Loading accounts...');
          await loadAccounts();
        }
        // If no regions are loaded and we have an account, load regions
        if (!selectedRegion && selectedAccount) {
          console.log('Loading regions...');
          await loadRegions(selectedAccount.name);
        }
        // If no service categories are loaded and we have account + region, load them
        if (serviceCategories.length === 0 && selectedAccount && selectedRegion) {
          console.log('Loading service categories...');
          await loadServiceCategories(selectedAccount.name, selectedRegion.code);
        }
      } catch (error) {
        console.error('Failed to load required data:', error);
      }
    }

    ensureDataLoaded();
  }, [selectedAccount, selectedRegion, serviceCategories, loadAccounts, loadRegions, loadServiceCategories]);

  // Auto-select first account and region if not set (for direct navigation to service pages)
  React.useEffect(() => {
    async function autoSelectDefaults() {
      try {
        // If we have accounts loaded but no selected account, select the first one
        const store = useAppStore.getState();
        if (store.accounts.length > 0 && !selectedAccount) {
          const firstAccount = store.accounts[0];
          await store.selectAccount(firstAccount);
        }
        
        // If we have regions loaded but no selected region, select the first one
        if (store.regions.length > 0 && !selectedRegion && selectedAccount) {
          const firstRegion = store.regions[0];
          await store.selectRegion(firstRegion);
        }
      } catch (error) {
        console.error('Failed to auto-select defaults:', error);
      }
    }

    autoSelectDefaults();
  }, [selectedAccount, selectedRegion]);

  // Load actual service data
  React.useEffect(() => {
    async function loadServiceData() {
      if (!serviceName || !categoryKey) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        
        // Use the account and region from store if available, otherwise use safe defaults
        const accountName = selectedAccount?.name || '';
        const regionCode = selectedRegion?.code || 'ap-south-1';

        if (!accountName) {
          setServiceData(null);
          return;
        }
        
        // Load actual service data from the data files
        const actualServiceData = await dataService.getServiceDetails(
          accountName,
          regionCode,
          serviceName
        );
        
        setServiceData(actualServiceData);
        
        // Use API-provided column order (matches Excel sheet column order exactly)
        if (actualServiceData.columns && actualServiceData.columns.length > 0) {
          setColumns(buildColumnsFromApiOrder(actualServiceData.columns));
        } else if (actualServiceData.resources && actualServiceData.resources.length > 0) {
          // Fallback: derive order from first resource's key insertion order
          const inferredColumns = Object.keys(actualServiceData.resources[0]).map((key, idx) => ({
            key,
            label: keyToLabel(key),
            visible: idx < DEFAULT_VISIBLE_COUNT,
            sortable: true,
          }));
          setColumns(inferredColumns);
        }
      } catch (error) {
        console.error('Failed to load service data:', error);
      } finally {
        setLoading(false);
      }
    }

    loadServiceData();
  }, [serviceName, categoryKey, selectedAccount, selectedRegion]);

  /** Download all resources as a CSV using current column order */
  const exportToCsv = () => {
    const resources = serviceData?.resources ?? [];
    if (resources.length === 0) return;

    // Use defined columns (all, not just visible) so the export is complete
    const exportCols = columns.length > 0
      ? columns
      : Object.keys(resources[0]).map((k) => ({ key: k, label: k }));

    const escape = (val: unknown): string => {
      const s = val === null || val === undefined ? '' : String(val);
      // If value contains comma, newline or quote — wrap in quotes and escape inner quotes
      if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
      return s;
    };

    const header = exportCols.map((c) => escape(c.label)).join(',');
    const rows = resources.map((row) =>
      exportCols.map((c) => escape(row[c.key])).join(',')
    );

    const csv = [header, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${serviceName || 'export'}_${selectedAccount?.name || 'account'}_${selectedRegion?.code || 'region'}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const visibleCols = columns.filter((c) => c.visible);

  const filtered = useMemo(() => {
    const resources = serviceData?.resources ?? [];
    let data = [...resources];

    if (search) {
      const q = search.toLowerCase();
      data = data.filter((resource) =>
        Object.values(resource).some((v) => String(v).toLowerCase().includes(q))
      );
    }

    if (stateFilter !== "all") {
      const targetState = stateFilter.toLowerCase();
      data = data.filter((resource) => {
        const status = getStringField(resource, "status")?.toLowerCase();
        const state = getStringField(resource, "state")?.toLowerCase();
        return status === targetState || state === targetState;
      });
    }

    if (sortKey && sortDir) {
      data.sort((a, b) => {
        const av = a[sortKey] ?? "";
        const bv = b[sortKey] ?? "";
        const cmp = String(av).localeCompare(String(bv), undefined, { numeric: true });
        return sortDir === "asc" ? cmp : -cmp;
      });
    }

    return data;
  }, [search, sortKey, sortDir, stateFilter, serviceData]);

  // Extract unique status/state values from data for dynamic filters
  const availableStates = useMemo(() => {
    const resources = serviceData?.resources ?? [];
    const states = new Set<string>();

    resources.forEach((item) => {
      const status = getStringField(item, "status");
      if (status) {
        states.add(status.toLowerCase());
      }
      const state = getStringField(item, "state");
      if (state) {
        states.add(state.toLowerCase());
      }
    });

    return Array.from(states).sort();
  }, [serviceData]);

  const totalPages = Math.ceil(filtered.length / pageSize);
  const pageData = filtered.slice(page * pageSize, (page + 1) * pageSize);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : sortDir === "desc" ? null : "asc");
      if (sortDir === "desc") setSortKey(null);
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-muted-foreground">Loading service details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!service && !loading) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-muted-foreground">Service not found.</p>
            <button 
              onClick={() => navigate('/')}
              className="mt-2 text-primary hover:underline"
            >
              Return to dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm">
          <button onClick={() => navigate("/")} className="text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1">
            <ArrowLeft className="w-4 h-4" />
            FinLens
          </button>
          <span className="text-muted-foreground">›</span>
          {selectedAccount && (
            <>
              <span className="text-muted-foreground">{selectedAccount.name}</span>
              <span className="text-muted-foreground">›</span>
            </>
          )}
          <span className="text-foreground font-medium">{serviceName ? formatServiceNameUppercase(serviceName) : 'Unknown Service'}</span>
        </div>

        {/* Service Header */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-4"
        >
          <AwsIcon service={serviceName || ''} size={52} className="rounded-2xl text-primary flex-shrink-0" />
          <div>
            <h1 className="text-xl font-bold">{serviceName ? formatServiceNameUppercase(serviceName) : 'Unknown Service'}</h1>
            <p className="text-sm text-muted-foreground">
              {category?.name || categoryKey} service · {serviceData?.summary?.resource_count || 0} resources
            </p>
          </div>
        </motion.div>

        {/* Action Bar */}
        <div className="flex flex-wrap items-center gap-3 p-3 rounded-lg bg-card border border-border">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0); }}
              placeholder="Search resources..."
              className="w-full pl-9 pr-3 py-2 rounded-lg bg-secondary border border-border text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/50"
            />
          </div>
          <select
            value={stateFilter}
            onChange={(e) => { setStateFilter(e.target.value); setPage(0); }}
            className="px-3 py-2 rounded-lg bg-secondary border border-border text-sm focus:outline-none focus:ring-1 focus:ring-primary/50"
          >
            <option value="all">All States</option>
            {availableStates.map((state) => (
              <option key={state} value={state}>
                {state.charAt(0).toUpperCase() + state.slice(1)}
              </option>
            ))}
          </select>
          <div className="relative" ref={colManagerRef}>
            <button
              onClick={() => setShowColManager(!showColManager)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-secondary border border-border text-sm hover:bg-secondary/80 transition-colors"
            >
              <Columns3 className="w-4 h-4" />
              Columns
            </button>
            {showColManager && (
              <div className="absolute z-50 top-full mt-1 right-0 w-56 rounded-lg border border-border bg-popover p-3 shadow-xl space-y-1">
                {columns.map((col) => (
                  <label key={col.key} className="flex items-center gap-2 text-sm py-1 cursor-pointer hover:bg-secondary rounded px-2">
                    <input
                      type="checkbox"
                      checked={col.visible}
                      onChange={() =>
                        setColumns((cols) =>
                          cols.map((c) => (c.key === col.key ? { ...c, visible: !c.visible } : c))
                        )
                      }
                      className="accent-primary"
                    />
                    {col.label}
                  </label>
                ))}
              </div>
            )}
          </div>
          <button
            onClick={exportToCsv}
            disabled={(serviceData?.resources?.length ?? 0) === 0}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>

        {/* Table */}
        <div className="rounded-lg border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-card border-b border-border">
                  {visibleCols.map((col) => (
                    <th
                      key={col.key}
                      onClick={() => col.sortable && handleSort(col.key)}
                      className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground whitespace-nowrap ${
                        col.sortable ? "cursor-pointer hover:text-foreground select-none" : ""
                      }`}
                    >
                      <div className="flex items-center gap-1">
                        {col.label}
                        {col.sortable && sortKey === col.key && (
                          sortDir === "asc" ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pageData.map((row, index) => {
                  const rowId = getRowId(row, index);
                  const isExpanded = expandedRow === rowId;
                  
                  const handleRowClick = (e: React.MouseEvent) => {
                    // Don't open sidebar if clicking on interactive elements
                    const target = e.target as HTMLElement;
                    if (target.closest('button') || target.closest('a') || target.closest('.data-popover')) {
                      return;
                    }
                    
                    setSelectedRowData(row);
                    setSidebarOpen(true);
                  };
                  
                  return (
                    <motion.tr
                      key={rowId}
                      initial={false}
                      className="border-b border-border hover:bg-secondary/30 transition-colors cursor-pointer"
                      onClick={handleRowClick}
                    >
                      {visibleCols.map((col) => (
                        <td key={col.key} className="px-4 py-3 whitespace-nowrap">
                          <CellValue value={row[col.key]} colKey={col.key} />
                        </td>
                      ))}
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 bg-card border-t border-border">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>{filtered.length} results</span>
              <select
                value={pageSize}
                onChange={(e) => { setPageSize(Number(e.target.value)); setPage(0); }}
                className="px-2 py-1 rounded bg-secondary border border-border text-xs"
              >
                <option value={25}>25 / page</option>
                <option value={50}>50 / page</option>
                <option value={100}>100 / page</option>
              </select>
            </div>
            <div className="flex items-center gap-1">
              <button
                disabled={page === 0}
                onClick={() => setPage(page - 1)}
                className="p-1.5 rounded hover:bg-secondary disabled:opacity-30 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs px-2">
                {page + 1} / {Math.max(totalPages, 1)}
              </span>
              <button
                disabled={page >= totalPages - 1}
                onClick={() => setPage(page + 1)}
                className="p-1.5 rounded hover:bg-secondary disabled:opacity-30 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Detail Sidebar */}
      <DetailSidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        data={selectedRowData}
      />
    </div>
  );
}
