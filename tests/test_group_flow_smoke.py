from pydave import (
    DaveCodec,
    DaveDecryptorResultCode,
    DaveEncryptorResultCode,
    DaveMediaType,
    load_dave_library,
    load_external_sender_library,
)


TEST_FRAME = bytes.fromhex('0dc5aedd5bdc3f20be5697e54dd1f437')


def test_two_party_group_flow():
    library = load_dave_library()
    helper = load_external_sender_library()

    group_id = 1234567890
    user_a = '1234123412341234'
    user_b = '5678567856785678'
    recognized = [user_a, user_b]

    with helper.create_external_sender(group_id) as external_sender, library.create_session() as session_a, library.create_session() as session_b:
        marshalled_external_sender = external_sender.get_marshaled_external_sender()
        session_a.set_external_sender(marshalled_external_sender)
        session_b.set_external_sender(marshalled_external_sender)

        session_a.init(version=1, group_id=group_id, self_user_id=user_a)
        session_b.init(version=1, group_id=group_id, self_user_id=user_b)

        key_package_b = session_b.get_marshalled_key_package()
        proposal = external_sender.propose_add(epoch=0, key_package=key_package_b)
        commit_welcome = session_a.process_proposals(proposal, recognized)
        assert commit_welcome

        commit, welcome = external_sender.split_commit_welcome(commit_welcome)
        assert commit
        assert welcome

        with session_a.process_commit(commit) as commit_result:
            assert commit_result.is_failed() is False
            assert commit_result.is_ignored() is False
            assert len(commit_result.get_roster_member_ids()) == 2

        with session_b.process_welcome(welcome, recognized) as welcome_result:
            assert welcome_result is not None
            assert len(welcome_result.get_roster_member_ids()) == 2

        auth_a = session_a.get_last_epoch_authenticator()
        auth_b = session_b.get_last_epoch_authenticator()
        assert auth_a
        assert auth_b
        assert auth_a == auth_b


def test_two_party_group_can_encrypt_and_decrypt():
    library = load_dave_library()
    helper = load_external_sender_library()

    group_id = 1234567890
    user_a = '1234123412341234'
    user_b = '5678567856785678'
    recognized = [user_a, user_b]

    with helper.create_external_sender(group_id) as external_sender, library.create_session() as session_a, library.create_session() as session_b:
        marshalled_external_sender = external_sender.get_marshaled_external_sender()
        session_a.set_external_sender(marshalled_external_sender)
        session_b.set_external_sender(marshalled_external_sender)

        session_a.init(version=1, group_id=group_id, self_user_id=user_a)
        session_b.init(version=1, group_id=group_id, self_user_id=user_b)

        key_package_b = session_b.get_marshalled_key_package()
        proposal = external_sender.propose_add(epoch=0, key_package=key_package_b)
        commit_welcome = session_a.process_proposals(proposal, recognized)
        commit, welcome = external_sender.split_commit_welcome(commit_welcome)

        with session_a.process_commit(commit) as commit_result:
            assert commit_result.is_failed() is False
            assert commit_result.is_ignored() is False

        with session_b.process_welcome(welcome, recognized) as welcome_result:
            assert welcome_result is not None

        with session_a.get_key_ratchet(user_a) as encrypt_ratchet, session_b.get_key_ratchet(user_a) as decrypt_ratchet, library.new_encryptor() as encryptor, library.new_decryptor() as decryptor:
            encryptor.assign_ssrc_to_codec(0, DaveCodec.OPUS)
            encryptor.set_passthrough_mode(False)
            encryptor.set_key_ratchet(encrypt_ratchet)
            decryptor.transition_to_passthrough_mode(False)
            decryptor.transition_to_key_ratchet(decrypt_ratchet)

            assert encryptor.has_key_ratchet() is True
            assert encryptor.is_passthrough_mode() is False

            encrypt_result, encrypted = encryptor.encrypt(DaveMediaType.AUDIO, 0, TEST_FRAME)
            assert encrypt_result is DaveEncryptorResultCode.SUCCESS
            assert encrypted
            assert encrypted != TEST_FRAME

            decrypt_result, decrypted = decryptor.decrypt(DaveMediaType.AUDIO, encrypted)
            assert decrypt_result is DaveDecryptorResultCode.SUCCESS
            assert decrypted == TEST_FRAME

            encryptor_stats = encryptor.get_stats(DaveMediaType.AUDIO)
            assert encryptor_stats.encrypt_success_count == 1
            assert encryptor_stats.encrypt_failure_count == 0
            assert encryptor_stats.encrypt_attempts == 1
            assert encryptor_stats.encrypt_max_attempts == 1
            assert encryptor_stats.encrypt_missing_key_count == 0
            assert encryptor_stats.encrypt_duration > 0

            decryptor_stats = decryptor.get_stats(DaveMediaType.AUDIO)
            assert decryptor_stats.decrypt_success_count == 1
            assert decryptor_stats.decrypt_failure_count == 0
            assert decryptor_stats.decrypt_attempts == 1
            assert decryptor_stats.decrypt_missing_key_count == 0
            assert decryptor_stats.decrypt_invalid_nonce_count == 0
            assert decryptor_stats.decrypt_duration > 0


def test_two_party_group_has_matching_pairwise_fingerprints():
    library = load_dave_library()
    helper = load_external_sender_library()

    group_id = 1234567890
    user_a = '1234123412341234'
    user_b = '5678567856785678'
    recognized = [user_a, user_b]

    with helper.create_external_sender(group_id) as external_sender, library.create_session() as session_a, library.create_session() as session_b:
        marshalled_external_sender = external_sender.get_marshaled_external_sender()
        session_a.set_external_sender(marshalled_external_sender)
        session_b.set_external_sender(marshalled_external_sender)

        session_a.init(version=1, group_id=group_id, self_user_id=user_a)
        session_b.init(version=1, group_id=group_id, self_user_id=user_b)

        key_package_b = session_b.get_marshalled_key_package()
        proposal = external_sender.propose_add(epoch=0, key_package=key_package_b)
        commit_welcome = session_a.process_proposals(proposal, recognized)
        commit, welcome = external_sender.split_commit_welcome(commit_welcome)

        with session_a.process_commit(commit) as commit_result:
            assert commit_result.is_failed() is False
            assert commit_result.is_ignored() is False

        with session_b.process_welcome(welcome, recognized) as welcome_result:
            assert welcome_result is not None

        fingerprint_a = session_a.get_pairwise_fingerprint(version=1, user_id=user_b)
        fingerprint_b = session_b.get_pairwise_fingerprint(version=1, user_id=user_a)
        assert fingerprint_a
        assert fingerprint_b
        assert fingerprint_a == fingerprint_b
