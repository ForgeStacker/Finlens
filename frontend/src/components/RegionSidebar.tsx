import { motion } from "framer-motion";
import { ArrowLeft, X, MapPin, Loader2 } from "lucide-react";
import { useAppStore } from "@/store/appStore";
import { useMemo } from "react";
import type { AWSRegion } from "@/services/types";

function RegionItem({ region }: { region: AWSRegion }) {
  const { selectRegion, selectedRegion, loading } = useAppStore();
  const isSelected = selectedRegion?.code === region.code;

  return (
    <button
      onClick={() => selectRegion(region)}
      disabled={loading}
      className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all duration-200 text-left disabled:opacity-50 disabled:cursor-not-allowed border ${
        isSelected
          ? "bg-primary/15 border-primary/30 shadow-lg shadow-primary/5"
          : "bg-card/40 border-border/50 hover:bg-card/70 hover:border-border hover:shadow-md"
      }`}
    >
      <span className="text-xl shrink-0">{region.flag}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{region.name}</p>
        <p className="text-xs text-muted-foreground font-mono">{region.code}</p>
        <div className="flex gap-3 mt-1">
          <span className="text-[10px] text-muted-foreground">{region.serviceCount} Services</span>
          <span className="text-[10px] text-muted-foreground">{region.resourceCount} Resources</span>
        </div>
      </div>
      <div className="shrink-0">
        {loading && isSelected ? (
          <Loader2 className="w-3 h-3 animate-spin text-primary" />
        ) : (
          region.active && <span className="w-2 h-2 rounded-full bg-success block" />
        )}
      </div>
    </button>
  );
}

export function RegionSidebar() {
  const { 
    regionSidebarOpen, 
    selectedAccount, 
    selectedRegion, 
    backToAccounts, 
    toggleRegionSidebar,
    regions,
    loading,
    error 
  } = useAppStore();

  const grouped = useMemo(() => {
    return regions.reduce<Record<string, AWSRegion[]>>((acc, r) => {
      (acc[r.category] ??= []).push(r);
      return acc;
    }, {});
  }, [regions]);

  return (
    <div className="h-full flex shrink-0">
      {/* Expanded sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: regionSidebarOpen ? 320 : 0 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="glass-card backdrop-blur-xl border-r border-border overflow-hidden"
      >
        <div className="flex flex-col h-full w-80">
          {/* Header */}
          <div className="p-4 border-b border-border/60 bg-card/30 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <button
                  onClick={backToAccounts}
                  className="p-1 rounded-lg hover:bg-secondary/60 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>
                <div>
                  <h2 className="text-sm font-semibold text-foreground">AWS Regions</h2>
                  {selectedAccount && (
                    <p className="text-xs text-muted-foreground">{selectedAccount.name}</p>
                  )}
                </div>
              </div>
              <button
                onClick={toggleRegionSidebar}
                className="p-1 rounded-lg hover:bg-secondary/60 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {error && (
            <div className="p-4 border-b border-border">
              <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-lg">
                {error}
              </div>
            </div>
          )}

          {/* Regions list */}
          <div className="flex-1 overflow-y-auto p-4">
            {loading && regions.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
                <span className="ml-2 text-sm text-muted-foreground">Loading regions...</span>
              </div>
            ) : Object.keys(grouped).length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <MapPin className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No regions available</p>
              </div>
            ) : (
              <div className="space-y-6">
                {Object.entries(grouped).map(([category, categoryRegions]) => (
                  <div key={category}>
                    <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
                      {category}
                    </h3>
                    <div className="space-y-2">
                      {categoryRegions.map((region) => (
                        <RegionItem key={region.code} region={region} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {selectedRegion && (
            <div className="p-4 border-t border-border">
              <div className="text-xs text-muted-foreground">
                Selected: <span className="font-medium">{selectedRegion.name}</span>
              </div>
            </div>
          )}
        </div>
      </motion.aside>

      {/* Collapsed mini sidebar */}
      {!regionSidebarOpen && selectedAccount && (
        <motion.div
          initial={false}
          animate={{ width: 56 }}
          className="h-full border-r border-border bg-card/30 backdrop-blur-sm flex flex-col items-center py-3"
        >
          <button
            onClick={toggleRegionSidebar}
            className="p-2 rounded-lg hover:bg-secondary/60 transition-colors"
            title="Show regions"
          >
            <MapPin className="w-5 h-5 text-muted-foreground" />
          </button>
        </motion.div>
      )}
    </div>
  );
}
