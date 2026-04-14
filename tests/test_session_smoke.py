from pydave.native import load_dave_library


def test_session_init_and_key_package():
    library = load_dave_library()
    with library.create_session() as session:
        session.init(version=1, group_id=1234567890, self_user_id='1234123412341234')
        assert session.get_protocol_version() == 1

        key_package = session.get_marshalled_key_package()
        assert key_package
        assert isinstance(key_package, bytes)


def test_session_reset_keeps_wrapper_alive():
    library = load_dave_library()
    with library.create_session() as session:
        session.init(version=1, group_id=42, self_user_id='42')
        before = session.get_marshalled_key_package()
        assert before

        session.reset()
        session.init(version=1, group_id=42, self_user_id='42')
        after = session.get_marshalled_key_package()
        assert after


def test_pairwise_fingerprint_without_group_is_empty():
    library = load_dave_library()
    with library.create_session() as session:
        fingerprint = session.get_pairwise_fingerprint(version=1, user_id='1234123412341234')
        assert fingerprint == b''
