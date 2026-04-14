from pydave import DaveDecryptorResultCode, DaveEncryptorResultCode, DaveMediaType
from pydave.highlevel import create_audio_media_pair, establish_two_party_group


TEST_FRAME = bytes.fromhex('0dc5aedd5bdc3f20be5697e54dd1f437')


def test_create_audio_media_pair_encrypts_and_decrypts():
    group = establish_two_party_group(
        group_id=1234567890,
        user_a='1234123412341234',
        user_b='5678567856785678',
    )
    try:
        media = create_audio_media_pair(group, sender_user_id=group.user_a)
        try:
            assert media.sender_user_id == group.user_a
            assert media.receiver_user_id == group.user_b

            encrypt_result, encrypted = media.encryptor.encrypt(DaveMediaType.AUDIO, media.ssrc, TEST_FRAME)
            assert encrypt_result is DaveEncryptorResultCode.SUCCESS
            assert encrypted
            assert encrypted != TEST_FRAME

            decrypt_result, decrypted = media.decryptor.decrypt(DaveMediaType.AUDIO, encrypted)
            assert decrypt_result is DaveDecryptorResultCode.SUCCESS
            assert decrypted == TEST_FRAME
        finally:
            media.close()
    finally:
        group.close()
