from __future__ import annotations

import ctypes
import logging
import threading
from ctypes import CFUNCTYPE, POINTER, c_bool, c_char_p, c_int, c_size_t, c_uint8, c_uint16, c_uint32, c_uint64, c_void_p
from enum import IntEnum
from pathlib import Path
from typing import Callable

from .paths import PROJECT_ROOT


_LOG = logging.getLogger(__name__)


class DaveCodec(IntEnum):
    UNKNOWN = 0
    OPUS = 1
    VP8 = 2
    VP9 = 3
    H264 = 4
    H265 = 5
    AV1 = 6


class DaveMediaType(IntEnum):
    AUDIO = 0
    VIDEO = 1


class DaveEncryptorResultCode(IntEnum):
    SUCCESS = 0
    ENCRYPTION_FAILURE = 1
    MISSING_KEY_RATCHET = 2
    MISSING_CRYPTOR = 3
    TOO_MANY_ATTEMPTS = 4


class DaveDecryptorResultCode(IntEnum):
    SUCCESS = 0
    DECRYPTION_FAILURE = 1
    MISSING_KEY_RATCHET = 2
    INVALID_NONCE = 3
    MISSING_CRYPTOR = 4


class DaveLoggingSeverity(IntEnum):
    VERBOSE = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    NONE = 4


DAVE_MLS_FAILURE_CALLBACK = CFUNCTYPE(None, c_char_p, c_char_p, c_void_p)
DAVE_PAIRWISE_FINGERPRINT_CALLBACK = CFUNCTYPE(None, POINTER(c_uint8), c_size_t, c_void_p)
DAVE_LOG_SINK_CALLBACK = CFUNCTYPE(None, c_int, c_char_p, c_int, c_char_p)


class _DAVEEncryptorStats(ctypes.Structure):
    _fields_ = [
        ("passthroughCount", c_uint64),
        ("encryptSuccessCount", c_uint64),
        ("encryptFailureCount", c_uint64),
        ("encryptDuration", c_uint64),
        ("encryptAttempts", c_uint64),
        ("encryptMaxAttempts", c_uint64),
        ("encryptMissingKeyCount", c_uint64),
    ]


class _DAVEDecryptorStats(ctypes.Structure):
    _fields_ = [
        ("passthroughCount", c_uint64),
        ("decryptSuccessCount", c_uint64),
        ("decryptFailureCount", c_uint64),
        ("decryptDuration", c_uint64),
        ("decryptAttempts", c_uint64),
        ("decryptMissingKeyCount", c_uint64),
        ("decryptInvalidNonceCount", c_uint64),
    ]


class DaveEncryptorStats:
    def __init__(self, *, passthrough_count: int, encrypt_success_count: int, encrypt_failure_count: int, encrypt_duration: int, encrypt_attempts: int, encrypt_max_attempts: int, encrypt_missing_key_count: int):
        self.passthrough_count = passthrough_count
        self.encrypt_success_count = encrypt_success_count
        self.encrypt_failure_count = encrypt_failure_count
        self.encrypt_duration = encrypt_duration
        self.encrypt_attempts = encrypt_attempts
        self.encrypt_max_attempts = encrypt_max_attempts
        self.encrypt_missing_key_count = encrypt_missing_key_count

    @classmethod
    def from_native(cls, native: _DAVEEncryptorStats) -> "DaveEncryptorStats":
        return cls(
            passthrough_count=int(native.passthroughCount),
            encrypt_success_count=int(native.encryptSuccessCount),
            encrypt_failure_count=int(native.encryptFailureCount),
            encrypt_duration=int(native.encryptDuration),
            encrypt_attempts=int(native.encryptAttempts),
            encrypt_max_attempts=int(native.encryptMaxAttempts),
            encrypt_missing_key_count=int(native.encryptMissingKeyCount),
        )


