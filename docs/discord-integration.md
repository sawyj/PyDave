# Discord Integration

This document describes the current Discord-oriented integration status for PyDAVE.

## Scope

PyDAVE is the reusable wrapper around the native `libdave` API.

Discord voice integration sits one layer above it. That layer is responsible for:
- advertising DAVE support during the voice identify step
- participating in the live MLS voice flow over the Discord voice websocket
- reacting to external sender, key package, welcome, and transition events
- handing encoded media frames to PyDAVE for encryption before RTP transport

## Proven integration path

An experimental integration was validated in a separate bot project (`tetabot`) using PyDAVE as the native engine.

That integration successfully demonstrated:
- DAVE voice negotiation with `max_dave_protocol_version=1`
- receipt and application of the MLS external sender package
- local key package generation and send
- welcome processing for the bot participant
- transition-ready acknowledgement
- outbound audio encryption through `libdave`
- successful anthem playback in a live Discord voice channel

## What PyDAVE provides to a Discord client

The Discord layer can already rely on PyDAVE for:
- local session creation
- external sender application
- marshalled key package generation
- welcome processing
- key-ratchet derivation
- media encryptor/decryptor setup

The most relevant public entry points today are:
- `load_dave_library()`
- `DaveSession`
- `DaveEncryptor`
- `DaveDecryptor`
- `establish_two_party_group(...)`
- `create_audio_media_pair(...)`

## What remains client-specific

The Discord layer still has to own:
- websocket opcode handling
- state synchronization with Discord's voice gateway
- RTP packet construction and transport details
- lifecycle policy for reconnects, speaker changes, and group updates

## Current recommendation

Treat PyDAVE as the cryptographic and MLS foundation.

Build Discord support as a companion layer or package on top rather than folding Discord-specific behavior into the core `pydave` package.
