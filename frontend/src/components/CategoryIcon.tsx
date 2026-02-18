import {
  Cpu,
  Database,
  HardDrive,
  Globe,
  Link,
  DollarSign,
  Shield,
  BarChart3,
  Wrench,
  TrendingUp,
  Upload,
  Settings,
  Brain,
  FileText
} from "lucide-react";

// Professional cloud/tech icons for each category
const categoryIcons = {
  compute: Cpu,
  database: Database,
  general: FileText,
  storage: HardDrive,
  networking: Globe,
  integration: Link,
  cost_management: DollarSign,
  security: Shield,
  monitoring: BarChart3,
  devops_tools: Wrench,
  analytics: TrendingUp,
  migration_transfer: Upload,
  management_governance: Settings,
  ai_ml: Brain
};

interface CategoryIconProps {
  category: string;
  size?: number;
  className?: string;
}

export function CategoryIcon({ category, size = 16, className = "" }: CategoryIconProps) {
  const IconComponent = categoryIcons[category as keyof typeof categoryIcons];
  
  if (!IconComponent) {
    // Fallback icon
    return <Settings size={size} className={className} />;
  }
  
  return <IconComponent size={size} className={className} />;
}
