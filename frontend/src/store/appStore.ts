import { create } from "zustand";
import type { AWSAccount, AWSRegion, AWSService, ServiceCategory } from "@/services/types";
import { dataService } from "@/services/dataService";

interface AppState {
  // Data state
  accounts: AWSAccount[];
  regions: AWSRegion[];
  serviceCategories: ServiceCategory[];
  lastScanTimestamp: string | null;
  
  // Selection state
  selectedAccount: AWSAccount | null;
  selectedRegion: AWSRegion | null;
  selectedCategory: ServiceCategory | null;
  
  // UI state
  accountSidebarOpen: boolean;
  regionSidebarOpen: boolean;
  
  // Loading state
  loading: boolean;
  error: string | null;

  // Data actions
  loadAccounts: () => Promise<void>;
  loadRegions: (accountName: string) => Promise<void>;
  loadServiceCategories: (accountName: string, regionCode: string) => Promise<void>;
  
  // Selection actions
  setSelectedAccount: (account: AWSAccount | null) => void;
  setSelectedRegion: (region: AWSRegion | null) => void;
  setSelectedCategory: (category: ServiceCategory | null) => void;
  
  // UI actions
  setAccountSidebarOpen: (open: boolean) => void;
  setRegionSidebarOpen: (open: boolean) => void;

  // Navigation actions
  selectAccount: (account: AWSAccount) => void;
  selectRegion: (region: AWSRegion) => void;
  selectCategory: (category: ServiceCategory) => void;
  backToAccounts: () => void;
  backToRegions: () => void;
  toggleAccountSidebar: () => void;
  toggleRegionSidebar: () => void;
  
  // Utility actions
  clearError: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  accounts: [],
  regions: [],
  serviceCategories: [],
  lastScanTimestamp: null,
  selectedAccount: null,
  selectedRegion: null,
  selectedCategory: null,
  accountSidebarOpen: true,
  regionSidebarOpen: false,
  loading: false,
  error: null,

  // Data loading actions
  loadAccounts: async () => {
    set({ loading: true, error: null });
    try {
      const accounts = await dataService.getAccounts();
      set({ accounts, loading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to load accounts', loading: false });
    }
  },

  loadRegions: async (accountName: string) => {
    set({ loading: true, error: null });
    try {
      const regions = await dataService.getRegions(accountName);
      set({ regions, loading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to load regions', loading: false });
    }
  },

  loadServiceCategories: async (accountName: string, regionCode: string) => {
    console.log('Store loadServiceCategories called with:', { accountName, regionCode });
    set({ loading: true, error: null });
    try {
      const serviceCategories = await dataService.getServiceCategories(accountName, regionCode);
      // Also fetch the last scan timestamp
      const lastScanTimestamp = await dataService.getLastScanTimestamp(accountName, regionCode);
      console.log('Store setting serviceCategories:', serviceCategories);
      console.log('Store setting lastScanTimestamp:', lastScanTimestamp);
      set({ serviceCategories, lastScanTimestamp, loading: false });
      console.log('Store state after setting:', get().serviceCategories);
    } catch (error) {
      console.log('Store loadServiceCategories error:', error);
      set({ error: error instanceof Error ? error.message : 'Failed to load services', loading: false });
    }
  },

  // Direct setters
  setSelectedAccount: (account) => set({ selectedAccount: account }),
  setSelectedRegion: (region) => set({ selectedRegion: region }),
  setSelectedCategory: (category) => set({ selectedCategory: category }),
  setAccountSidebarOpen: (open) => set({ accountSidebarOpen: open }),
  setRegionSidebarOpen: (open) => set({ regionSidebarOpen: open }),

  // Navigation actions
  selectAccount: async (account) => {
    set({
      selectedAccount: account,
      selectedRegion: null,
      selectedCategory: null,
      accountSidebarOpen: false,
      regionSidebarOpen: true,
      regions: [] // Clear previous regions
    });
    // Load regions for selected account
    await get().loadRegions(account.name);
  },

  selectRegion: async (region) => {
    const { selectedAccount } = get();
    if (!selectedAccount) return;
    
    set({
      selectedRegion: region,
      selectedCategory: null,
      regionSidebarOpen: false,
      serviceCategories: [] // Clear previous categories
    });
    // Load service categories for selected account/region
    await get().loadServiceCategories(selectedAccount.name, region.code);
  },

  selectCategory: (category) =>
    set({
      selectedCategory: category,
    }),

  backToAccounts: () =>
    set({
      selectedAccount: null,
      selectedRegion: null,
      selectedCategory: null,
      regions: [],
      serviceCategories: [],
      regionSidebarOpen: false,
      accountSidebarOpen: true,
    }),

  backToRegions: () =>
    set({
      selectedRegion: null,
      selectedCategory: null,
      serviceCategories: [],
      regionSidebarOpen: true,
      accountSidebarOpen: false,
    }),

  toggleAccountSidebar: () =>
    set((s) => ({
      accountSidebarOpen: !s.accountSidebarOpen,
      // Close region sidebar when opening account sidebar
      regionSidebarOpen: !s.accountSidebarOpen ? false : s.regionSidebarOpen,
    })),

  toggleRegionSidebar: () =>
    set((s) => ({
      regionSidebarOpen: !s.regionSidebarOpen,
      // Close account sidebar when opening region sidebar
      accountSidebarOpen: !s.regionSidebarOpen ? false : s.accountSidebarOpen,
    })),

  clearError: () => set({ error: null }),
}));

// Initialize accounts on store creation - temporarily disabled for debugging
// useAppStore.getState().loadAccounts();