class DaveDecryptorStats:
    def __init__(self, *, passthrough_count: int, decrypt_success_count: int, decrypt_failure_count: int, decrypt_duration: int, decrypt_attempts: int, decrypt_missing_key_count: int, decrypt_invalid_nonce_count: int):
        self.passthrough_count = passthrough_count
        self.decrypt_success_count = decrypt_success_count
        self.decrypt_failure_count = decrypt_failure_count
        self.decrypt_duration = decrypt_duration
        self.decrypt_attempts = decrypt_attempts
        self.decrypt_missing_key_count = decrypt_missing_key_count
        self.decrypt_invalid_nonce_count = decrypt_invalid_nonce_count

    @classmethod
    def from_native(cls, native: _DAVEDecryptorStats) -> "DaveDecryptorStats":
        return cls(
            passthrough_count=int(native.passthroughCount),
            decrypt_success_count=int(native.decryptSuccessCount),
            decrypt_failure_count=int(native.decryptFailureCount),
            decrypt_duration=int(native.decryptDuration),
            decrypt_attempts=int(native.decryptAttempts),
            decrypt_missing_key_count=int(native.decryptMissingKeyCount),
            decrypt_invalid_nonce_count=int(native.decryptInvalidNonceCount),
        )


class DaveLibrary:
    def __init__(self, dll: ctypes.CDLL, path: Path):
        self.dll = dll
        self.path = path
        self._log_sink_callback = None
        self._configure()

    def _configure(self) -> None:
        byte_ptr = POINTER(c_uint8)
        size_ptr = POINTER(c_size_t)

        self.dll.daveMaxSupportedProtocolVersion.argtypes = []
        self.dll.daveMaxSupportedProtocolVersion.restype = c_uint16
        self.dll.daveSetLogSinkCallback.argtypes = [DAVE_LOG_SINK_CALLBACK]
        self.dll.daveSetLogSinkCallback.restype = None
        self.dll.daveFree.argtypes = [c_void_p]
        self.dll.daveFree.restype = None

        self.dll.daveSessionCreate.argtypes = [c_void_p, c_char_p, DAVE_MLS_FAILURE_CALLBACK, c_void_p]
        self.dll.daveSessionCreate.restype = c_void_p
        self.dll.daveSessionDestroy.argtypes = [c_void_p]
        self.dll.daveSessionDestroy.restype = None
        self.dll.daveSessionInit.argtypes = [c_void_p, c_uint16, c_uint64, c_char_p]
        self.dll.daveSessionInit.restype = None
        self.dll.daveSessionReset.argtypes = [c_void_p]
        self.dll.daveSessionReset.restype = None
        self.dll.daveSessionSetProtocolVersion.argtypes = [c_void_p, c_uint16]
        self.dll.daveSessionSetProtocolVersion.restype = None
        self.dll.daveSessionGetProtocolVersion.argtypes = [c_void_p]
        self.dll.daveSessionGetProtocolVersion.restype = c_uint16
        self.dll.daveSessionGetLastEpochAuthenticator.argtypes = [c_void_p, POINTER(byte_ptr), size_ptr]
        self.dll.daveSessionGetLastEpochAuthenticator.restype = None
        self.dll.daveSessionSetExternalSender.argtypes = [c_void_p, byte_ptr, c_size_t]
        self.dll.daveSessionSetExternalSender.restype = None
        self.dll.daveSessionGetMarshalledKeyPackage.argtypes = [c_void_p, POINTER(byte_ptr), size_ptr]
        self.dll.daveSessionGetMarshalledKeyPackage.restype = None
        self.dll.daveSessionProcessProposals.argtypes = [c_void_p, byte_ptr, c_size_t, POINTER(c_char_p), c_size_t, POINTER(byte_ptr), size_ptr]
        self.dll.daveSessionProcessProposals.restype = None
        self.dll.daveSessionProcessCommit.argtypes = [c_void_p, byte_ptr, c_size_t]
        self.dll.daveSessionProcessCommit.restype = c_void_p
        self.dll.daveSessionProcessWelcome.argtypes = [c_void_p, byte_ptr, c_size_t, POINTER(c_char_p), c_size_t]
        self.dll.daveSessionProcessWelcome.restype = c_void_p
        self.dll.daveSessionGetKeyRatchet.argtypes = [c_void_p, c_char_p]
        self.dll.daveSessionGetKeyRatchet.restype = c_void_p
        self.dll.daveSessionGetPairwiseFingerprint.argtypes = [c_void_p, c_uint16, c_char_p, DAVE_PAIRWISE_FINGERPRINT_CALLBACK, c_void_p]
        self.dll.daveSessionGetPairwiseFingerprint.restype = None
        self.dll.daveCommitResultIsFailed.argtypes = [c_void_p]
        self.dll.daveCommitResultIsFailed.restype = c_bool
        self.dll.daveCommitResultIsIgnored.argtypes = [c_void_p]
        self.dll.daveCommitResultIsIgnored.restype = c_bool
        self.dll.daveCommitResultGetRosterMemberIds.argtypes = [c_void_p, POINTER(POINTER(c_uint64)), size_ptr]
        self.dll.daveCommitResultGetRosterMemberIds.restype = None
        self.dll.daveCommitResultDestroy.argtypes = [c_void_p]
        self.dll.daveCommitResultDestroy.restype = None
        self.dll.daveWelcomeResultGetRosterMemberIds.argtypes = [c_void_p, POINTER(POINTER(c_uint64)), size_ptr]
        self.dll.daveWelcomeResultGetRosterMemberIds.restype = None
        self.dll.daveWelcomeResultDestroy.argtypes = [c_void_p]
        self.dll.daveWelcomeResultDestroy.restype = None
        self.dll.daveKeyRatchetDestroy.argtypes = [c_void_p]
        self.dll.daveKeyRatchetDestroy.restype = None

        self.dll.daveEncryptorCreate.argtypes = []
        self.dll.daveEncryptorCreate.restype = c_void_p
        self.dll.daveEncryptorDestroy.argtypes = [c_void_p]
        self.dll.daveEncryptorDestroy.restype = None
        self.dll.daveEncryptorSetKeyRatchet.argtypes = [c_void_p, c_void_p]
        self.dll.daveEncryptorSetKeyRatchet.restype = None
        self.dll.daveEncryptorSetPassthroughMode.argtypes = [c_void_p, c_bool]
        self.dll.daveEncryptorSetPassthroughMode.restype = None
        self.dll.daveEncryptorHasKeyRatchet.argtypes = [c_void_p]
        self.dll.daveEncryptorHasKeyRatchet.restype = c_bool
        self.dll.daveEncryptorIsPassthroughMode.argtypes = [c_void_p]
        self.dll.daveEncryptorIsPassthroughMode.restype = c_bool
        self.dll.daveEncryptorAssignSsrcToCodec.argtypes = [c_void_p, c_uint32, c_int]
        self.dll.daveEncryptorAssignSsrcToCodec.restype = None
        self.dll.daveEncryptorGetMaxCiphertextByteSize.argtypes = [c_void_p, c_int, c_size_t]
        self.dll.daveEncryptorGetMaxCiphertextByteSize.restype = c_size_t
        self.dll.daveEncryptorEncrypt.argtypes = [
            c_void_p,
            c_int,
            c_uint32,
            byte_ptr,
            c_size_t,
            byte_ptr,
            c_size_t,
            size_ptr,
        ]
        self.dll.daveEncryptorEncrypt.restype = c_int
        self.dll.daveEncryptorGetStats.argtypes = [c_void_p, c_int, POINTER(_DAVEEncryptorStats)]
        self.dll.daveEncryptorGetStats.restype = None

        self.dll.daveDecryptorCreate.argtypes = []
        self.dll.daveDecryptorCreate.restype = c_void_p
        self.dll.daveDecryptorDestroy.argtypes = [c_void_p]
        self.dll.daveDecryptorDestroy.restype = None
        self.dll.daveDecryptorTransitionToKeyRatchet.argtypes = [c_void_p, c_void_p]
        self.dll.daveDecryptorTransitionToKeyRatchet.restype = None
        self.dll.daveDecryptorTransitionToPassthroughMode.argtypes = [c_void_p, c_bool]
        self.dll.daveDecryptorTransitionToPassthroughMode.restype = None
        self.dll.daveDecryptorGetMaxPlaintextByteSize.argtypes = [c_void_p, c_int, c_size_t]
        self.dll.daveDecryptorGetMaxPlaintextByteSize.restype = c_size_t
        self.dll.daveDecryptorDecrypt.argtypes = [
            c_void_p,
            c_int,
            byte_ptr,
            c_size_t,
            byte_ptr,
            c_size_t,
            size_ptr,
        ]
        self.dll.daveDecryptorDecrypt.restype = c_int
        self.dll.daveDecryptorGetStats.argtypes = [c_void_p, c_int, POINTER(_DAVEDecryptorStats)]
        self.dll.daveDecryptorGetStats.restype = None

    def max_supported_protocol_version(self) -> int:
        return int(self.dll.daveMaxSupportedProtocolVersion())

    def configure_log_sink(self, *, enabled: bool) -> None:
        if enabled:
            def _callback(severity: int, file_ptr, line: int, message_ptr) -> None:
                try:
                    parsed_severity = DaveLoggingSeverity(severity)
                except ValueError:
                    parsed_severity = DaveLoggingSeverity.INFO
                level = {
                    DaveLoggingSeverity.VERBOSE: logging.DEBUG,
                    DaveLoggingSeverity.INFO: logging.INFO,
                    DaveLoggingSeverity.WARNING: logging.WARNING,
                    DaveLoggingSeverity.ERROR: logging.ERROR,
                    DaveLoggingSeverity.NONE: logging.DEBUG,
                }[parsed_severity]
                file_name = file_ptr.decode("utf-8", errors="replace") if file_ptr else "<unknown>"
                message = message_ptr.decode("utf-8", errors="replace") if message_ptr else ""
                _LOG.log(level, "libdave [%s:%s] %s", file_name, line, message)

            self._log_sink_callback = DAVE_LOG_SINK_CALLBACK(_callback)
        else:
            def _callback(_severity: int, _file_ptr, _line: int, _message_ptr) -> None:
                return

            self._log_sink_callback = DAVE_LOG_SINK_CALLBACK(_callback)

        self.dll.daveSetLogSinkCallback(self._log_sink_callback)

    def create_session(self, auth_session_id: str | None = None, failure_callback: Callable[[str, str], None] | None = None) -> DaveSession:
        return DaveSession(self, auth_session_id=auth_session_id, failure_callback=failure_callback)

    def create_encryptor(self) -> int:
        return int(self.dll.daveEncryptorCreate())

    def destroy_encryptor(self, handle: int) -> None:
        self.dll.daveEncryptorDestroy(c_void_p(handle))

    def create_decryptor(self) -> int:
        return int(self.dll.daveDecryptorCreate())

    def destroy_decryptor(self, handle: int) -> None:
        self.dll.daveDecryptorDestroy(c_void_p(handle))

    def new_encryptor(self) -> DaveEncryptor:
        return DaveEncryptor(self)

    def new_decryptor(self) -> DaveDecryptor:
        return DaveDecryptor(self)

    def destroy_key_ratchet(self, handle: int) -> None:
        self.dll.daveKeyRatchetDestroy(c_void_p(handle))

    def free(self, pointer: c_void_p) -> None:
        self.dll.daveFree(pointer)


