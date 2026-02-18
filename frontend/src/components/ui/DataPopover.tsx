import React, { useState } from "react";
import { createPortal } from "react-dom";
import {
  Tag,
  Copy,
  Check,
  ChevronDown,
  Server,
  Shield,
  Network,
  Database,
  Info,
  Eye,
  ExternalLink
} from "lucide-react";

interface DataPopoverProps {
  data: unknown;
  type: 'tags' | 'vpc_config' | 'security_groups' | 'subnets' | 'array' | 'object' | 'complex';
  trigger?: React.ReactNode;
  title?: string;
  className?: string;
}

type TagItem = { Key: string; Value: string };
type SecurityGroup = { VpcSecurityGroupId: string; Status: string };
type Subnet = { 
  SubnetIdentifier?: string;
  subnet_id?: string;
  SubnetAvailabilityZone?: { Name: string };
  availability_zone?: string;
  SubnetStatus?: string;
  state?: string;
  CidrBlock?: string;
  cidr_block?: string;
  available_ip_address_count?: number;
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

function CopyButton({ text, size = "sm" }: { text: string; size?: "sm" | "xs" }) {
  const [copied, setCopied] = useState(false);
  const iconSize = size === "xs" ? "w-3 h-3" : "w-4 h-4";
  
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      className="p-1 rounded hover:bg-secondary/60 transition-colors"
      title="Copy"
    >
      {copied ? (
        <Check className={`${iconSize} text-success`} />
      ) : (
        <Copy className={`${iconSize} text-muted-foreground`} />
      )}
    </button>
  );
}

function TagsContent({ data }: { data: TagItem[] }) {
  if (!data?.length) return <div className="text-muted-foreground text-sm">No tags</div>;

  // Filter out empty tags
  const validTags = data.filter(tag => tag.Key && tag.Value);
  
  if (!validTags.length) return <div className="text-muted-foreground text-sm">No valid tags</div>;

  return (
    <div className="space-y-2">
      {validTags.map((tag, index) => (
        <div key={index} className="flex justify-between items-start gap-3 p-2 rounded-lg bg-card/50 border border-border/40">
          <div className="flex-1 min-w-0">
            <div className="text-xs text-muted-foreground">{tag.Key}</div>
            <div className="text-sm font-medium break-words">{tag.Value}</div>
          </div>
          <CopyButton text={`${tag.Key}=${tag.Value}`} size="xs" />
        </div>
      ))}
    </div>
  );
}

