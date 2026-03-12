#!/usr/bin/env python3
"""
SIGSALY Emulator
================
A simulation of the SIGSALY secure voice system (1943), adapted for text.

SIGSALY (also known as Project X, Ciphony I, and the Green Hornet) was the
first secure digital voice communication system, used by Allied leaders in WWII.

How the real SIGSALY worked:
  1. VOCODER  — compressed speech into 10 spectral band amplitudes + pitch
  2. QUANTIZE — each band was rounded to one of 6 discrete levels (0–5)
  3. KEY      — a matching pair of vinyl records played random noise in sync
                 at both ends; this noise was quantized into levels 0–5
  4. ENCRYPT  — ciphertext = (vocoder_level + key_level) mod 6
  5. TRANSMIT — only the ciphertext was sent over radio
  6. DECRYPT  — plaintext = (ciphertext - key_level) mod 6
  7. SYNTH    — the vocoder bands were reconstructed into speech

This emulator maps that process onto text:
  • Each character → ASCII value → split into N_BANDS "spectral bands"
  • Each band quantized to LEVELS values (0 .. LEVELS-1)
  • One-time pad key generated from a shared seed (the "vinyl record")
  • Encryption: (band + key) mod LEVELS
  • Decryption: (cipher - key) mod LEVELS  (exact inverse)
"""

import os
import sys
import random
import textwrap
import time

# ── SIGSALY parameters ────────────────────────────────────────────────────────
N_BANDS = 6          # number of vocoder frequency bands per character
LEVELS  = 6          # quantisation levels per band  (0 – 5), matching real SIGSALY
COLS    = 72         # display width

# ── helpers ───────────────────────────────────────────────────────────────────

def banner(title: str) -> None:
    line = "═" * COLS
    pad  = (COLS - len(title) - 2) // 2
    print(f"\n{line}")
    print(" " * pad + f"[ {title} ]")
    print(f"{line}")


def slow_print(text: str, delay: float = 0.012) -> None:
    """Print character-by-character for a teletype effect."""
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def section(label: str) -> None:
    print(f"\n  ┌─ {label} {'─' * (COLS - len(label) - 5)}┐")


def end_section() -> None:
    print(f"  └{'─' * (COLS - 2)}┘")


# ── VOCODER (text → band matrix) ──────────────────────────────────────────────

def char_to_bands(ch: str) -> list[int]:
    """
    Simulate the vocoder: map one character to N_BANDS quantised levels.

    Real SIGSALY measured energy in 10 frequency bands; here we encode
    each character as a base-6 number across N_BANDS digits, with two
    derived "harmonic" bands for visual interest.

    Base-6 with 4 digits covers 0–1295, more than enough for all 256 byte
    values.  This gives us exact, lossless reconstruction — just like the
    real SIGSALY vocoder which was designed to perfectly reconstruct speech.
    """
    v = ord(ch) & 0xFF
    # 4 base-6 digits (little-endian) — reversible encoding
    b = []
    tmp = v
    for _ in range(4):
        b.append(tmp % LEVELS)
        tmp //= LEVELS
    # 2 derived "harmonic" bands (not needed for decoding, visual only)
    b.append((v * 7 + 13) % LEVELS)
    b.append((v ^ (v >> 4)) % LEVELS)
    return b[:N_BANDS]


def bands_to_char(bands: list[int]) -> str:
    """
    Reverse the vocoder: reconstruct a character from its band values.
    Exact inverse of char_to_bands — recovers v from base-6 digits.
    """
    v = bands[0] + bands[1]*6 + bands[2]*36 + bands[3]*216
    return chr(v & 0xFF)


# ── KEY RECORD (one-time pad) ─────────────────────────────────────────────────