class DaveCommitResult:
    def __init__(self, library: DaveLibrary, handle: int):
        self._library = library
        self.handle = handle

    def close(self) -> None:
        if self.handle:
            self._library.dll.daveCommitResultDestroy(c_void_p(self.handle))
            self.handle = 0

    def __enter__(self) -> DaveCommitResult:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def is_failed(self) -> bool:
        return bool(self._library.dll.daveCommitResultIsFailed(c_void_p(self.handle)))

    def is_ignored(self) -> bool:
        return bool(self._library.dll.daveCommitResultIsIgnored(c_void_p(self.handle)))

    def get_roster_member_ids(self) -> list[int]:
        roster_ptr = POINTER(c_uint64)()
        roster_len = c_size_t(0)
        self._library.dll.daveCommitResultGetRosterMemberIds(c_void_p(self.handle), ctypes.byref(roster_ptr), ctypes.byref(roster_len))
        if not roster_ptr or roster_len.value == 0:
            return []
        values = [int(roster_ptr[index]) for index in range(roster_len.value)]
        self._library.free(roster_ptr)
        return values


class DaveWelcomeResult:
    def __init__(self, library: DaveLibrary, handle: int):
        self._library = library
        self.handle = handle

    def close(self) -> None:
        if self.handle:
            self._library.dll.daveWelcomeResultDestroy(c_void_p(self.handle))
            self.handle = 0

    def __enter__(self) -> DaveWelcomeResult:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def get_roster_member_ids(self) -> list[int]:
        roster_ptr = POINTER(c_uint64)()
        roster_len = c_size_t(0)
        self._library.dll.daveWelcomeResultGetRosterMemberIds(c_void_p(self.handle), ctypes.byref(roster_ptr), ctypes.byref(roster_len))
        if not roster_ptr or roster_len.value == 0:
            return []
        values = [int(roster_ptr[index]) for index in range(roster_len.value)]
        self._library.free(roster_ptr)
        return values