function VpcConfigContent({ data }: { data: Record<string, unknown> }) {
  const subnetIds = Array.isArray(data.subnet_ids) ? data.subnet_ids.filter(Boolean) as string[] : [];
  const securityGroupIds = Array.isArray(data.security_group_ids) ? data.security_group_ids.filter(Boolean) as string[] : [];
  const vpcId = typeof data.vpc_id === "string" && data.vpc_id ? data.vpc_id : null;

  const hasData = vpcId || subnetIds.length > 0 || securityGroupIds.length > 0;
  
  if (!hasData) return <div className="text-muted-foreground text-sm">No VPC configuration data</div>;

  return (
    <div className="space-y-3">
      {vpcId && (
        <div className="p-2 rounded-lg bg-card/50 border border-border/40">
          <div className="text-xs text-muted-foreground">VPC ID</div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-mono">{vpcId}</span>
            <CopyButton text={vpcId} size="xs" />
          </div>
        </div>
      )}
      
      {subnetIds.length > 0 && (
        <div>
          <div className="text-xs text-muted-foreground mb-2">Subnets ({subnetIds.length})</div>
          <div className="space-y-1">
            {subnetIds.map((subnetId, index) => (
              <div key={index} className="flex items-center gap-2 p-2 rounded-lg bg-card/50 border border-border/40">
                <span className="text-sm font-mono">{subnetId}</span>
                <CopyButton text={subnetId} size="xs" />
              </div>
            ))}
          </div>
        </div>
      )}

      {securityGroupIds.length > 0 && (
        <div>
          <div className="text-xs text-muted-foreground mb-2">Security Groups ({securityGroupIds.length})</div>
          <div className="space-y-1">
            {securityGroupIds.map((sgId, index) => (
              <div key={index} className="flex items-center gap-2 p-2 rounded-lg bg-card/50 border border-border/40">
                <span className="text-sm font-mono">{sgId}</span>
                <CopyButton text={sgId} size="xs" />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SecurityGroupsContent({ data }: { data: SecurityGroup[] }) {
  if (!data?.length) return <div className="text-muted-foreground text-sm">No security groups</div>;
  
  // Filter out security groups without valid IDs
  const validGroups = data.filter(sg => sg.VpcSecurityGroupId);
  
  if (!validGroups.length) return <div className="text-muted-foreground text-sm">No valid security groups</div>;

  return (
    <div className="space-y-2">
      {validGroups.map((sg, index) => (
        <div key={index} className="flex items-center justify-between gap-3 p-2 rounded-lg bg-card/50 border border-border/40">
          <div className="flex-1 min-w-0">
            <div className="text-sm font-mono">{sg.VpcSecurityGroupId}</div>
            {sg.Status && (
              <div className={`text-xs px-1.5 py-0.5 rounded-full inline-block mt-1 ${
                sg.Status === 'active' ? 'bg-success/15 text-success' : 'bg-warning/15 text-warning'
              }`}>
                {sg.Status}
              </div>
            )}
          </div>
          <CopyButton text={sg.VpcSecurityGroupId} size="xs" />
        </div>
      ))}
    </div>
  );
}

function SubnetsContent({ data }: { data: Subnet[] }) {
  if (!data?.length) return <div className="text-muted-foreground text-sm">No subnets</div>;

  return (
    <div className="space-y-2">
      {data.map((subnet, index) => {
        // Handle both VPC subnet format and RDS subnet format
        const subnetId = subnet.subnet_id || subnet.SubnetIdentifier;
        const cidrBlock = subnet.cidr_block || subnet.CidrBlock;
        const availabilityZone = subnet.availability_zone || subnet.SubnetAvailabilityZone?.Name;
        const status = subnet.state || subnet.SubnetStatus;
        
        return (
          <div key={index} className="p-2 rounded-lg bg-card/50 border border-border/40">
            <div className="flex items-center justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="text-sm font-mono">{subnetId}</div>
                {cidrBlock && (
                  <div className="text-xs text-muted-foreground mt-1">CIDR: {cidrBlock}</div>
                )}
                {availabilityZone && (
                  <div className="text-xs text-muted-foreground">AZ: {availabilityZone}</div>
                )}
                {subnet.available_ip_address_count && (
                  <div className="text-xs text-muted-foreground">Available IPs: {subnet.available_ip_address_count}</div>
                )}
                {status && (
                  <div className={`text-xs px-1.5 py-0.5 rounded-full inline-block mt-1 ${
                    status === 'Active' || status === 'available' ? 'bg-success/15 text-success' : 'bg-warning/15 text-warning'
                  }`}>
                    {status}
                  </div>
                )}
              </div>
              {subnetId && <CopyButton text={subnetId} size="xs" />}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ArrayContent({ data }: { data: unknown[] }) {
  if (!data?.length) return <div className="text-muted-foreground text-sm">Empty array</div>;
  
  // Filter out null, undefined, and empty string items
  const validItems = data.filter(item => {
    if (item === null || item === undefined || item === "") return false;
    if (typeof item === "string" && item.trim() === "") return false;
    return true;
  });
  
  if (!validItems.length) return <div className="text-muted-foreground text-sm">No valid items</div>;

  return (
    <div className="space-y-2">
      {validItems.map((item, index) => (
        <div key={index} className="p-2 rounded-lg bg-card/50 border border-border/40">
          <div className="text-xs text-muted-foreground">Item {index + 1}</div>
          <div className="text-sm break-words">
            {typeof item === "string" ? (
              <div className="flex items-center gap-2">
                <span className="font-mono">{item}</span>
                <CopyButton text={item} size="xs" />
              </div>
            ) : isRecord(item) ? (
              <div className="space-y-1 mt-1">
                {Object.entries(item)
                  .filter(([, value]) => value !== null && value !== undefined && value !== "")
                  .slice(0, 3)
                  .map(([key, value]) => (
                    <div key={key} className="text-xs">
                      <span className="text-muted-foreground">{key}:</span> {String(value)}
                    </div>
                  ))}
                {Object.keys(item).length > 3 && (
                  <div className="text-xs text-muted-foreground">... and {Object.keys(item).length - 3} more</div>
                )}
              </div>
            ) : (
              String(item)
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function ObjectContent({ data }: { data: Record<string, unknown> }) {
  // Filter out empty, null, undefined values and empty arrays/objects
  const validEntries = Object.entries(data).filter(([key, value]) => {
    if (value === null || value === undefined || value === "") return false;
    if (Array.isArray(value) && value.length === 0) return false;
    if (typeof value === "object" && value !== null && Object.keys(value).length === 0) return false;
    return true;
  });
  
  if (validEntries.length === 0) return <div className="text-muted-foreground text-sm">No data to display</div>;

  return (
    <div className="space-y-2">
      {validEntries.map(([key, value]) => (
        <div key={key} className="p-2 rounded-lg bg-card/50 border border-border/40">
          <div className="text-xs text-muted-foreground">{key}</div>
          <div className="text-sm break-words">
            {typeof value === "string" && value.length > 0 ? (
              <div className="flex items-center gap-2">
                <span className={key.includes("id") || key.includes("arn") ? "font-mono" : ""}>{value}</span>
                {(key.includes("id") || key.includes("arn") || key.includes("url")) && (
                  <CopyButton text={value} size="xs" />
                )}
              </div>
            ) : Array.isArray(value) ? (
              <span className="text-muted-foreground">Array ({value.length} items)</span>
            ) : isRecord(value) ? (
              <span className="text-muted-foreground">Object ({Object.keys(value).length} keys)</span>
            ) : (
              String(value)
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

const typeIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  tags: Tag,
  vpc_config: Network,
  security_groups: Shield,
  subnets: Database,
  array: Server,
  object: Info,
  complex: Info,
};

const defaultTriggers: Record<string, (count: number) => string> = {
  tags: (count) => `${count} tags`,
  vpc_config: () => "VPC Config",
  security_groups: (count) => `${count} groups`,
  subnets: (count) => `${count} subnets`,
  array: (count) => `${count} items`,
  object: (count) => `${count} keys`,
  complex: () => "View details",
};

export function DataPopover({ data, type, trigger, title, className = "" }: DataPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [buttonRef, setButtonRef] = useState<HTMLElement | null>(null);
  
  // Process data based on type
  let processedData: unknown = data;
  let count = 0;

  if (type === 'tags') {
    // Convert tags to array format
    if (Array.isArray(data)) {
      processedData = data
        .map((item) => {
          if (isRecord(item) && typeof item.Key === "string" && typeof item.Value === "string") {
            return { Key: item.Key, Value: item.Value };
          }
          return null;
        })
        .filter((item): item is TagItem => item !== null);
    } else if (isRecord(data)) {
      processedData = Object.entries(data)
        .filter(([, value]) => typeof value === "string")
        .map(([key, value]) => ({ Key: key, Value: value as string }));
    }
    count = Array.isArray(processedData) ? processedData.length : 0;
  } else if (Array.isArray(data)) {
    count = data.length;
  } else if (isRecord(data)) {
    count = Object.keys(data).length;
  }

  const IconComponent = typeIcons[type] || Info;
  
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setButtonRef(e.currentTarget as HTMLElement);
    setIsOpen(!isOpen);
  };

  const displayTrigger = trigger || (
    <button
      onClick={handleClick}
      className="flex items-center gap-1 px-2 py-1 rounded-md bg-secondary text-xs hover:bg-secondary/80 transition-colors"
    >
      <IconComponent className="w-3 h-3" />
      {defaultTriggers[type]?.(count) || `${count} items`}
      <ChevronDown className="w-3 h-3" />
    </button>
  );

  if (count === 0 && type !== 'complex') {
    return <span className="text-muted-foreground text-xs">—</span>;
  }

  // Calculate popup position
  const getPopupPosition = () => {
    if (!buttonRef) return { top: 0, left: 0, maxHeight: 240 };
    
    const rect = buttonRef.getBoundingClientRect();
    const popoverWidth = 320;
    const gap = 6;
    const viewportPadding = 16;
    const minPopoverHeight = 180;
    
    // Prefer below the button
    let top = rect.bottom + gap;
    let left = rect.left;
    let maxHeight = Math.floor(window.innerHeight - top - viewportPadding - 2);

    // Root-cause fix:
    // If there isn't enough space below, we were forcing a minimum height, which overflowed viewport.
    // Fallback to opening above the trigger when below space is insufficient.
    if (maxHeight < minPopoverHeight) {
      const topAbove = rect.top - gap;
      const heightAbove = Math.floor(topAbove - viewportPadding - 2);

      if (heightAbove > maxHeight) {
        top = Math.max(viewportPadding, rect.top - gap - Math.min(400, heightAbove));
        maxHeight = Math.min(400, heightAbove);
      } else {
        // Keep below, but strictly clamp to available viewport space (no minimum that can overflow)
        maxHeight = Math.max(0, maxHeight);
      }
    } else {
      maxHeight = Math.min(400, maxHeight);
    }

    const spaceRight = window.innerWidth - rect.left - viewportPadding;
    const spaceLeft = rect.right - viewportPadding;
    
    // Adjust horizontal position
    if (spaceRight < popoverWidth) {
      if (spaceLeft >= popoverWidth) {
        left = rect.right - popoverWidth;
      } else {
        left = Math.max(viewportPadding, (window.innerWidth - popoverWidth) / 2);
      }
    }
    
    // Ensure doesn't go off edges
    left = Math.max(viewportPadding, Math.min(left, window.innerWidth - popoverWidth - viewportPadding));
    
    return { top, left, maxHeight };
  };

  const popupPosition = getPopupPosition();

  return (
    <div className={`relative ${className}`} onClick={(e) => e.stopPropagation()}>
      {trigger ? (
        <div onClick={handleClick}>
          {trigger}
        </div>
      ) : (
        displayTrigger
      )}
      
      {isOpen && createPortal(
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-50"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Popover */}
          <div
            className="fixed z-[60] w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-border/60 bg-gradient-to-br from-card/90 to-card/75 backdrop-blur-2xl text-card-foreground shadow-2xl flex flex-col overflow-hidden min-h-0"
            style={{
              top: `${popupPosition.top}px`,
              left: `${popupPosition.left}px`,
              maxHeight: `${popupPosition.maxHeight}px`,
            }}
          >
            {title && (
              <div className="flex items-center gap-2 px-4 py-3 border-b border-border/60 flex-shrink-0">
                <IconComponent className="w-4 h-4 text-primary" />
                <span className="font-medium text-sm">{title}</span>
              </div>
            )}
            
            <div className="overflow-y-auto overflow-x-hidden flex-1 min-h-0 p-4 overscroll-contain">
              {type === 'tags' && <TagsContent data={processedData as TagItem[]} />}
              {type === 'vpc_config' && <VpcConfigContent data={data as Record<string, unknown>} />}
              {type === 'security_groups' && <SecurityGroupsContent data={data as SecurityGroup[]} />}
              {type === 'subnets' && <SubnetsContent data={data as Subnet[]} />}
              {type === 'array' && <ArrayContent data={data as unknown[]} />}
              {(type === 'object' || type === 'complex') && <ObjectContent data={data as Record<string, unknown>} />}
            </div>
          </div>
        </>,
        document.body
      )}
    </div>
  );
}