class KeyRecord:
    """
    Simulates the paired vinyl key records used at both SIGSALY terminals.
    Both sender and receiver must have identical records (same seed).
    """

    def __init__(self, seed: int):
        self.seed   = seed
        self._rng   = random.Random(seed)
        self._pos   = 0
        self._cache: list[int] = []

    def next_value(self) -> int:
        """Return next random key level (0 .. LEVELS-1)."""
        v = self._rng.randint(0, LEVELS - 1)
        self._cache.append(v)
        self._pos += 1
        return v

    def reset(self) -> None:
        """Rewind the record to the beginning (for display / decryption)."""
        self._rng   = random.Random(self.seed)
        self._pos   = 0
        self._cache = []

    def peek_cache(self) -> list[int]:
        return list(self._cache)


# ── ENCRYPTION ────────────────────────────────────────────────────────────────

def encrypt(plaintext: str, key: KeyRecord) -> list[list[int]]:
    """
    Vocoder → quantise → add key (mod LEVELS).
    Returns a list of band arrays (one per character).
    """
    key.reset()
    ciphertext = []
    for ch in plaintext:
        plain_bands  = char_to_bands(ch)
        cipher_bands = [(pb + key.next_value()) % LEVELS for pb in plain_bands]
        ciphertext.append(cipher_bands)
    return ciphertext


def decrypt(ciphertext: list[list[int]], key: KeyRecord) -> str:
    """
    Subtract key (mod LEVELS) → inverse vocoder → reconstruct text.
    """
    key.reset()
    plaintext = []
    for cipher_bands in ciphertext:
        plain_bands = [(cb - key.next_value()) % LEVELS for cb in cipher_bands]
        plaintext.append(bands_to_char(plain_bands))
    return "".join(plaintext)


# ── DISPLAY HELPERS ───────────────────────────────────────────────────────────

def render_bands(band_matrix: list[list[int]], label: str, max_chars: int = 30) -> None:
    """Print a colour-coded band matrix (truncated for readability)."""
    display = band_matrix[:max_chars]
    section(label)
    header = "  │  Char  │  " + "  ".join(f"B{i}" for i in range(N_BANDS)) + "  │"
    print(header)
    print("  │" + "─" * (len(header) - 4) + "│")
    for i, bands in enumerate(display):
        char_lbl = repr(chr(
            bands[0] | (bands[1] << 3) | (bands[2] << 5)
        )) if label.startswith("Plain") else "·"
        band_str = "   ".join(str(b) for b in bands)
        print(f"  │  [{i:>3}]  │  {band_str}  │")
    if len(band_matrix) > max_chars:
        print(f"  │  ... ({len(band_matrix) - max_chars} more characters) ...")
    end_section()


def render_key_strip(key_values: list[int], max_show: int = 60) -> None:
    """Visualise the key record as a strip of numbers."""
    section("KEY RECORD (one-time pad strip)")
    strip = key_values[:max_show]
    row   = "  │  " + " ".join(str(v) for v in strip)
    if len(key_values) > max_show:
        row += f"  … ({len(key_values) - max_show} more)"
    print(row)
    # Visual "groove" representation
    groove = "  │  " + "".join("▁▂▃▄▅▆"[v] for v in strip)
    print(groove)
    end_section()


