from pydave import (
    generate_displayable_code,
    generate_key_fingerprint,
    generate_pairwise_fingerprint,
)


def main() -> None:
    alice_identity_key = b"alice-identity-key"
    bob_identity_key = b"bob-identity-key"

    alice_fingerprint = generate_key_fingerprint(alice_identity_key)
    bob_fingerprint = generate_key_fingerprint(bob_identity_key)
    pairwise = generate_pairwise_fingerprint(alice_fingerprint, bob_fingerprint)
    display_code = generate_displayable_code(pairwise)

    print(f"Alice fingerprint: {alice_fingerprint.hex()}")
    print(f"Bob fingerprint:   {bob_fingerprint.hex()}")
    print(f"Pairwise:          {pairwise.hex()}")
    print(f"Display code:      {display_code}")


if __name__ == "__main__":
    main()
