"""Regression checks for the explicit Vercel container context allowlist."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class DockerContextTests(unittest.TestCase):
    def test_source_stage_copy_files_have_explicit_allowlist(self):
        lines = (ROOT / 'Dockerfile.vercel.dockerignore').read_text().splitlines()
        dockerfile = (ROOT / 'Dockerfile.vercel').read_text().splitlines()
        for line in dockerfile:
            if line.startswith('FROM ') and ' AS native' in line:
                break
            if not line.startswith('COPY '):
                continue
            tokens = line.split()[1:-1]
            for path in tokens:
                if path.endswith('/'):
                    self.assertTrue((ROOT / path).is_dir(), path)
                    continue
                self.assertTrue((ROOT / path).is_file(), path)
                self.assertIn('!' + path, lines, path + ' missing from allowlist')
                # The source-stage file must be re-included after the parent glob.
                parent_glob = path.rsplit('/', 1)[0] + '/*' if '/' in path else '**'
                if parent_glob in lines:
                    self.assertGreater(lines.index('!' + path), lines.index(parent_glob), path)

if __name__ == '__main__':
    unittest.main()
