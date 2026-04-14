# PyDAVE

PyDAVE is an experimental Python wrapper around Discord's official `libdave` implementation.

It provides:
- low-level Python bindings to the `libdave` C API via `ctypes`
- higher-level helpers for common MLS and media workflows
- a proven path for building `libdave` on Windows
- test and smoke coverage for the critical pieces we have implemented so far

## Why this project exists

Discord voice now requires DAVE-capable clients in situations where older voice stacks are rejected. `libdave` is the official native implementation, but Python developers still need:
- a Windows-friendly build path
- Python bindings for the C API
- examples and tests for MLS session setup and media encryption
- a reusable foundation for Discord client integrations

PyDAVE aims to be that foundation.

## Project scope

PyDAVE is split conceptually into two layers:

1. `pydave`
   The reusable Python wrapper around the native `libdave` API.

2. Discord integration layer
   A separate, more opinionated layer that wires DAVE into a Discord voice client.

This repository currently focuses on the first layer while documenting the second as an active integration track.

## Current capabilities

Implemented and verified:
- loading the real `libdave.dll`
- fingerprint helpers in pure Python
- encryptor and decryptor wrappers
- passthrough encrypt/decrypt flow
- session creation and key package generation
- pairwise fingerprint generation from live sessions
- two-party group establishment from Python
- key-ratchet based media encryption/decryption from Python
- high-level helpers for:
  - establishing a two-party group
  - preparing an audio media pair

## Current status

What works well:
- native `libdave` loading from Python
- MLS session and welcome processing
- outbound media encryption via `libdave`
- Windows toolchain and rebuild process

What is still experimental:
- packaging and distribution story
- broader platform coverage beyond the Windows toolchain we used
- Discord-specific integration APIs and client hooks
- ergonomic high-level APIs for larger applications

## Repository layout

- `source/pydave`
  Python package source.
- `source/pydave/highlevel`
  Higher-level workflow helpers on top of the low-level bindings.
- `tests`
  Smoke tests and integration-oriented tests.
- `native_helpers`
  Small native helpers needed for parts of the C API surface.
- `vendor/libdave`
  Vendored upstream Discord `libdave` source.
- `docs`
  Project documentation.
- `build`
  Local build outputs. Not intended as committed source.

## Documentation

- [Project Status](docs/status.md)
- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Windows Build Guide](docs/build/windows.md)
- [Discord Integration Notes](docs/discord-integration.md)

## Examples

- [Fingerprint Helpers](examples/fingerprints.py)
- [Two-Party Media Round Trip](examples/two_party_media.py)

## Development notes

PyDAVE currently uses a hybrid approach:
- pure Python for helper logic where appropriate
- `ctypes` for the native C API surface

This choice keeps iteration speed high while avoiding the complexity of a compiled Python extension during early development.

PyDAVE also exposes a native log-sink hook through `DaveLibrary.configure_log_sink(...)`, which makes it easier for embedding applications to keep `libdave` quiet by default and turn on native tracing only when debugging.

## Not a finished voice client

PyDAVE is not, by itself, a full Discord voice client.

`libdave` gives us the DAVE protocol engine, MLS state handling, key ratchets, and media encryption primitives. A working bot or client still needs voice gateway integration and media transport wiring on top.

## License and upstream

PyDAVE builds on Discord's official `libdave` implementation vendored under `vendor/libdave`.
Please review upstream licensing and notices before publishing or distributing derivative work.

Project-wide licensing for PyDAVE itself should be treated as not finalized until an explicit top-level license is added.
