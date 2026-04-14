from pydave.fingerprints import generate_displayable_code, generate_key_fingerprint, generate_pairwise_fingerprint


def test_generate_displayable_code_groups_digits():
    data = bytes(range(1, 17))
    result = generate_displayable_code(data, desired_length=8, group_size=4)
    assert result.isdigit()
    assert len(result) == 8


def test_generate_key_fingerprint_contains_version_and_user():
    result = generate_key_fingerprint(0, b'abc', '42')
    assert result[:2] == bytes([0, 0])
    assert result[2:5] == b'abc'
    assert len(result) == 13


def test_generate_pairwise_fingerprint_is_order_independent():
    left = generate_pairwise_fingerprint(0, b'key-a', '1', b'key-b', '2')
    right = generate_pairwise_fingerprint(0, b'key-b', '2', b'key-a', '1')
    assert left == right
    assert len(left) == 64
