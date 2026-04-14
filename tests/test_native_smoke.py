from pydave.native import DaveCodec, DaveEncryptorResultCode, DaveDecryptorResultCode, DaveMediaType, load_dave_library


TEST_FRAME = bytes.fromhex('0dc5aedd5bdc3f20be5697e54dd1f437')
LONG_TEST_FRAME = bytes.fromhex(
    '0dc5aedd5bdc3f20be5697e54dd1f437'
    'b896a36f858c6f20bbd69e2a493ca170'
    'c4f0c1b9acd49d324b92afa788d09b12'
    'b29115a2feb3552b60fff983234a6c96'
    '08af3933683efc6b0f5579a9'
)


def test_load_library_and_query_version():
    library = load_dave_library()
    assert library.path.exists()
    assert library.max_supported_protocol_version() >= 1


def test_create_and_destroy_encryptor_and_decryptor():
    library = load_dave_library()

    encryptor = library.create_encryptor()
    assert encryptor
    library.destroy_encryptor(encryptor)

    decryptor = library.create_decryptor()
    assert decryptor
    library.destroy_decryptor(decryptor)


def test_encryptor_passthrough():
    library = load_dave_library()
    with library.new_encryptor() as encryptor:
        assert encryptor.has_key_ratchet() is False
        assert encryptor.is_passthrough_mode() is False

        encryptor.set_passthrough_mode(True)
        encryptor.assign_ssrc_to_codec(0, DaveCodec.OPUS)

        result, output = encryptor.encrypt(DaveMediaType.AUDIO, 0, TEST_FRAME)
        assert result is DaveEncryptorResultCode.SUCCESS
        assert output == TEST_FRAME


def test_decryptor_passthrough():
    library = load_dave_library()
    with library.new_decryptor() as decryptor:
        decryptor.transition_to_passthrough_mode(True)
        result, output = decryptor.decrypt(DaveMediaType.AUDIO, TEST_FRAME)
        assert result is DaveDecryptorResultCode.SUCCESS
        assert output == TEST_FRAME


def test_passthrough_with_separate_buffers():
    library = load_dave_library()

    with library.new_encryptor() as encryptor, library.new_decryptor() as decryptor:
        encryptor.assign_ssrc_to_codec(0, DaveCodec.OPUS)
        encryptor.set_passthrough_mode(True)
        decryptor.transition_to_passthrough_mode(True)

        encrypted_buffer = bytearray(len(LONG_TEST_FRAME) * 2)
        encrypt_result, encrypted = encryptor.encrypt(DaveMediaType.AUDIO, 0, LONG_TEST_FRAME, output=encrypted_buffer)
        assert encrypt_result is DaveEncryptorResultCode.SUCCESS
        assert encrypted == LONG_TEST_FRAME

        decrypted_buffer = bytearray(len(LONG_TEST_FRAME))
        decrypt_result, decrypted = decryptor.decrypt(DaveMediaType.AUDIO, encrypted, output=decrypted_buffer)
        assert decrypt_result is DaveDecryptorResultCode.SUCCESS
        assert decrypted == LONG_TEST_FRAME
