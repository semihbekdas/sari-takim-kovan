from argon2 import PasswordHasher

from kovan.infrastructure.security.argon2 import Argon2PasswordHasher


def test_hash_is_argon2id_and_does_not_contain_password() -> None:
    hashed = Argon2PasswordHasher().hash("gizli-sifre")

    assert hashed.startswith("$argon2id$")
    assert "gizli-sifre" not in hashed
    assert PasswordHasher().verify(hashed, "gizli-sifre")


def test_same_password_gets_different_hashes() -> None:
    hasher = Argon2PasswordHasher()

    assert hasher.hash("gizli-sifre") != hasher.hash("gizli-sifre")
