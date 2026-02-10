/**
 * L2-10: Search Node with autocomplete.
 *
 * Search by hash prefix or restored name (after key restore).
 */

import { useState, useMemo, useCallback } from "react";
import { useScaffold, useDispatch } from "../context/ScaffoldContext";

export function SearchBar() {
  const { data, keyData } = useScaffold();
  const dispatch = useDispatch();
  const [input, setInput] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Build searchable entries
  const entries = useMemo(() => {
    if (!data) return [];
    return Object.keys(data.nodes).map((id) => {
      const restored = keyData?.nodes?.[id];
      const label = restored
        ? `${restored.part}@${restored.site}`
        : id.slice(0, 12);
      return { id, label };
    });
  }, [data, keyData]);

  // Filter suggestions
  const suggestions = useMemo(() => {
    if (!input || input.length < 2) return [];
    const q = input.toLowerCase();
    return entries
      .filter(
        (e) =>
          e.id.toLowerCase().startsWith(q) ||
          e.label.toLowerCase().includes(q)
      )
      .slice(0, 10);
  }, [input, entries]);

  const handleSelect = useCallback(
    (id: string) => {
      dispatch({ type: "SET_SEARCH", payload: id });
      setInput(
        entries.find((e) => e.id === id)?.label ?? id.slice(0, 12)
      );
      setShowSuggestions(false);
    },
    [dispatch, entries]
  );

  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder="Search nodes..."
        value={input}
        onChange={(e) => {
          setInput(e.target.value);
          setShowSuggestions(true);
          if (!e.target.value) {
            dispatch({ type: "SET_SEARCH", payload: "" });
          }
        }}
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
      />
      {showSuggestions && suggestions.length > 0 && (
        <div className="suggestions">
          {suggestions.map((s) => (
            <div
              key={s.id}
              className="suggestion-item"
              onMouseDown={() => handleSelect(s.id)}
            >
              {s.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
