/**
 * L2-23: key.scaf Drag & Drop.
 * L2-24: Password Prompt.
 * L2-25: Client-side AES Decrypt.
 * L2-26: Live Label Restore.
 * L2-28: Key Never Uploaded Guarantee.
 *
 * Drop zone + password modal for restoring real labels from key.scaf.
 * All decryption happens client-side — NO network calls.
 */

import { useState, useCallback, useRef } from "react";
import { useScaffold, useDispatch } from "../context/ScaffoldContext";
import { decryptKeyScaf } from "../lib/crypto";
import type { KeyScafData } from "../types";

export function KeyRestore() {
  const { restored } = useScaffold();
  const dispatch = useDispatch();

  const [dragOver, setDragOver] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const fileBufferRef = useRef<ArrayBuffer | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((file: File) => {
    const reader = new FileReader();
    reader.onload = () => {
      fileBufferRef.current = reader.result as ArrayBuffer;
      setShowModal(true);
      setPassword("");
      setError("");
    };
    reader.readAsArrayBuffer(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDecrypt = useCallback(async () => {
    if (!fileBufferRef.current || !password) return;

    setLoading(true);
    setError("");

    try {
      // L2-25: Client-side AES decrypt — no network calls (L2-28)
      const result = await decryptKeyScaf(fileBufferRef.current, password);
      // L2-26: Dispatch to context for live label restore
      dispatch({ type: "RESTORE_KEY", payload: result as KeyScafData });
      setShowModal(false);
      fileBufferRef.current = null;
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Decryption failed — wrong password?"
      );
    } finally {
      setLoading(false);
    }
  }, [password, dispatch]);

  if (restored) {
    return (
      <div className="sidebar-section">
        <h3>Key Status</h3>
        <div className="key-status restored">
          <span>&#10003;</span> Labels restored
        </div>
      </div>
    );
  }

  return (
    <div className="sidebar-section">
      <h3>Restore Labels</h3>
      <div
        className={`key-drop-zone ${dragOver ? "drag-over" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <p>Drop key.scaf here or click to browse</p>
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept=".scaf"
        style={{ display: "none" }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      <div className="key-status masked">
        <span>&#9679;</span> Viewing masked data
      </div>

      {/* L2-24: Password Prompt Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Enter key.scaf Password</h3>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleDecrypt()}
              autoFocus
            />
            {error && <div className="error">{error}</div>}
            <div className="actions">
              <button
                className="btn"
                onClick={() => setShowModal(false)}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleDecrypt}
                disabled={loading || !password}
              >
                {loading ? "Decrypting..." : "Decrypt"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
