/**
 * Upload zone for drag-dropping upload.json files.
 */

import { useState, useCallback, useRef } from "react";
import { useDispatch } from "../context/ScaffoldContext";
import { parseScaffoldJSON, ParseError } from "../lib/parser";

export function UploadZone() {
  const dispatch = useDispatch();
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      setError("");
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const data = parseScaffoldJSON(reader.result as string);
          dispatch({ type: "LOAD_DATA", payload: data });
        } catch (err) {
          if (err instanceof ParseError) {
            setError(err.message);
          } else {
            setError("Failed to parse file");
          }
        }
      };
      reader.readAsText(file);
    },
    [dispatch]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="upload-zone">
      <div
        className={`drop-area ${dragOver ? "drag-over" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <h2>SCAFFOLD Viewer</h2>
        <p>Drop upload.json here or click to browse</p>
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        style={{ display: "none" }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      {error && (
        <div style={{ color: "var(--danger)", fontSize: 13 }}>{error}</div>
      )}
    </div>
  );
}
