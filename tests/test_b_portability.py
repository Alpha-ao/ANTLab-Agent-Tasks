import importlib.util
import pathlib
import tempfile
import unittest

MODULE=pathlib.Path(__file__).resolve().parents[1]/'scripts/b_artifacts.py'
spec=importlib.util.spec_from_file_location('b_artifact_helpers',MODULE)
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)

class PortabilityTests(unittest.TestCase):
    def test_windows_paths_and_exact_line_ending_equivalence(self):
        import hashlib
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);(root/'folder').mkdir();p=root/'folder/file.py'
            original=b'x = 1\n';expected=hashlib.sha256(original).hexdigest()
            manifest={'folder/file.py':{'historical_raw_sha256':expected,'lf_sha256':helpers.text_hash(original)}}
            p.write_bytes(b'x = 1\r\n')
            self.assertEqual(helpers.portable_path(root,'folder\\file.py'),p)
            self.assertTrue(helpers.matches_hash(root,'folder\\file.py',expected,manifest))
            p.write_bytes(b'x = 2\r\n')
            self.assertFalse(helpers.matches_hash(root,'folder\\file.py',expected,manifest))
            for bad in ('../secret','/root/secret','C:\\secret'):
                with self.assertRaises(ValueError):helpers.portable_path(root,bad)
