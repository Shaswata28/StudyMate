import logging
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock

from app.core.local_store import data_directory
from app.services.local_setup import get_executable, install_archive, machine

RELEASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
# Kokoro English v0.19 uses the bundled eSpeak pronunciation data.
VERSION = "v1.13.3"
ASSETS = {
    ("Windows", "amd64"): ("win-x64-shared-MT-Release", "0043cd9cdd755d35627299e6a02839e95a262508ae9593af6c5c72ffd674b650"),
    ("Windows", "arm64"): ("win-arm64-shared-MT-Release", "2627ab760ac0551601bb1f60f78f43fa848809395cae88372f69ebf7d49b1f44"),
    ("Darwin", "amd64"): ("osx-x64-shared", "d43a1fe29406f76ef05874ac2cb1ffa90550c7035ca12108f6a0c8856c143b88"),
    ("Darwin", "arm64"): ("osx-arm64-shared", "d67b1a77ca252a4dbe0480255c61eeadc951708d15ac840c12308864496b134d"),
    ("Linux", "amd64"): ("linux-x64-shared", "3e6aa632a30b7047f389e337e342eb08ea6c5661717645fd072e7d0ebf9d57fb"),
    ("Linux", "arm64"): ("linux-aarch64-shared-cpu", "dca81c3d36c68e84949158a993e2ea99055bcecc96893f93739209fbe2eac649"),
}
MODEL_ARCHIVE = "kokoro-int8-en-v0_19.tar.bz2"
MODEL_DIGEST = "c9f0dd393615805b0bab050c340834d5e684e732aec91c0e860cd30e982c08bd"
install_lock = Lock()
install_progress = None
speech_lock = Lock()
logger = logging.getLogger(__name__)


def directories():
    root = data_directory()
    return root / "runtimes" / f"sherpa-onnx-{VERSION}", root / "models" / "kokoro-en-int8"


def executable_name():
    return "sherpa-onnx-offline-tts.exe" if machine()[0] == "Windows" else "sherpa-onnx-offline-tts"


def kokoro_files():
    runtime, weights = directories()
    binary = get_executable(runtime, executable_name())
    voices = get_executable(weights, "voices.bin")
    if binary and voices:
        assets = voices.parent
        model = next(iter(assets.glob("*.onnx")), None)
        if model and (assets / "tokens.txt").is_file() and (assets / "espeak-ng-data").is_dir():
            return binary, model
    return None


def install_kokoro_archive(package, *args):
    global install_progress

    def report_download(received, total):
        global install_progress
        install_progress = {"phase": "downloading", "package": package, "received": received, "total": total}

    def report_install():
        global install_progress
        install_progress = {**install_progress, "phase": "installing"}

    report_download(0, None)
    try:
        install_archive(*args, on_progress=report_download, on_install=report_install)
    finally:
        install_progress = None


def install_kokoro():
    asset = ASSETS.get(machine())
    if asset is None:
        raise RuntimeError("Kokoro is unavailable for this platform.")
    with install_lock:
        runtime, weights = directories()
        if not get_executable(runtime, executable_name()):
            suffix, digest = asset
            archive = f"sherpa-onnx-{VERSION}-{suffix}.tar.bz2"
            install_kokoro_archive("runtime", f"{RELEASE}{VERSION}/{archive}", digest, archive, runtime, executable_name())
        if not get_executable(weights, "voices.bin"):
            install_kokoro_archive("voice", f"{RELEASE}tts-models/{MODEL_ARCHIVE}", MODEL_DIGEST, MODEL_ARCHIVE, weights, "voices.bin")
        if not kokoro_files():
            raise RuntimeError("The installed Kokoro package is incomplete.")


def synthesize_kokoro(text: str) -> bytes:
    files = kokoro_files()
    if not files:
        raise RuntimeError("Download Kokoro in Settings before using this voice.")
    binary, model = files
    assets = model.parent
    libraries = str(binary.parent.parent / "lib")
    environment = os.environ.copy()
    environment["PATH"] = libraries + os.pathsep + environment.get("PATH", "")
    environment["LD_LIBRARY_PATH"] = libraries + os.pathsep + environment.get("LD_LIBRARY_PATH_ORIG", "")
    environment["DYLD_LIBRARY_PATH"] = libraries
    if not speech_lock.acquire(timeout=20):
        raise RuntimeError("Kokoro is already reading aloud. Try again in a moment.")
    try:
        with TemporaryDirectory() as folder:
            audio = Path(folder) / "read-aloud.wav"
            result = subprocess.run(
                [str(binary), f"--kokoro-model={model}", f"--kokoro-voices={assets / 'voices.bin'}",
                 f"--kokoro-tokens={assets / 'tokens.txt'}", f"--kokoro-data-dir={assets / 'espeak-ng-data'}",
                 "--num-threads=2", "--sid=0", f"--output-filename={audio}", " " + text],
                cwd=binary.parent, env=environment, capture_output=True, timeout=90,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=False,
            )
            if result.returncode or not audio.is_file():
                logger.warning("Kokoro exited with status %s", result.returncode)
                raise RuntimeError("Kokoro could not read this text aloud.")
            return audio.read_bytes()
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError("Kokoro could not finish reading this text.") from error
    finally:
        speech_lock.release()
