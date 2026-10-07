/**
 * Client-side SHA256 hashing utility for PII
 * Never sends raw CPF/phone to the server
 */

/**
 * Hash a string using SHA256
 * @param value - The string to hash
 * @returns Promise resolving to hex-encoded SHA256 hash (64 characters)
 */
export async function hashString(value: string): Promise<string> {
  // Normalize input: remove whitespace and convert to lowercase for consistent hashing
  const normalized = value.trim().toLowerCase()
  
  // Encode the string as UTF-8
  const encoder = new TextEncoder()
  const data = encoder.encode(normalized)
  
  // Hash using Web Crypto API
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  
  // Convert ArrayBuffer to hex string
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
  
  return hashHex
}

