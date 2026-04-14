from __future__ import annotations

from dataclasses import dataclass

from ..native import DaveCodec, DaveDecryptor, DaveEncryptor
from .groups import TwoPartyGroupContext


@dataclass
class TwoPartyAudioMediaContext:
    group: TwoPartyGroupContext
    sender_user_id: str
    receiver_user_id: str
    ssrc: int
    codec: DaveCodec
    encryptor: DaveEncryptor
    decryptor: DaveDecryptor

    def close(self) -> None:
        self.encryptor.close()
        self.decryptor.close()


def create_audio_media_pair(
    group: TwoPartyGroupContext,
    *,
    sender_user_id: str,
    ssrc: int = 0,
    codec: DaveCodec = DaveCodec.OPUS,
) -> TwoPartyAudioMediaContext:
    if sender_user_id == group.user_a:
        sender_session = group.session_a
        receiver_session = group.session_b
        receiver_user_id = group.user_b
    elif sender_user_id == group.user_b:
        sender_session = group.session_b
        receiver_session = group.session_a
        receiver_user_id = group.user_a
    else:
        raise ValueError(f"sender_user_id must be one of the established group members: {group.user_a!r}, {group.user_b!r}")

    encryptor = sender_session._library.new_encryptor()
    decryptor = receiver_session._library.new_decryptor()

    try:
        with sender_session.get_key_ratchet(sender_user_id) as encrypt_ratchet, receiver_session.get_key_ratchet(sender_user_id) as decrypt_ratchet:
            encryptor.assign_ssrc_to_codec(ssrc, codec)
            encryptor.set_passthrough_mode(False)
            encryptor.set_key_ratchet(encrypt_ratchet)
            decryptor.transition_to_passthrough_mode(False)
            decryptor.transition_to_key_ratchet(decrypt_ratchet)

        return TwoPartyAudioMediaContext(
            group=group,
            sender_user_id=sender_user_id,
            receiver_user_id=receiver_user_id,
            ssrc=ssrc,
            codec=codec,
            encryptor=encryptor,
            decryptor=decryptor,
        )
    except Exception:
        encryptor.close()
        decryptor.close()
        raise
