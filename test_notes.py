"""Tests for Tsunami Notes encryption and note management logic."""

import os
import tempfile
import unittest

from tsunami_notes.notes import (
    _derive_key,
    _encrypt,
    _decrypt,
    add_note,
    delete_note,
    edit_note,
    load_vault,
    save_vault,
    view_note,
    list_trash,
    restore_trash,
    empty_trash,
    export_vault,
    import_vault,
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
        self.assertEqual(len(v["trash"]), 1)
        self.assertEqual(v["trash"][0]["title"], "T")

    def test_restore_trash(self):
        v = self._vault()
        add_note(v, "T", "B")
        delete_note(v, 1)
        restore_trash(v, 1)
        self.assertEqual(len(v["notes"]), 1)
        self.assertEqual(len(v["trash"]), 0)
        self.assertEqual(v["notes"][0]["title"], "T")

    def test_empty_trash(self):
        v = self._vault()
        add_note(v, "T", "B")
        delete_note(v, 1)
        empty_trash(v)
        self.assertEqual(len(v["trash"]), 0)

    def test_export_import_vault(self):
        v = self._vault()
        add_note(v, "Exp", "Body")
        fd, tmp = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            export_vault(v, tmp)
            v2 = self._vault()
            import_vault(v2, tmp)
            self.assertEqual(len(v2["notes"]), 1)
            self.assertEqual(v2["notes"][0]["title"], "Exp")
        finally:
            os.remove(tmp)

    def test_delete_out_of_range(self, capsys=None):
        v = self._vault()
        # should not raise
        delete_note(v, 99)

    def test_edit_out_of_range(self):
        v = self._vault()
        # should not raise
        edit_note(v, 99, title="x", body=None)

    def test_add_note_with_tags(self):
        v = self._vault()
        add_note(v, "Title", "Body", ["tag1", "tag2"])
        self.assertEqual(len(v["notes"]), 1)
        self.assertEqual(v["notes"][0]["tags"], ["tag1", "tag2"])

    def test_edit_note_tags(self):
        v = self._vault()
        add_note(v, "Title", "Body", ["tag1"])
        edit_note(v, 1, title=None, body=None, tags=["tag2"])
        self.assertEqual(v["notes"][0]["tags"], ["tag2"])

    def test_revisions(self):
        from tsunami_notes.notes import add_note, edit_note, rollback_revision

        v = self._vault()
        add_note(v, "T1", "B1")
        edit_note(v, 1, title="T2", body="B2")
        self.assertEqual(v["notes"][0]["title"], "T2")
        self.assertEqual(len(v["notes"][0]["revisions"]), 1)
        self.assertEqual(v["notes"][0]["revisions"][0]["title"], "T1")

        rollback_revision(v, 1, 1)
        self.assertEqual(v["notes"][0]["title"], "T1")
        self.assertEqual(len(v["notes"][0]["revisions"]), 2)
        self.assertEqual(v["notes"][0]["revisions"][1]["title"], "T2")

    def test_search_notes(self):
        from tsunami_notes.notes import search_notes
        from unittest.mock import patch
        import io

        v = self._vault()
        add_note(v, "Secret meeting", "Meet at noon", [])

        # Test finding in title
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            search_notes(v, "meeting")
            self.assertIn("Secret meeting", mock_stdout.getvalue())

        # Test finding in body
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            search_notes(v, "noon")
            self.assertIn("Secret meeting", mock_stdout.getvalue())

        # Test not finding
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            search_notes(v, "xyz")
            self.assertIn("No matching notes found", mock_stdout.getvalue())


class TestDuress(unittest.TestCase):
    def setUp(self):
        fd, self.tmp = tempfile.mkstemp(suffix=".vault")
        os.close(fd)
        os.remove(self.tmp)

    def tearDown(self):
        for p in [self.tmp, self.tmp + ".meta", self.tmp + ".fake"]:
            if os.path.exists(p):
                os.remove(p)

    def test_duress_flow(self):
        from tsunami_notes.notes import (
            save_vault,
            set_duress_password,
            check_duress_password,
            handle_duress,
        )

        vault = {"notes": [{"title": "secret", "body": "data"}]}
        save_vault(self.tmp, "main_pw", vault)

        # Set duress password
        set_duress_password(self.tmp, "duress_pw")

        # Check passwords
        self.assertFalse(check_duress_password(self.tmp, "main_pw"))
        self.assertFalse(check_duress_password(self.tmp, "wrong_pw"))
        self.assertTrue(check_duress_password(self.tmp, "duress_pw"))

        # Handle duress
        handle_duress(self.tmp)

        self.assertFalse(os.path.exists(self.tmp))
        self.assertFalse(os.path.exists(self.tmp + ".meta"))


if __name__ == "__main__":
    unittest.main()
