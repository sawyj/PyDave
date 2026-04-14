from __future__ import annotations

import hashlib
import struct


_DISPLAYABLE_MAX_GROUP_SIZE = 8
_PAIRWISE_SALT = bytes([
    0x24, 0xCA, 0xB1, 0x7A, 0x7A, 0xF8, 0xEC, 0x2B,
    0x82, 0xB4, 0x12, 0xB9, 0x2D, 0xAB, 0x19, 0x2E,
])


def generate_displayable_code(data: bytes, desired_length: int, group_size: int) -> str:
    if len(data) < desired_length:
        raise ValueError('len(data) must be greater than or equal to desired_length')
    if desired_length % group_size != 0:
        raise ValueError('desired_length must be a multiple of group_size')
    if group_size > _DISPLAYABLE_MAX_GROUP_SIZE:
        raise ValueError(f'group_size must be less than or equal to {_DISPLAYABLE_MAX_GROUP_SIZE}')

    group_modulus = 10 ** group_size
    result: list[str] = []

    for offset in range(0, desired_length, group_size):
        group = data[offset:offset + group_size]
        group_value = int.from_bytes(group, byteorder='big', signed=False) % group_modulus
        result.append(str(group_value).zfill(group_size))

    return ''.join(result)


def generate_key_fingerprint(version: int, key: bytes, user_id: str) -> bytes:
    if version != 0:
        raise ValueError('unsupported fingerprint format version')
    if not key:
        raise ValueError('zero-length key')
    if not user_id:
        raise ValueError('zero-length user ID')

    user_id_int = int(user_id)
    if user_id_int < 0 or user_id_int >= 2 ** 64:
        raise ValueError('user ID out of range')

    return struct.pack('>H', version) + key + struct.pack('>Q', user_id_int)


def generate_pairwise_fingerprint(version: int, key_a: bytes, user_id_a: str, key_b: bytes, user_id_b: str) -> bytes:
    fingerprints = sorted([
        generate_key_fingerprint(version, key_a, user_id_a),
        generate_key_fingerprint(version, key_b, user_id_b),
    ])
    combined = fingerprints[0] + fingerprints[1]
    return hashlib.scrypt(combined, salt=_PAIRWISE_SALT, n=16384, r=8, p=2, dklen=64)
