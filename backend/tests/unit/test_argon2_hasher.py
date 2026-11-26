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


def test_verify_accepts_correct_password_only() -> None:
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash("gizli-sifre")

    assert hasher.verify(hashed, "gizli-sifre")
    assert not hasher.verify(hashed, "yanlis-sifre")


def test_verify_with_broken_hash_returns_false() -> None:
    assert not Argon2PasswordHasher().verify("bozuk-hash", "gizli-sifre")
