from __future__ import annotations

import ctypes
import os
from ctypes import POINTER, c_size_t, c_uint8, c_uint32, c_uint64, c_void_p
from pathlib import Path

from .paths import PROJECT_ROOT


class DaveExternalSenderLibrary:
    def __init__(self, dll: ctypes.CDLL, path: Path):
        self.dll = dll
        self.path = path
        self._configure()

    def _configure(self) -> None:
        byte_ptr = POINTER(c_uint8)
        size_ptr = POINTER(c_size_t)

        self.dll.daveExternalSenderCreate.argtypes = [c_uint64]
        self.dll.daveExternalSenderCreate.restype = c_void_p
        self.dll.daveExternalSenderDestroy.argtypes = [c_void_p]
        self.dll.daveExternalSenderDestroy.restype = None
        self.dll.daveExternalSenderGetMarshalledExternalSender.argtypes = [c_void_p, POINTER(byte_ptr), size_ptr]
        self.dll.daveExternalSenderGetMarshalledExternalSender.restype = None
        self.dll.daveExternalSenderProposeAdd.argtypes = [c_void_p, c_uint32, byte_ptr, c_size_t, POINTER(byte_ptr), size_ptr]
        self.dll.daveExternalSenderProposeAdd.restype = None
        self.dll.daveExternalSenderSplitCommitWelcome.argtypes = [c_void_p, byte_ptr, c_size_t, POINTER(byte_ptr), size_ptr, POINTER(byte_ptr), size_ptr]
        self.dll.daveExternalSenderSplitCommitWelcome.restype = None
        self.dll.pydaveExternalSenderFree.argtypes = [c_void_p]
        self.dll.pydaveExternalSenderFree.restype = None

    def create_external_sender(self, group_id: int) -> DaveExternalSender:
        return DaveExternalSender(self, group_id)


class DaveExternalSender:
    def __init__(self, library: DaveExternalSenderLibrary, group_id: int):
        self._library = library
        self.handle = int(library.dll.daveExternalSenderCreate(group_id))
        if not self.handle:
            raise RuntimeError('Failed to create external sender helper')

    def close(self) -> None:
        if self.handle:
            self._library.dll.daveExternalSenderDestroy(c_void_p(self.handle))
            self.handle = 0

    def __enter__(self) -> DaveExternalSender:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def get_marshaled_external_sender(self) -> bytes:
        out_ptr = POINTER(c_uint8)()
        out_len = c_size_t(0)
        self._library.dll.daveExternalSenderGetMarshalledExternalSender(c_void_p(self.handle), ctypes.byref(out_ptr), ctypes.byref(out_len))
        return _take_owned_bytes(self._library, out_ptr, out_len.value)

    def propose_add(self, epoch: int, key_package: bytes | bytearray | memoryview) -> bytes:
        key_package_view = memoryview(key_package).cast('B')
        key_package_array = _readable_array(key_package_view)
        out_ptr = POINTER(c_uint8)()
        out_len = c_size_t(0)
        self._library.dll.daveExternalSenderProposeAdd(c_void_p(self.handle), epoch, key_package_array, len(key_package_view), ctypes.byref(out_ptr), ctypes.byref(out_len))
        return _take_owned_bytes(self._library, out_ptr, out_len.value)

    def split_commit_welcome(self, commit_welcome: bytes | bytearray | memoryview) -> tuple[bytes, bytes]:
        payload_view = memoryview(commit_welcome).cast('B')
        payload_array = _readable_array(payload_view)
        commit_ptr = POINTER(c_uint8)()
        commit_len = c_size_t(0)
        welcome_ptr = POINTER(c_uint8)()
        welcome_len = c_size_t(0)
        self._library.dll.daveExternalSenderSplitCommitWelcome(
            c_void_p(self.handle),
            payload_array,
            len(payload_view),
            ctypes.byref(commit_ptr),
            ctypes.byref(commit_len),
            ctypes.byref(welcome_ptr),
            ctypes.byref(welcome_len),
        )
        return _take_owned_bytes(self._library, commit_ptr, commit_len.value), _take_owned_bytes(self._library, welcome_ptr, welcome_len.value)


def _take_owned_bytes(library: DaveExternalSenderLibrary, ptr: POINTER(c_uint8), length: int) -> bytes:
    if not ptr or length == 0:
        return b''
    data = ctypes.string_at(ptr, length)
    library.dll.pydaveExternalSenderFree(ptr)
    return data


def _readable_array(data: memoryview):
    array_type = c_uint8 * len(data)
    return array_type.from_buffer_copy(data)


def candidate_external_sender_library_paths() -> list[Path]:
    return [
        PROJECT_ROOT / 'build' / 'external_sender' / 'Release' / 'pydave_external_sender.dll',
        PROJECT_ROOT / 'build' / 'external_sender' / 'Debug' / 'pydave_external_sender.dll',
    ]


def load_external_sender_library(path: str | Path | None = None) -> DaveExternalSenderLibrary:
    selected = Path(path) if path is not None else None
    if selected is None:
        for candidate in candidate_external_sender_library_paths():
            if candidate.exists():
                selected = candidate
                break
    if selected is None:
        searched = "\n".join(str(item) for item in candidate_external_sender_library_paths())
        raise FileNotFoundError(f'Could not find pydave_external_sender.dll. Searched:\n{searched}')

    os.add_dll_directory(str((PROJECT_ROOT / 'build' / 'cpp' / 'Release').resolve()))
    os.add_dll_directory(str(selected.parent.resolve()))
    return DaveExternalSenderLibrary(ctypes.CDLL(str(selected)), selected)