class DaveSession:
    def __init__(self, library: DaveLibrary, auth_session_id: str | None = None, failure_callback: Callable[[str, str], None] | None = None):
        self._library = library
        self._user_failure_callback = failure_callback
        self._failure_events: list[tuple[str, str]] = []
        self._callback = DAVE_MLS_FAILURE_CALLBACK(self._handle_failure)
        auth_session_id_bytes = auth_session_id.encode('utf-8') if auth_session_id is not None else None
        self.handle = int(self._library.dll.daveSessionCreate(None, auth_session_id_bytes, self._callback, None))
        if not self.handle:
            raise RuntimeError('Failed to create DAVE session')

    def _handle_failure(self, source: bytes | None, reason: bytes | None, _user_data) -> None:
        decoded_source = source.decode('utf-8') if source else ''
        decoded_reason = reason.decode('utf-8') if reason else ''
        self._failure_events.append((decoded_source, decoded_reason))
        if self._user_failure_callback is not None:
            self._user_failure_callback(decoded_source, decoded_reason)

    @property
    def failure_events(self) -> list[tuple[str, str]]:
        return list(self._failure_events)

    def close(self) -> None:
        if self.handle:
            self._library.dll.daveSessionDestroy(c_void_p(self.handle))
            self.handle = 0

    def __enter__(self) -> DaveSession:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def init(self, version: int, group_id: int, self_user_id: str) -> None:
        self._library.dll.daveSessionInit(c_void_p(self.handle), version, group_id, self_user_id.encode('utf-8'))

    def reset(self) -> None:
        self._library.dll.daveSessionReset(c_void_p(self.handle))

    def set_protocol_version(self, version: int) -> None:
        self._library.dll.daveSessionSetProtocolVersion(c_void_p(self.handle), version)

    def get_protocol_version(self) -> int:
        return int(self._library.dll.daveSessionGetProtocolVersion(c_void_p(self.handle)))

    def get_last_epoch_authenticator(self) -> bytes:
        out_ptr = POINTER(c_uint8)()
        out_len = c_size_t(0)
        self._library.dll.daveSessionGetLastEpochAuthenticator(c_void_p(self.handle), ctypes.byref(out_ptr), ctypes.byref(out_len))
        return _take_owned_bytes(self._library, out_ptr, out_len.value)

    def set_external_sender(self, data: bytes | bytearray | memoryview) -> None:
        payload = memoryview(data).cast('B')
        payload_array = _readable_array(payload)
        self._library.dll.daveSessionSetExternalSender(c_void_p(self.handle), payload_array, len(payload))

    def get_marshalled_key_package(self) -> bytes:
        out_ptr = POINTER(c_uint8)()
        out_len = c_size_t(0)
        self._library.dll.daveSessionGetMarshalledKeyPackage(c_void_p(self.handle), ctypes.byref(out_ptr), ctypes.byref(out_len))
        return _take_owned_bytes(self._library, out_ptr, out_len.value)

    def process_proposals(self, proposals: bytes | bytearray | memoryview, recognized_user_ids: list[str]) -> bytes:
        proposal_view = memoryview(proposals).cast('B')
        proposal_array = _readable_array(proposal_view)
        recognized_array = (c_char_p * len(recognized_user_ids))(*(item.encode('utf-8') for item in recognized_user_ids))
        out_ptr = POINTER(c_uint8)()
        out_len = c_size_t(0)
        self._library.dll.daveSessionProcessProposals(c_void_p(self.handle), proposal_array, len(proposal_view), recognized_array, len(recognized_user_ids), ctypes.byref(out_ptr), ctypes.byref(out_len))
        return _take_owned_bytes(self._library, out_ptr, out_len.value)

    def process_commit(self, commit: bytes | bytearray | memoryview) -> DaveCommitResult:
        commit_view = memoryview(commit).cast('B')
        commit_array = _readable_array(commit_view)
        raw_handle = self._library.dll.daveSessionProcessCommit(c_void_p(self.handle), commit_array, len(commit_view))
        handle = int(raw_handle) if raw_handle else 0
        return DaveCommitResult(self._library, handle)

    def process_welcome(self, welcome: bytes | bytearray | memoryview, recognized_user_ids: list[str]) -> DaveWelcomeResult | None:
        welcome_view = memoryview(welcome).cast('B')
        welcome_array = _readable_array(welcome_view)
        recognized_array = (c_char_p * len(recognized_user_ids))(*(item.encode('utf-8') for item in recognized_user_ids))
        raw_handle = self._library.dll.daveSessionProcessWelcome(c_void_p(self.handle), welcome_array, len(welcome_view), recognized_array, len(recognized_user_ids))
        handle = int(raw_handle) if raw_handle else 0
        if not handle:
            return None
        return DaveWelcomeResult(self._library, handle)

    def get_key_ratchet(self, user_id: str) -> "DaveKeyRatchet":
        handle = int(self._library.dll.daveSessionGetKeyRatchet(c_void_p(self.handle), user_id.encode('utf-8')))
        if not handle:
            raise RuntimeError(f'Failed to get key ratchet for user {user_id!r}')
        return DaveKeyRatchet(self._library, handle)

    def get_pairwise_fingerprint(self, version: int, user_id: str, timeout_seconds: float = 5.0) -> bytes:
        captured: dict[str, bytes] = {"fingerprint": b""}
        completed = threading.Event()

        def _callback(fingerprint_ptr, length, _user_data) -> None:
            if fingerprint_ptr and length:
                captured["fingerprint"] = ctypes.string_at(fingerprint_ptr, length)
            else:
                captured["fingerprint"] = b""
            completed.set()

        callback = DAVE_PAIRWISE_FINGERPRINT_CALLBACK(_callback)
        self._library.dll.daveSessionGetPairwiseFingerprint(
            c_void_p(self.handle),
            version,
            user_id.encode('utf-8'),
            callback,
            None,
        )
        if not completed.wait(timeout_seconds):
            raise TimeoutError(f'Pairwise fingerprint callback did not complete within {timeout_seconds} seconds')
        return captured["fingerprint"]


