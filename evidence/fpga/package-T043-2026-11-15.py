"""Preserve the verified T043 implementation without modifying its manifest.

Run from the project root. Refuses to overwrite the archive or package receipt.
This packages existing evidence only; it never invokes EDA or hardware tools.
"""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / 'evidence/fpga/T043-implementation-2026-11-15.zip'
RECEIPT = ROOT / 'evidence/fpga/review-package-2026-11-15.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(name):
    path = (ROOT / name).resolve()
    path.relative_to(ROOT)
    return path.read_bytes()


def main():
    assert not ARCHIVE.exists() and not RECEIPT.exists(), 'Existing package preserved'
    manifest_name = 'evidence/fpga/manifest.json'
    audit_name = 'evidence/fpga/final-audit-2026-11-15.json'
    manifest = json.loads(read(manifest_name))
    audit = json.loads(read(audit_name))
    assert manifest['status'] == audit['status'] == 'PASS'
    assert sha(read(manifest_name)) == audit['manifest_sha256']
    expected = {}
    for mapping in (manifest['artifacts'], manifest['source_sha256'], audit['receipts_sha256']):
        for name, digest in mapping.items():
            assert name not in expected or expected[name] == digest
            expected[name] = digest
    for name in (manifest_name, audit_name, audit['attempt_journal'],
                 'evidence/fpga/final-audit-2026-11-15.py',
                 'evidence/fpga/package-T043-2026-11-15.py'):
        expected[name] = sha(read(name))
    # Validate before writing and again while packaging; retain any failed archive.
    for name, digest in expected.items():
        assert sha(read(name)) == digest, 'Input drift: ' + name
    with zipfile.ZipFile(ARCHIVE, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, digest in sorted(expected.items()):
            data = read(name)
            assert sha(data) == digest, 'Input drift: ' + name
            archive.writestr(name, data)
    with zipfile.ZipFile(ARCHIVE) as archive:
        assert archive.testzip() is None
        assert sorted(archive.namelist()) == sorted(expected)
        for name, digest in expected.items():
            assert sha(archive.read(name)) == digest, 'Archive drift: ' + name
    receipt = {
        'task': 'T043', 'status': 'PASS', 'package_date_la': '2026-11-15',
        'verification_date_la': audit['verification_date_la'],
        'scope': 'Recoverable implementation evidence; awaiting owner review, no programming',
        'base_commit': manifest['base_commit'],
        'archive': str(ARCHIVE.relative_to(ROOT)).replace('\\', '/'),
        'archive_sha256': sha(ARCHIVE.read_bytes()), 'archive_bytes': ARCHIVE.stat().st_size,
        'members': expected, 'member_count': len(expected),
        'manifest_sha256': audit['manifest_sha256'], 'audit_sha256': sha(read(audit_name)),
        'bitstream': audit['output'] + '/design.bit',
        'bitstream_sha256': audit['bitstream_sha256'],
        'formal': 'T023 owner-skipped / NOT RUN',
        'physical_programming': 'NOT RUN', 'asic': 'NOT RUN',
    }
    with RECEIPT.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'members'}, indent=2))


if __name__ == '__main__':
    main()
