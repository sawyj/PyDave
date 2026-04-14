from pydave import DaveEncryptorResultCode, DaveMediaType, create_audio_media_pair, establish_two_party_group


def main() -> None:
    group = establish_two_party_group(
        group_id=12345,
        user_a="1001",
        user_b="1002",
    )
    media = create_audio_media_pair(
        group,
        sender_user_id="1001",
        ssrc=1110,
    )

    try:
        opus_frame = b"example-opus-frame"
        encrypt_result, ciphertext = media.encryptor.encrypt(DaveMediaType.AUDIO, media.ssrc, opus_frame)
        if encrypt_result is not DaveEncryptorResultCode.SUCCESS:
            raise RuntimeError(f"Encrypt failed with {encrypt_result.name}")

        decrypt_result, plaintext = media.decryptor.decrypt(DaveMediaType.AUDIO, ciphertext)
        print(f"Encrypted bytes: {len(ciphertext)}")
        print(f"Decrypt result:  {decrypt_result.name}")
        print(f"Round trip ok:   {plaintext == opus_frame}")
    finally:
        media.close()
        group.close()


if __name__ == "__main__":
    main()