class DaveKeyRatchet:
    def __init__(self, library: DaveLibrary, handle: int):
        self._library = library
        self.handle = handle

    def close(self) -> None:
        if self.handle:
            self._library.destroy_key_ratchet(self.handle)
            self.handle = 0

    def __enter__(self) -> "DaveKeyRatchet":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


class DaveEncryptor:
    def __init__(self, library: DaveLibrary):
        self._library = library
        self.handle = library.create_encryptor()
        if not self.handle:
            raise RuntimeError('Failed to create DAVE encryptor')

    def close(self) -> None:
        if self.handle:
            self._library.destroy_encryptor(self.handle)
            self.handle = 0

    def __enter__(self) -> DaveEncryptor:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def set_passthrough_mode(self, enabled: bool) -> None:
        self._library.dll.daveEncryptorSetPassthroughMode(c_void_p(self.handle), enabled)

    def set_key_ratchet(self, key_ratchet: DaveKeyRatchet) -> None:
        self._library.dll.daveEncryptorSetKeyRatchet(c_void_p(self.handle), c_void_p(key_ratchet.handle))

    def has_key_ratchet(self) -> bool:
        return bool(self._library.dll.daveEncryptorHasKeyRatchet(c_void_p(self.handle)))

    def is_passthrough_mode(self) -> bool:
        return bool(self._library.dll.daveEncryptorIsPassthroughMode(c_void_p(self.handle)))

    def assign_ssrc_to_codec(self, ssrc: int, codec: DaveCodec) -> None:
        self._library.dll.daveEncryptorAssignSsrcToCodec(c_void_p(self.handle), ssrc, int(codec))

    def max_ciphertext_size(self, media_type: DaveMediaType, frame_size: int) -> int:
        return int(self._library.dll.daveEncryptorGetMaxCiphertextByteSize(c_void_p(self.handle), int(media_type), frame_size))

    def encrypt(self, media_type: DaveMediaType, ssrc: int, frame: bytes | bytearray | memoryview, output: bytearray | None = None) -> tuple[DaveEncryptorResultCode, bytes]:
        frame_view = memoryview(frame).cast('B')
        capacity = self.max_ciphertext_size(media_type, len(frame_view)) if output is None else len(output)
        buffer = bytearray(capacity) if output is None else output
        bytes_written = c_size_t(0)

        frame_array = _readable_array(frame_view)
        output_array = _writable_array(buffer)
        result = DaveEncryptorResultCode(self._library.dll.daveEncryptorEncrypt(
            c_void_p(self.handle),
            int(media_type),
            ssrc,
            frame_array,
            len(frame_view),
            output_array,
            len(buffer),
            ctypes.byref(bytes_written),
        ))
        return result, bytes(buffer[:bytes_written.value])

    def get_stats(self, media_type: DaveMediaType) -> DaveEncryptorStats:
        native = _DAVEEncryptorStats()
        self._library.dll.daveEncryptorGetStats(c_void_p(self.handle), int(media_type), ctypes.byref(native))
        return DaveEncryptorStats.from_native(native)


