/**
 * SCAFFOLD application state management.
 *
 * Central context for all viewer state: data, filters, selections,
 * key restore status, and diff comparison state (L2-19).
 */

import {
  createContext,
  useContext,
  useReducer,
  type ReactNode,
  type Dispatch,
} from "react";
import type { ScaffoldJSON, KeyScafData, DiffResult } from "../types";
import { extractStages, extractSites, getMaxDepth } from "../lib/parser";
import { computeDiff } from "../lib/diff";

export type Page = "landing" | "guide" | "viewer";

interface State {
  data: ScaffoldJSON | null;
  loaded: boolean;
  keyData: KeyScafData | null;
  restored: boolean;
  selectedProduct: string | null;
  selectedSuppliers: Set<string>;
  stageFilters: Set<string>;
  siteFilters: Set<string>;
  depthFilter: number;
  maxDepth: number;
  searchQuery: string;
  viewMode: "graph" | "sankey" | "diff";
  stages: string[];
  sites: string[];
  nodeSizing: boolean;
  page: Page;
  /** L2-19: Baseline data for diff comparison. */
  baselineData: ScaffoldJSON | null;
  /** L2-19: Target data for diff comparison. */
  targetData: ScaffoldJSON | null;
  /** L2-19/L2-21: Computed diff result. */
  diffResult: DiffResult | null;
  /** L2-20: Filter which diff statuses to show. */
  diffStatusFilter: Set<string>;
}

type Action =
  | { type: "LOAD_DATA"; payload: ScaffoldJSON }
  | { type: "RESTORE_KEY"; payload: KeyScafData }
  | { type: "SELECT_PRODUCT"; payload: string | null }
  | { type: "TOGGLE_SUPPLIER"; payload: string }
  | { type: "CLEAR_SUPPLIERS" }
  | { type: "TOGGLE_STAGE"; payload: string }
  | { type: "SET_ALL_STAGES"; payload: boolean }
  | { type: "TOGGLE_SITE"; payload: string }
  | { type: "SET_ALL_SITES"; payload: boolean }
  | { type: "SET_DEPTH"; payload: number }
  | { type: "SET_SEARCH"; payload: string }
  | { type: "SET_VIEW"; payload: "graph" | "sankey" | "diff" }
  | { type: "TOGGLE_NODE_SIZING" }
  | { type: "SET_PAGE"; payload: Page }
  | { type: "LOAD_DIFF"; payload: { baseline: ScaffoldJSON; target: ScaffoldJSON } }
  | { type: "CLEAR_DIFF" }
  | { type: "TOGGLE_DIFF_STATUS"; payload: string }
  | { type: "RESET" };

const ALL_DIFF_STATUSES = new Set(["added", "removed", "modified", "unchanged"]);

const initialState: State = {
  data: null,
  loaded: false,
  keyData: null,
  restored: false,
  selectedProduct: null,
  selectedSuppliers: new Set(),
  stageFilters: new Set(),
  siteFilters: new Set(),
  depthFilter: Infinity,
  maxDepth: 0,
  searchQuery: "",
  viewMode: "graph",
  stages: [],
  sites: [],
  nodeSizing: true,
  page: "landing",
  baselineData: null,
  targetData: null,
  diffResult: null,
  diffStatusFilter: new Set(ALL_DIFF_STATUSES),
};

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "LOAD_DATA": {
      const data = action.payload;
      const stages = extractStages(data);
      const sites = extractSites(data);
      const maxDepth = getMaxDepth(data);
      return {
        ...state,
        data,
        loaded: true,
        stages,
        sites,
        maxDepth,
        stageFilters: new Set(stages), // all checked by default
        siteFilters: new Set(sites),
        depthFilter: maxDepth,
        selectedProduct: null,
        searchQuery: "",
        page: "viewer",
      };
    }
    case "RESTORE_KEY":
      return { ...state, keyData: action.payload, restored: true };
    case "SELECT_PRODUCT":
      return { ...state, selectedProduct: action.payload, selectedSuppliers: new Set() };
    case "TOGGLE_SUPPLIER": {
      const next = new Set(state.selectedSuppliers);
      if (next.has(action.payload)) next.delete(action.payload);
      else next.add(action.payload);
      return { ...state, selectedSuppliers: next, selectedProduct: null };
    }
    case "CLEAR_SUPPLIERS":
      return { ...state, selectedSuppliers: new Set() };
    case "TOGGLE_STAGE": {
      const next = new Set(state.stageFilters);
      if (next.has(action.payload)) next.delete(action.payload);
      else next.add(action.payload);
      return { ...state, stageFilters: next };
    }
    case "SET_ALL_STAGES": {
      return {
        ...state,
        stageFilters: action.payload
          ? new Set(state.stages)
          : new Set(),
      };
    }
    case "TOGGLE_SITE": {
      const next = new Set(state.siteFilters);
      if (next.has(action.payload)) next.delete(action.payload);
      else next.add(action.payload);
      return { ...state, siteFilters: next };
    }
    case "SET_ALL_SITES": {
      return {
        ...state,
        siteFilters: action.payload ? new Set(state.sites) : new Set(),
      };
    }
    case "SET_DEPTH":
      return { ...state, depthFilter: action.payload };
    case "SET_SEARCH":
      return { ...state, searchQuery: action.payload };
    case "SET_VIEW":
      return { ...state, viewMode: action.payload };
    case "TOGGLE_NODE_SIZING":
      return { ...state, nodeSizing: !state.nodeSizing };
    case "SET_PAGE":
      return { ...state, page: action.payload };
    case "LOAD_DIFF": {
      // L2-19: Load two JSONs and compute diff
      const { baseline, target } = action.payload;
      const diffResult = computeDiff(baseline, target);
      // Merge stages/sites from both snapshots for filters
      const bStages = extractStages(baseline);
      const tStages = extractStages(target);
      const allStages = Array.from(new Set([...bStages, ...tStages])).sort();
      const bSites = extractSites(baseline);
      const tSites = extractSites(target);
      const allSites = Array.from(new Set([...bSites, ...tSites])).sort();
      const maxDepth = Math.max(getMaxDepth(baseline), getMaxDepth(target));
      return {
        ...state,
        baselineData: baseline,
        targetData: target,
        diffResult,
        data: target, // use target as the "active" data for other panels
        loaded: true,
        viewMode: "diff",
        stages: allStages,
        sites: allSites,
        maxDepth,
        stageFilters: new Set(allStages),
        siteFilters: new Set(allSites),
        depthFilter: maxDepth,
        diffStatusFilter: new Set(ALL_DIFF_STATUSES),
        selectedProduct: null,
        searchQuery: "",
        page: "viewer",
      };
    }
    case "CLEAR_DIFF":
      return {
        ...state,
        baselineData: null,
        targetData: null,
        diffResult: null,
        diffStatusFilter: new Set(ALL_DIFF_STATUSES),
        viewMode: "graph",
      };
    case "TOGGLE_DIFF_STATUS": {
      const next = new Set(state.diffStatusFilter);
      if (next.has(action.payload)) next.delete(action.payload);
      else next.add(action.payload);
      return { ...state, diffStatusFilter: next };
    }
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

const ScaffoldContext = createContext<State>(initialState);
const DispatchContext = createContext<Dispatch<Action>>(() => {});

export function ScaffoldProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  return (
    <ScaffoldContext.Provider value={state}>
      <DispatchContext.Provider value={dispatch}>
        {children}
      </DispatchContext.Provider>
    </ScaffoldContext.Provider>
  );
}

export function useScaffold() {
  return useContext(ScaffoldContext);
}

export function useDispatch() {
  return useContext(DispatchContext);
}
