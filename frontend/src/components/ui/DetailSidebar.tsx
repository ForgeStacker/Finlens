import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Copy, Check, ExternalLink } from "lucide-react";
import { useState } from "react";
import { DataPopover } from "./DataPopover";
import type { ServiceResource } from "@/services/types";

interface DetailSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  data: ServiceResource | null;
  title?: string;
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
      className="p-1 rounded hover:bg-secondary/60 transition-colors opacity-0 group-hover:opacity-100"
      title="Copy value"
    >
      {copied ? (
        <Check className="w-3 h-3 text-success" />
      ) : (
        <Copy className="w-3 h-3 text-muted-foreground" />
      )}
    </button>
  );
}

function formatKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, l => l.toUpperCase());
}

function formatValue(value: unknown, key: string): React.ReactNode {
  if (value === null || value === undefined) {
    return <span className="text-muted-foreground italic">—</span>;
  }

  if (typeof value === "boolean") {
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
        value ? 'bg-success/15 text-success' : 'bg-destructive/15 text-destructive'
      }`}>
        {value ? "True" : "False"}
      </span>
    );
  }

  if (typeof value === "string") {
    if (value === "") {
      return <span className="text-muted-foreground italic">Empty</span>;
    }
    
    // Handle URLs
    if (value.startsWith("http://") || value.startsWith("https://")) {
      return (
        <div className="flex items-center gap-2">
          <a 
            href={value} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-primary hover:text-primary/80 text-sm break-all"
          >
            {value}
          </a>
          <ExternalLink className="w-3 h-3 text-muted-foreground" />
        </div>
      );
    }
    
    // Handle IDs, ARNs, and other identifiers
    if (key.toLowerCase().includes("id") || key.toLowerCase().includes("arn") || value.startsWith("arn:")) {
      return (
        <span className="font-mono text-sm break-all">
          {value}
        </span>
      );
    }
    
    // Handle dates
    if (value.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/) || value.match(/^\d{4}-\d{2}-\d{2}/)) {
      try {
        const date = new Date(value);
        if (!isNaN(date.getTime())) {
          return (
            <div className="text-sm">
              <div>{date.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground">
                {date.toISOString()}
              </div>
            </div>
          );
        }
      } catch (e) {
        // Fall through to regular string handling
      }
    }
    
    return <span className="text-sm break-words">{value}</span>;
  }

  if (typeof value === "number") {
    return <span className="text-sm font-medium">{value.toLocaleString()}</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-muted-foreground italic">Empty array</span>;
    }
    
    // Special handling for tags
    if (key.toLowerCase().includes("tag")) {
      return <DataPopover data={value} type="tags" title="Tags" />;
    }
    
    // Special handling for subnets
    if (key.toLowerCase().includes("subnet")) {
      return <DataPopover data={value} type="subnets" title="Subnets" />;
    }
    
    // Special handling for security groups
    if (key.toLowerCase().includes("security")) {
      return <DataPopover data={value} type="security_groups" title="Security Groups" />;
    }
    
    return <DataPopover data={value} type="array" title={formatKey(key)} />;
  }

  if (typeof value === "object" && value !== null) {
    const obj = value as Record<string, unknown>;
    if (Object.keys(obj).length === 0) {
      return <span className="text-muted-foreground italic">Empty object</span>;
    }
    
    // Special handling for VPC configs
    if (key.toLowerCase().includes("vpc")) {
      return <DataPopover data={obj} type="vpc_config" title="VPC Configuration" />;
    }
    
    // Special handling for endpoints
    if (key.toLowerCase().includes("endpoint")) {
      return <DataPopover data={obj} type="object" title="Endpoint Details" />;
    }
    
    return <DataPopover data={obj} type="object" title={formatKey(key)} />;
  }

  return <span className="text-sm">{String(value)}</span>;
}

export function DetailSidebar({ isOpen, onClose, data, title }: DetailSidebarProps) {
  if (!data) return null;

  const entries = Object.entries(data).filter(([key, value]) => {
    // Filter out internal React keys and empty values
    if (key.startsWith("__") || key.startsWith("_")) return false;
    if (value === null || value === undefined) return false;
    if (typeof value === "string" && value.trim() === "") return false;
    if (Array.isArray(value) && value.length === 0) return false;
    if (typeof value === "object" && value !== null && Object.keys(value).length === 0) return false;
    return true;
  });

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40"
            onClick={onClose}
          />
          
          {/* Sidebar */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-full w-[600px] bg-gradient-to-br from-card/80 to-card/60 backdrop-blur-2xl text-card-foreground border-l border-border/60 shadow-2xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-border/60 bg-gradient-to-r from-card/60 to-card/40">
              <div className="flex-1 min-w-0">
                <h2 className="text-xl font-bold truncate text-foreground">
                  {data.name || data.resource_name || data.resource_id || "Resource Details"}
                </h2>
                <p className="text-sm text-muted-foreground mt-1">
                  {data.type || data.resource_type || "Detailed Information"}
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-secondary/60 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              <div className="p-6">
                <div className="border border-border rounded-lg overflow-hidden">
                  {entries.map(([key, value], index) => (
                    <div
                      key={key}
                      className={`group flex border-b border-border/60 last:border-b-0 hover:bg-card/60 transition-colors ${
                        index % 2 === 0 ? 'bg-card/30' : 'bg-card/20'
                      }`}
                    >
                      <div className="w-1/3 p-4 border-r border-border/60 bg-card/40">
                        <div className="text-sm font-semibold text-foreground">
                          {formatKey(key)}
                        </div>
                      </div>
                      <div className="flex-1 p-4 flex items-center justify-between gap-2">
                        <div className="flex-1 min-w-0 text-sm text-muted-foreground">
                          {formatValue(value, key)}
                        </div>
                        {(typeof value === "string" && value.length > 0) && (
                          <CopyButton text={String(value)} />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-border/60 bg-gradient-to-r from-card/40 to-card/30">
              <div className="text-sm text-muted-foreground flex items-center justify-between">
                <span>{entries.length} properties displayed</span>
                <span className="text-xs">Click complex data to expand</span>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}