class DaveDecryptor:
    def __init__(self, library: DaveLibrary):
        self._library = library
        self.handle = library.create_decryptor()
        if not self.handle:
            raise RuntimeError('Failed to create DAVE decryptor')

    def close(self) -> None:
        if self.handle:
            self._library.destroy_decryptor(self.handle)
            self.handle = 0

    def __enter__(self) -> DaveDecryptor:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def transition_to_passthrough_mode(self, enabled: bool) -> None:
        self._library.dll.daveDecryptorTransitionToPassthroughMode(c_void_p(self.handle), enabled)

    def transition_to_key_ratchet(self, key_ratchet: DaveKeyRatchet) -> None:
        self._library.dll.daveDecryptorTransitionToKeyRatchet(c_void_p(self.handle), c_void_p(key_ratchet.handle))

    def max_plaintext_size(self, media_type: DaveMediaType, encrypted_frame_size: int) -> int:
        return int(self._library.dll.daveDecryptorGetMaxPlaintextByteSize(c_void_p(self.handle), int(media_type), encrypted_frame_size))

    def decrypt(self, media_type: DaveMediaType, encrypted_frame: bytes | bytearray | memoryview, output: bytearray | None = None) -> tuple[DaveDecryptorResultCode, bytes]:
        frame_view = memoryview(encrypted_frame).cast('B')
        capacity = self.max_plaintext_size(media_type, len(frame_view)) if output is None else len(output)
        buffer = bytearray(capacity) if output is None else output
        bytes_written = c_size_t(0)

        input_array = _readable_array(frame_view)
        output_array = _writable_array(buffer)
        result = DaveDecryptorResultCode(self._library.dll.daveDecryptorDecrypt(
            c_void_p(self.handle),
            int(media_type),
            input_array,
            len(frame_view),
            output_array,
            len(buffer),
            ctypes.byref(bytes_written),
        ))
        return result, bytes(buffer[:bytes_written.value])

    def get_stats(self, media_type: DaveMediaType) -> DaveDecryptorStats:
        native = _DAVEDecryptorStats()
        self._library.dll.daveDecryptorGetStats(c_void_p(self.handle), int(media_type), ctypes.byref(native))
        return DaveDecryptorStats.from_native(native)


