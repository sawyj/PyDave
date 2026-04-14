# Project Status

## Summary

PyDAVE has moved beyond proof-of-concept status for the core native wrapper.

The project has already demonstrated:
- loading `libdave.dll` from Python
- building and operating MLS sessions from Python
- two-party group formation and welcome processing
- pairwise fingerprint generation
- key-ratchet based media encryption/decryption

## Verified milestones

### Native wrapper milestones
- `libdave.dll` builds successfully on Windows
- Python can load the DLL through `ctypes`
- encryptor/decryptor lifecycle works
- passthrough encryption and decryption work
- stats retrieval works

### Session milestones
- sessions can be created and initialized
- key packages can be generated
- external sender handling works
- two-party group establishment works
- welcome processing works
- pairwise fingerprints match across participants

### Media milestones
- key ratchets can be derived from live sessions
- encryptors can be configured from session-derived ratchets
- media frames can be encrypted and decrypted successfully

### High-level API milestones
- two-party group setup helper exists
- audio media pair helper exists

## Experimental areas

The following areas are still active development rather than stable API surface:
- naming and API ergonomics
- module boundaries for Discord-specific integrations
- packaging and release conventions
- cross-platform testing and automation
- richer session orchestration helpers

## Current recommendation

Treat PyDAVE as:
- a strong experimental library foundation
- a useful reference implementation for Python developers
- not yet a finished general-purpose production package

## Near-term priorities

1. Improve docs and examples.
2. Tighten public API shape.
3. Separate core wrapper concerns from Discord integration concerns.
4. Expand test coverage around real-world flows.