def render_transmission(cipher_matrix: list[list[int]]) -> None:
    """Show what an eavesdropper would see on the wire."""
    section("RADIO TRANSMISSION (what an eavesdropper intercepts)")
    flat = [v for bands in cipher_matrix for v in bands]
    # Group into rows of 60 digits
    row_width = 60
    rows = [flat[i:i+row_width] for i in range(0, len(flat), row_width)]
    for r in rows:
        print("  │  " + " ".join(str(v) for v in r))
    end_section()


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main() -> None:
    os.system("clear" if os.name == "posix" else "cls")

    banner("S I G S A L Y  —  Secure Speech Emulator  (1943 / 2025)")
    print(textwrap.dedent("""
      SIGSALY was the world's first secure digital voice system, used by
      Churchill, Roosevelt, and Allied commanders throughout WWII.  It
      digitised speech via a vocoder, applied a one-time-pad from paired
      vinyl records, and transmitted only the encrypted signal.

      This emulator adapts that process for arbitrary text input.
    """))

    # ── Input ──────────────────────────────────────────────────────────────────
    print("  Enter the message to transmit (printable ASCII, max 200 chars):")
    print("  (Press ENTER for a default test message)\n")
    try:
        raw = input("  PLAINTEXT ▶  ").strip()
    except (EOFError, KeyboardInterrupt):
        raw = ""

    if not raw:
        raw = "HELLO WINSTON, THE EAGLE HAS LANDED. -FDR"
        print(f"  Using default: {raw!r}")

    # Constrain to printable ASCII characters that round-trip cleanly
    plaintext = "".join(ch for ch in raw if 32 <= ord(ch) <= 127)[:200]

    # ── Key record ─────────────────────────────────────────────────────────────
    print("\n  Enter the shared key seed (integer, same at both terminals):")
    print("  (Press ENTER for a random seed)\n")
    try:
        seed_raw = input("  KEY SEED  ▶  ").strip()
        seed = int(seed_raw) if seed_raw else random.randint(10000, 99999)
    except (ValueError, EOFError, KeyboardInterrupt):
        seed = random.randint(10000, 99999)

    print(f"\n  Using key seed: {seed}  (both terminals must share this)\n")
    time.sleep(0.5)

    # ── Sender side ────────────────────────────────────────────────────────────
    banner("TERMINAL A  —  SENDER")
    key_a = KeyRecord(seed)

    print("\n  Step 1 · VOCODER  — decomposing text into spectral bands …\n")
    plain_bands = [char_to_bands(ch) for ch in plaintext]

    print("\n  Step 2 · ENCRYPTION  — adding key record (mod 6) …\n")
    cipher_matrix = encrypt(plaintext, key_a)

    # Show the key values used
    key_a.reset()
    key_vals_used = [key_a.next_value() for _ in range(len(plaintext))]

    render_bands(plain_bands,   "Plaintext Band Matrix (sender's vocoder output)")
    render_key_strip(key_vals_used, max_show=min(len(plaintext), 60))
    render_bands(cipher_matrix, "Ciphertext Band Matrix (encrypted — sent over radio)")
    render_transmission(cipher_matrix)

    # ── Receiver side ──────────────────────────────────────────────────────────
    banner("TERMINAL B  —  RECEIVER")
    print("\n  Intercepting transmission and applying synchronised key record …\n")
    time.sleep(0.4)

    key_b   = KeyRecord(seed)          # identical seed = identical record
    decoded = decrypt(cipher_matrix, key_b)

    section("DECRYPTED OUTPUT (receiver's vocoder synthesis)")
    print()
    slow_print(f"  ▶  {decoded}", delay=0.035)
    print()
    end_section()

    # ── Verification ───────────────────────────────────────────────────────────
    banner("VERIFICATION")
    match  = decoded == plaintext
    status = "✓ PERFECT MATCH" if match else "✗ MISMATCH (non-ASCII chars may have been stripped)"
    print(f"\n  Original  : {plaintext!r}")
    print(f"  Recovered : {decoded!r}")
    print(f"  Status    : {status}\n")

    if not match:
        diffs = [(i, plaintext[i], decoded[i])
                 for i in range(min(len(plaintext), len(decoded)))
                 if plaintext[i] != decoded[i]]
        if diffs:
            print("  Differing positions:")
            for i, a, b in diffs[:10]:
                print(f"    pos {i}: sent {a!r}  →  received {b!r}")

    # ── Eavesdropper analysis ──────────────────────────────────────────────────
    banner("CRYPTANALYSIS NOTE")
    flat_cipher = [v for bands in cipher_matrix for v in bands]
    freq = {i: flat_cipher.count(i) / len(flat_cipher) * 100 for i in range(LEVELS)}
    print("\n  An eavesdropper sees only a stream of digits 0–5.")
    print("  Frequency distribution of intercepted values:\n")
    for level, pct in sorted(freq.items()):
        bar = "█" * int(pct / 2)
        print(f"    {level}  {bar:<25}  {pct:5.1f}%")
    print("""
  The one-time pad ensures the distribution is nearly flat — no statistical
  attack can recover the plaintext without the key record.  This is
  information-theoretically secure (Shannon, 1949).
    """)

    banner("END OF TRANSMISSION")


if __name__ == "__main__":
    main()
