from pydave.highlevel import establish_two_party_group


def test_establish_two_party_group_returns_ready_sessions():
    context = establish_two_party_group(
        group_id=1234567890,
        user_a='1234123412341234',
        user_b='5678567856785678',
    )
    try:
        assert context.recognized_user_ids == ['1234123412341234', '5678567856785678']
        assert context.epoch_authenticator

        fingerprint_a = context.session_a.get_pairwise_fingerprint(version=1, user_id=context.user_b)
        fingerprint_b = context.session_b.get_pairwise_fingerprint(version=1, user_id=context.user_a)
        assert fingerprint_a
        assert fingerprint_a == fingerprint_b
    finally:
        context.session_a.close()
        context.session_b.close()
