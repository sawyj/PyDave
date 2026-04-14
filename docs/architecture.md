# Architecture

## Layers

PyDAVE is easiest to understand as a layered system.

### 1. Native library layer
Source of truth:
- `vendor/libdave`

This is Discord's official implementation of the DAVE protocol primitives and MLS/media logic.

### 2. Low-level Python binding layer
Key file:
- `source/pydave/native.py`

Responsibilities:
- load `libdave.dll`
- declare `ctypes` signatures
- wrap opaque handles
- expose sessions, ratchets, encryptors, decryptors, and result handles

### 3. Supporting helper layer
Key files:
- `source/pydave/fingerprints.py`
- `source/pydave/external_sender.py`
- `source/pydave/paths.py`

Responsibilities:
- pure-Python fingerprint utilities
- external sender helper loading
- path and library discovery helpers

### 4. High-level workflow layer
Key directory:
- `source/pydave/highlevel`

Responsibilities:
- group establishment workflows
- media setup workflows
- ergonomic helpers that avoid repeating low-level orchestration in every caller

## Why `ctypes`

PyDAVE intentionally started with `ctypes` instead of a compiled Python extension because:
- the official library already exposes a usable C API
- iteration speed is much higher
- debugging memory and handle issues is easier at first
- it avoids adding another compiled extension toolchain too early

## Ownership model

Important ownership rules in the current wrapper:
- handles created by `libdave` are wrapped in Python objects and explicitly destroyed
- native-owned byte buffers returned by `libdave` are copied into Python `bytes`
- helper-side memory on Windows is freed by the helper DLL, not by the Python CRT

## Discord integration boundary

PyDAVE itself should remain the reusable wrapper.
A Discord-specific integration layer should sit above it rather than redefining the core library.

That keeps the core package useful for:
- experiments
- tests
- alternative integrations
- other Python applications that need DAVE primitives
