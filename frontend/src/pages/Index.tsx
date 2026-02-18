import { Header } from "@/components/Header";
import { AccountSidebar } from "@/components/AccountSidebar";
import { RegionSidebar } from "@/components/RegionSidebar";
import { MetricCards } from "@/components/MetricCards";
import { ServiceGrid } from "@/components/ServiceGrid";
import { useAppStore } from "@/store/appStore";
import { Loader2, AlertCircle } from "lucide-react";
import { useEffect } from "react";

const Index = () => {
  const { selectedAccount, selectedRegion, loading, error, clearError, loadAccounts } = useAppStore();

  // Load accounts on component mount
  useEffect(() => {
    loadAccounts();
  }, [loadAccounts]);

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <AccountSidebar />
        <RegionSidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Global error display */}
          {error && (
            <div className="glass rounded-xl p-4 border border-destructive/20 bg-destructive/5">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-destructive" />
                <p className="text-destructive font-medium">Error</p>
                <button
                  onClick={clearError}
                  className="ml-auto text-xs text-destructive hover:text-destructive/80"
                >
                  Dismiss
                </button>
              </div>
              <p className="text-sm text-destructive/80 mt-1">{error}</p>
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div className="glass rounded-xl p-6 text-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-2" />
              <p className="text-muted-foreground">Loading...</p>
            </div>
          )}

          {/* Welcome / context banner */}
          {!selectedAccount && !loading && (
            <div className="glass rounded-xl p-6 text-center">
              <p className="text-muted-foreground">Select an AWS account from the sidebar to begin scanning resources.</p>
            </div>
          )}

          {selectedAccount && !selectedRegion && !loading && (
            <div className="glass rounded-xl p-6 text-center">
              <p className="text-muted-foreground">
                Account <span className="text-primary font-medium">{selectedAccount.name}</span> selected. Choose a region to view resources.
              </p>
              {selectedAccount.totalServices && (
                <div className="flex justify-center gap-4 mt-3 text-sm text-muted-foreground">
                  <span>{selectedAccount.totalServices} total services</span>
                  <span>•</span>
                  <span>{selectedAccount.totalResources || 0} total resources</span>
                </div>
              )}
            </div>
          )}

          {selectedRegion && !loading && (
            <>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>FinLens</span>
                <span>›</span>
                <span>{selectedAccount?.name}</span>
                <span>›</span>
                <span className="text-foreground font-medium">{selectedRegion.name}</span>
              </div>

              <MetricCards />
              <ServiceGrid />
            </>
          )}

          {/* Show dashboard preview even without selection */}
          {!selectedRegion && !loading && (
            <div className="space-y-6">
              <div className="glass rounded-xl p-6">
                <h3 className="text-lg font-semibold text-foreground mb-3">FinLens Dashboard Preview</h3>
                <p className="text-muted-foreground mb-4">
                  Get comprehensive insights into your AWS infrastructure across multiple accounts and regions.
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary">70+</div>
                    <div className="text-sm text-muted-foreground">AWS Services</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary">Real-time</div>
                    <div className="text-sm text-muted-foreground">Data Scanning</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary">Multi</div>
                    <div className="text-sm text-muted-foreground">Region Support</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary">JSON</div>
                    <div className="text-sm text-muted-foreground">Data Export</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default Index;
