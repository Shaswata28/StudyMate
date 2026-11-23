from contextlib import contextmanager
from io import BytesIO
import hashlib
import tarfile
from unittest.mock import patch

import httpx

from app.services import kokoro


def test_kokoro_install_progress(tmp_path):
    archive = BytesIO()
    with tarfile.open(fileobj=archive, mode="w:bz2") as tar:
        entry = tarfile.TarInfo("voices.bin")
        entry.size = 5
        tar.addfile(entry, BytesIO(b"voice"))
    payload = archive.getvalue()
    observed = []

    @contextmanager
    def stream(method, url, **kwargs):
        observed.append(kokoro.install_progress)
        yield httpx.Response(200, content=payload, request=httpx.Request(method, url))

    extract = tarfile.TarFile.extractall

    def record_install(tar, *args, **kwargs):
        observed.append(kokoro.install_progress)
        return extract(tar, *args, **kwargs)

    target = tmp_path / "voice"
    with patch.object(httpx, "stream", stream), patch.object(tarfile.TarFile, "extractall", record_install):
        kokoro.install_kokoro_archive(
            "voice", "https://example.com/voice", hashlib.sha256(payload).hexdigest(),
            "voice.tar.bz2", target, "voices.bin",
        )

    assert (target / "voices.bin").read_bytes() == b"voice"
    assert observed == [
        dict(phase="downloading", package="voice", received=0, total=None),
        dict(phase="installing", package="voice", received=len(payload), total=len(payload)),
    ]
    assert kokoro.install_progress is None
