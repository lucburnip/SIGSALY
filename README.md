# SIGSALY
SIGSALY Encrypt &amp; Decrypt Emulator

# SIGSALY Emulator
 
A Python simulation of the SIGSALY secure communication system (1943), adapted for text input. No external dependencies — standard library only.
 
---
 
## What is SIGSALY?
 
SIGSALY (codenamed **Project X**, also known as **Ciphony I** and — by those who used it — the **Green Hornet**, after the buzzing sound it made on the line) was the world's first secure digital voice communication system. Developed jointly by Bell Laboratories and the US Army Signal Corps and deployed from 1943, it allowed Allied leaders to speak with confidence that their conversations could not be intercepted or decoded by the enemy.
 
Before SIGSALY, "scrambled" phone lines used analogue voice inversion — a technique that the Germans had broken and were routinely monitoring. SIGSALY was categorically different. It was the first system to apply **pulse-code modulation** (digitising an analogue signal into discrete numerical values) combined with a **one-time pad** (a provably unbreakable encryption scheme), making it not just difficult to crack but mathematically impossible without the key.
 
### How it worked
 
The system operated at both ends of a transmission — for instance, the Pentagon in Washington and Churchill's Cabinet War Rooms in London:
 
1. **Vocoder** — the speaker's voice was passed through a voice encoder (vocoder) that broke the audio signal into 10 frequency band amplitudes and a pitch channel, sampled 50 times per second. These were quantised to one of **6 discrete levels** (0–5), producing a stream of digits rather than a continuous waveform.
 
2. **Key records** — at the heart of the system's security were matched pairs of 16-inch vinyl lacquer records, each containing a pre-recorded track of pure thermal noise. Every SIGSALY terminal had an identical copy of the same record. These were played in synchronisation at both ends — the sender's terminal and the receiver's — using precision turntables locked together via radio timing signals.
 
3. **Encryption** — each vocoder level was added to the corresponding key value from the record using **modular arithmetic** (mod 6). The result — the ciphertext — bore no meaningful relationship to the original voice data without the key.
 
4. **Transmission** — only the encrypted digit stream was broadcast over radio. An eavesdropper intercepting it would receive a statistically flat sequence of numbers from which no information whatsoever could be extracted.
 
5. **Decryption** — at the receiving end, the identical key record was playing in lock-step. Subtracting the key values (mod 6) perfectly reversed the encryption, recovering the original vocoder data.
 
6. **Voice synthesis** — the recovered band values were fed back through a voice synthesiser, reconstructing the speech for the listener.
 
### Why it was unbreakable
 
SIGSALY's security rested on Claude Shannon's proof (formalised in his 1949 paper *Communication Theory of Secrecy Systems*) that a one-time pad used correctly is **information-theoretically secure** — meaning that even an adversary with unlimited computing power cannot recover the plaintext, because the ciphertext is statistically independent of it. The key records were used only once and then destroyed.
 
Each terminal weighed approximately 50 tons, occupied a room, and required a team of trained operators. Twelve terminals were eventually installed at Allied command locations including Washington, London, Algiers, Brisbane, and on General Eisenhower's command ship. It is credited with enabling frank, unguarded communication between Roosevelt and Churchill throughout the war.
 
Its existence remained classified until 1976.
 
---
 
## This Emulator
 
This program adapts the SIGSALY process for arbitrary text input, preserving the mathematical structure of the original system.
 
| SIGSALY concept | Emulator equivalent |
|---|---|
| Voice signal | Input text string |
| Vocoder (10 frequency bands, levels 0–5) | Base-6 encoding of each character into 6 band values |
| Vinyl key records (thermal noise, quantised) | Seeded pseudo-random number generator (`KeyRecord` class) |
| Encryption: `(vocoder + key) mod 6` | Same modular addition, band by band |
| Synchronised playback | Shared integer seed — both terminals use the same seed |
| Voice synthesis | Reconstruction of character from base-6 band values |
 
The encryption arithmetic is identical to the original. The vocoder encoding is lossless (base-6 is an exact representation of a byte), so decryption is always perfect.
 
---
 
## Usage
 
```
python3 sigsaly.py
```
 
You will be prompted for:
 
- **Plaintext** — the message to transmit (printable ASCII, up to 200 characters). Press Enter to use a default test message.
- **Key seed** — an integer shared between sender and receiver, representing the paired vinyl records. Press Enter to generate one randomly.
 
The program then walks through each stage of the process:
 
1. The plaintext band matrix (vocoder output)
2. The key record strip (one-time pad values)
3. The ciphertext band matrix (encrypted signal)
4. The raw transmission as an eavesdropper would see it
5. The decrypted output at the receiver's terminal
6. A frequency analysis of the intercepted ciphertext, demonstrating its statistical flatness
 
---
 
## Requirements
 
Python 3.10 or later. No third-party packages.
 
---
 
## Further Reading
 
- Steven Budiansky, *Battle of Wits: The Complete Story of Codebreaking in World War II* (2000)
- Claude Shannon, "Communication Theory of Secrecy Systems", *Bell System Technical Journal*, 1949
- Donald Mehl, "SIGSALY — The Start of the Digital Revolution", NSA Center for Cryptologic History
- [National Cryptologic Museum](https://www.nsa.gov/about/cryptologic-heritage/museum/) — a SIGSALY terminal is on permanent display
