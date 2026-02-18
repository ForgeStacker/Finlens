import { motion } from "framer-motion";
import { ChevronRight, ChevronLeft, Cloud, Loader2 } from "lucide-react";
import { useAppStore } from "@/store/appStore";
import type { AWSAccount } from "@/services/types";

const envColors: Record<string, string> = {
  Production: "bg-success/15 text-success",
  Development: "bg-accent/15 text-accent",
  Staging: "bg-warning/15 text-warning",
  Testing: "bg-primary/15 text-primary",
};

function AccountItem({ account }: { account: AWSAccount }) {
  const { selectAccount, selectedAccount, loading } = useAppStore();
  const isSelected = selectedAccount?.id === account.id;

  return (
    <button
      onClick={() => selectAccount(account)}
      disabled={loading}
      className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all duration-200 group text-left disabled:opacity-50 disabled:cursor-not-allowed border ${
        isSelected
          ? "bg-primary/15 border-primary/30 shadow-lg shadow-primary/5"
          : "bg-card/40 border-border/50 hover:bg-card/70 hover:border-border hover:shadow-md"
      }`}
    >
      <div className="w-9 h-9 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
        <Cloud className="w-5 h-5 text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{account.name}</p>
        <p className="text-xs text-muted-foreground">{account.accountId}</p>
        {account.totalServices && (
          <p className="text-xs text-muted-foreground mt-1">
            {account.totalServices} services • {account.totalResources || 0} resources
          </p>
        )}
      </div>
      <div className="flex flex-col items-end gap-1">
        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${envColors[account.environment] || ""}`}>
          {account.environment}
        </span>
        {loading && isSelected ? (
          <Loader2 className="w-4 h-4 text-primary animate-spin" />
        ) : (
          <ChevronRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        )}
      </div>
    </button>
  );
}

export function AccountSidebar() {
  const { accountSidebarOpen, toggleAccountSidebar, selectedAccount, accounts, loading, error } = useAppStore();

  return (
    <div className="h-full flex shrink-0">
      {/* Expanded sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: accountSidebarOpen ? 320 : 0 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="glass-card backdrop-blur-xl border-r border-border overflow-hidden"
      >
        <div className="flex flex-col h-full w-80">
          <div className="flex items-center justify-between p-4 border-b border-border/60 bg-card/30">
            <h2 className="text-sm font-semibold text-foreground">AWS Accounts</h2>
            <button
              onClick={toggleAccountSidebar}
              className="p-1 rounded-lg hover:bg-secondary/60 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          </div>

          {error && (
            <div className="p-4 border-b border-border">
              <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-lg">
                {error}
              </div>
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {loading && accounts.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
                <span className="ml-2 text-sm text-muted-foreground">Loading accounts...</span>
              </div>
            ) : accounts.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Cloud className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No accounts found</p>
              </div>
            ) : (
              accounts.map((account) => (
                <AccountItem key={account.id} account={account} />
              ))
            )}
          </div>

          {selectedAccount && (
            <div className="p-4 border-t border-border">
              <div className="text-xs text-muted-foreground">
                Selected: <span className="font-medium">{selectedAccount.name}</span>
              </div>
            </div>
          )}
        </div>
      </motion.aside>

      {/* Collapsed mini bar */}
      {!accountSidebarOpen && (
        <motion.div
          initial={false}
          animate={{ width: 56 }}
          className="h-full border-r border-border bg-card/30 backdrop-blur-sm flex flex-col items-center py-3"
        >
          <button
            onClick={toggleAccountSidebar}
            className="p-2 rounded-lg hover:bg-secondary/60 transition-colors"
            title="Show accounts"
          >
            <Cloud className="w-5 h-5 text-muted-foreground" />
          </button>
        </motion.div>
      )}
    </div>
  );
}