def _take_owned_bytes(library: DaveLibrary, ptr: POINTER(c_uint8), length: int) -> bytes:
    if not ptr or length == 0:
        if ptr:
            library.free(ptr)
        return b''
    data = ctypes.string_at(ptr, length)
    library.free(ptr)
    return data


def _readable_array(data: memoryview):
    array_type = c_uint8 * len(data)
    return array_type.from_buffer_copy(data)


def _writable_array(data: bytearray):
    array_type = c_uint8 * len(data)
    return array_type.from_buffer(data)


def candidate_library_paths() -> list[Path]:
    return [
        PROJECT_ROOT / 'build' / 'cpp' / 'Debug' / 'libdave.dll',
        PROJECT_ROOT / 'build' / 'cpp' / 'Release' / 'libdave.dll',
        PROJECT_ROOT / 'build' / 'Debug' / 'libdave.dll',
        PROJECT_ROOT / 'build' / 'Release' / 'libdave.dll',
        PROJECT_ROOT / 'build' / 'libdave.dll',
        PROJECT_ROOT / 'vendor' / 'libdave' / 'cpp' / 'build' / 'Debug' / 'libdave.dll',
        PROJECT_ROOT / 'vendor' / 'libdave' / 'cpp' / 'build' / 'Release' / 'libdave.dll',
        PROJECT_ROOT / 'vendor' / 'libdave' / 'cpp' / 'build' / 'libdave.dll',
    ]


def load_dave_library(path: str | Path | None = None) -> DaveLibrary:
    if path is not None:
        selected = Path(path)
        return DaveLibrary(ctypes.CDLL(str(selected)), selected)

    for candidate in candidate_library_paths():
        if candidate.exists():
            return DaveLibrary(ctypes.CDLL(str(candidate)), candidate)

    searched = "\n".join(str(item) for item in candidate_library_paths())
    raise FileNotFoundError(f"Could not find libdave.dll. Searched:\n{searched}")
