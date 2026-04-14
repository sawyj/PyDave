from __future__ import annotations

from dataclasses import dataclass

from ..external_sender import DaveExternalSenderLibrary, load_external_sender_library
from ..native import DaveLibrary, DaveSession, load_dave_library


@dataclass
class TwoPartyGroupContext:
    group_id: int
    user_a: str
    user_b: str
    session_a: DaveSession
    session_b: DaveSession
    recognized_user_ids: list[str]
    epoch_authenticator: bytes

    def close(self) -> None:
        self.session_a.close()
        self.session_b.close()


def establish_two_party_group(
    *,
    group_id: int,
    user_a: str,
    user_b: str,
    library: DaveLibrary | None = None,
    external_sender_library: DaveExternalSenderLibrary | None = None,
) -> TwoPartyGroupContext:
    owning_library = library is None
    owning_external_sender_library = external_sender_library is None

    library = library or load_dave_library()
    external_sender_library = external_sender_library or load_external_sender_library()
    recognized = [user_a, user_b]

    try:
        external_sender = external_sender_library.create_external_sender(group_id)
        session_a = library.create_session()
        session_b = library.create_session()

        try:
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
                if commit_result.is_failed() or commit_result.is_ignored():
                    raise RuntimeError("Failed to establish two-party group for session A")

            with session_b.process_welcome(welcome, recognized) as welcome_result:
                if welcome_result is None:
                    raise RuntimeError("Failed to establish two-party group for session B")

            auth_a = session_a.get_last_epoch_authenticator()
            auth_b = session_b.get_last_epoch_authenticator()
            if not auth_a or auth_a != auth_b:
                raise RuntimeError("Two-party group establishment produced mismatched authenticators")

            return TwoPartyGroupContext(
                group_id=group_id,
                user_a=user_a,
                user_b=user_b,
                session_a=session_a,
                session_b=session_b,
                recognized_user_ids=recognized,
                epoch_authenticator=auth_a,
            )
        except Exception:
            session_a.close()
            session_b.close()
            raise
        finally:
            external_sender.close()
    finally:
        if owning_library:
            pass
        if owning_external_sender_library:
            pass
