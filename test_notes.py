"""Tests for Tsunami Notes encryption and note management logic."""

import os
import tempfile
import unittest

from notes import (
    _derive_key,
    _encrypt,
    _decrypt,
    add_note,
    delete_note,
    edit_note,
    load_vault,
    save_vault,
    view_note,
)


class TestCrypto(unittest.TestCase):
    def test_derive_key_length(self):
        key = _derive_key("password", b"saltsaltsaltsalt" * 2)
        self.assertEqual(len(key), 32)

    def test_derive_key_deterministic(self):
        salt = os.urandom(32)
        k1 = _derive_key("secret", salt)
        k2 = _derive_key("secret", salt)
        self.assertEqual(k1, k2)

    def test_derive_key_different_passwords(self):
        salt = os.urandom(32)
        k1 = _derive_key("password1", salt)
        k2 = _derive_key("password2", salt)
        self.assertNotEqual(k1, k2)

    def test_encrypt_decrypt_roundtrip(self):
        key = os.urandom(32)
        plaintext = b"Hello, Tsunami!"
        ciphertext = _encrypt(key, plaintext)
        self.assertEqual(_decrypt(key, ciphertext), plaintext)

    def test_encrypt_produces_different_nonce(self):
        key = os.urandom(32)
        c1 = _encrypt(key, b"same")
        c2 = _encrypt(key, b"same")
        # nonces (first 12 bytes) should differ with overwhelming probability
        self.assertNotEqual(c1[:12], c2[:12])

    def test_decrypt_wrong_key_raises(self):
        key = os.urandom(32)
        wrong_key = os.urandom(32)
        ciphertext = _encrypt(key, b"secret")
        with self.assertRaises(Exception):
            _decrypt(wrong_key, ciphertext)


class TestVault(unittest.TestCase):
    def setUp(self):
        fd, self.tmp = tempfile.mkstemp(suffix=".vault")
        os.close(fd)
        os.remove(self.tmp)  # save_vault creates the file itself

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_save_and_load(self):
        vault = {"notes": [{"title": "t", "body": "b"}]}
        save_vault(self.tmp, "pw", vault)
        loaded = load_vault(self.tmp, "pw")
        self.assertEqual(loaded, vault)

    def test_load_nonexistent_returns_empty(self):
        v = load_vault("/tmp/does_not_exist_tsunami.vault", "pw")
        self.assertEqual(v, {"notes": []})

    def test_wrong_password_raises(self):
        save_vault(self.tmp, "correct", {"notes": []})
        with self.assertRaises(ValueError):
            load_vault(self.tmp, "wrong")

    def test_file_permissions(self):
        save_vault(self.tmp, "pw", {"notes": []})
        mode = oct(os.stat(self.tmp).st_mode & 0o777)
        self.assertEqual(mode, oct(0o600))

    def test_save_reencrypts_each_time(self):
        vault = {"notes": []}
        save_vault(self.tmp, "pw", vault)
        with open(self.tmp, "rb") as fh:
            data1 = fh.read()
        save_vault(self.tmp, "pw", vault)
        with open(self.tmp, "rb") as fh:
            data2 = fh.read()
        # New salt + nonce each time → different bytes
        self.assertNotEqual(data1, data2)


class TestNoteOperations(unittest.TestCase):
    def _vault(self):
        return {"notes": []}

    def test_add_note(self):
        v = self._vault()
        add_note(v, "Title", "Body")
        self.assertEqual(len(v["notes"]), 1)
        self.assertEqual(v["notes"][0]["title"], "Title")

    def test_view_note(self, capsys=None):
        v = self._vault()
        add_note(v, "T", "B")
        # should not raise
        view_note(v, 1)

    def test_edit_note_title(self):
        v = self._vault()
        add_note(v, "Old", "Body")
        edit_note(v, 1, title="New", body=None)
        self.assertEqual(v["notes"][0]["title"], "New")
        self.assertEqual(v["notes"][0]["body"], "Body")

    def test_edit_note_body(self):
        v = self._vault()
        add_note(v, "T", "Old body")
        edit_note(v, 1, title=None, body="New body")
        self.assertEqual(v["notes"][0]["body"], "New body")

    def test_delete_note(self):
        v = self._vault()
        add_note(v, "T", "B")
        delete_note(v, 1)
        self.assertEqual(len(v["notes"]), 0)

    def test_delete_out_of_range(self, capsys=None):
        v = self._vault()
        # should not raise
        delete_note(v, 99)

    def test_edit_out_of_range(self):
        v = self._vault()
        # should not raise
        edit_note(v, 99, title="x", body=None)


if __name__ == "__main__":
    unittest.main()
