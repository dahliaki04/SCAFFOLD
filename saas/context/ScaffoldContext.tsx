/**
 * SCAFFOLD application state management.
 *
 * Central context for all viewer state: data, filters, selections,
 * key restore status.
 */

import {
  createContext,
  useContext,
  useReducer,
  type ReactNode,
  type Dispatch,
} from "react";
import type { ScaffoldJSON, KeyScafData } from "../types";
import { extractStages, extractSites, getMaxDepth } from "../lib/parser";

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
  viewMode: "graph" | "sankey";
  stages: string[];
  sites: string[];
  nodeSizing: boolean;
  page: Page;
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
  | { type: "SET_VIEW"; payload: "graph" | "sankey" }
  | { type: "TOGGLE_NODE_SIZING" }
  | { type: "SET_PAGE"; payload: Page }
  | { type: "RESET" };

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
