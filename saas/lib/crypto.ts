/**
 * L2-25: Client-side AES Decrypt.
 *
 * Decrypts key.scaf files in the browser using Web Crypto API.
 * key.scaf format: MAGIC(4B) + VERSION(uint16 LE, 2B) + SALT(16B) + Fernet token
 *
 * L2-28: Key Never Uploaded Guarantee — all operations are local.
 * This module makes ZERO network calls.
 */

import pako from "pako";

const MAGIC = new Uint8Array([0x53, 0x43, 0x41, 0x46]); // b'SCAF'
const EXPECTED_VERSION = 3;
const PBKDF2_ITERATIONS = 1_200_000;
const SALT_OFFSET = 6;
const SALT_LENGTH = 16;
const TOKEN_OFFSET = SALT_OFFSET + SALT_LENGTH; // byte 22

export class DecryptError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DecryptError";
  }
}

/**
 * Derive a 32-byte key from password + salt using PBKDF2-HMAC-SHA256.
 * The 32 bytes are split: [16B signing key][16B encryption key] (Fernet spec).
 */
async function deriveKey(
  password: string,
  salt: Uint8Array
): Promise<{ signingKey: Uint8Array; encryptionKey: CryptoKey }> {
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    enc.encode(password),
    "PBKDF2",
    false,
    ["deriveBits"]
  );

  const derivedBits = await crypto.subtle.deriveBits(
    {
      name: "PBKDF2",
      salt,
      iterations: PBKDF2_ITERATIONS,
      hash: "SHA-256",
    },
    keyMaterial,
    256 // 32 bytes
  );

  const derived = new Uint8Array(derivedBits);
  const signingKeyBytes = derived.slice(0, 16);
  const encKeyBytes = derived.slice(16, 32);

  const encryptionKey = await crypto.subtle.importKey(
    "raw",
    encKeyBytes,
    { name: "AES-CBC" },
    false,
    ["decrypt"]
  );

  return { signingKey: signingKeyBytes, encryptionKey };
}

/**
 * Verify HMAC-SHA256 signature of Fernet token.
 */
async function verifyHMAC(
  signingKeyBytes: Uint8Array,
  data: Uint8Array,
  expectedHMAC: Uint8Array
): Promise<boolean> {
  const key = await crypto.subtle.importKey(
    "raw",
    signingKeyBytes,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );

  const signature = await crypto.subtle.sign("HMAC", key, data);
  const computed = new Uint8Array(signature);

  if (computed.length !== expectedHMAC.length) return false;
  let match = true;
  for (let i = 0; i < computed.length; i++) {
    if (computed[i] !== expectedHMAC[i]) match = false;
  }
  return match;
}

/**
 * Decode base64url string to Uint8Array.
 */
function base64urlDecode(str: string): Uint8Array {
  // Fernet uses standard base64 (not URL-safe), but cryptography lib uses base64url
  let b64 = str.replace(/-/g, "+").replace(/_/g, "/");
  while (b64.length % 4 !== 0) b64 += "=";
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

/**
 * Decrypt a key.scaf file buffer and return the contained JSON data.
 *
 * This function runs entirely in the browser — no network calls (L2-28).
 */
export async function decryptKeyScaf(
  buffer: ArrayBuffer,
  password: string
): Promise<unknown> {
  const raw = new Uint8Array(buffer);

  // Verify magic bytes
  for (let i = 0; i < 4; i++) {
    if (raw[i] !== MAGIC[i]) {
      throw new DecryptError("Invalid file: missing SCAF magic bytes");
    }
  }

  // Verify version
  const version = raw[4] | (raw[5] << 8); // uint16 LE
  if (version !== EXPECTED_VERSION) {
    throw new DecryptError(
      `Unsupported version: ${version} (expected ${EXPECTED_VERSION})`
    );
  }

  // Extract salt
  const salt = raw.slice(SALT_OFFSET, SALT_OFFSET + SALT_LENGTH);

  // Extract Fernet token (everything after salt)
  const tokenBytes = raw.slice(TOKEN_OFFSET);
  const tokenStr = new TextDecoder().decode(tokenBytes);

  // Decode Fernet token from base64
  const token = base64urlDecode(tokenStr);

  // Parse Fernet token structure:
  // Version(1B) + Timestamp(8B) + IV(16B) + Ciphertext(variable) + HMAC(32B)
  if (token.length < 57) {
    // 1 + 8 + 16 + 0 + 32 minimum
    throw new DecryptError("Invalid Fernet token: too short");
  }

  const fernetVersion = token[0];
  if (fernetVersion !== 0x80) {
    throw new DecryptError("Invalid Fernet token version");
  }

  const iv = token.slice(9, 25); // bytes 9-24
  const ciphertext = token.slice(25, token.length - 32);
  const hmac = token.slice(token.length - 32);

  // Derive keys from password
  const { signingKey, encryptionKey } = await deriveKey(password, salt);

  // Verify HMAC (over everything except the last 32 bytes)
  const hmacData = token.slice(0, token.length - 32);
  const valid = await verifyHMAC(signingKey, hmacData, hmac);
  if (!valid) {
    throw new DecryptError(
      "Decryption failed: invalid password or corrupted file"
    );
  }

  // Decrypt AES-128-CBC
  const plaintext = await crypto.subtle.decrypt(
    { name: "AES-CBC", iv },
    encryptionKey,
    ciphertext
  );

  // Decompress zlib
  const decompressed = pako.inflate(new Uint8Array(plaintext));

  // Parse JSON
  const text = new TextDecoder().decode(decompressed);
  return JSON.parse(text);
}
