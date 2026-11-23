import ctypes
import hashlib
import os
import platform
import shutil
import subprocess
import tarfile
import time
import zipfile
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.core.local_store import data_directory

GIB = 1024 ** 3
MODELS = [
    ("qwen3.5:0.8b-q8_0", "Compact", "1.0 GB"),
    ("qwen3.5:2b-q4_K_M", "Balanced", "1.9 GB"),
    ("qwen3.5:4b", "More capable", "3.3?4.0 GB"),
]
OLLAMA_RELEASE = "https://github.com/ollama/ollama/releases/download/v0.40.17/"
OLLAMA_ASSETS = {
    ("Windows", "amd64"): ("ollama-windows-amd64.zip", "3dd80f6e3a9699f2eadf4ac418f00529cee594df9557541806eda1f1f3f5588a"),
    ("Windows", "arm64"): ("ollama-windows-arm64.zip", "f5eab93c7e6dca27f47d556489fa89f760979c6f6f83e0bf1cb26d38630ce83a"),
    ("Linux", "amd64"): ("ollama-linux-amd64.tar.zst", "1df9d6228bac5a22e420b242708c0d10e5b886db97bab99d446a41760f4e79af"),
    ("Linux", "arm64"): ("ollama-linux-arm64.tar.zst", "0ec632480057cef6300459d1fa7dbbb3fc188b9a7d56cd0b0a72d05927d90ecc"),
    ("Darwin", "arm64"): ("ollama-darwin.tgz", "4b9db20d077c5a1e52fb4a6f2e6791f76ae945fd07c9b1a5647c82e927826653"),
}
WHISPER_ARCHIVE = ("https://github.com/ggml-org/whisper.cpp/releases/download/v1.8.3/whisper-bin-x64.zip",
                   "d824b1e37599f882b396e73f1ee0bfd5d0529f700314c48311dcbd00b803321d")
WHISPER_WEIGHTS = ("https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin",
                   "921e4cf8686fdd993dcd081a5da5b6c365bfde1162e72b08d75ac75289920b1f")
ollama_lock = Lock()
voice_lock = Lock()


def machine():
    arch = platform.machine().lower()
    return platform.system(), {"x86_64": "amd64", "aarch64": "arm64"}.get(arch, arch)


def command(*args):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL, timeout=3,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).strip()
    except (OSError, subprocess.SubprocessError):
        return ""


@lru_cache(maxsize=1)
def hardware():
    system, arch = machine()
    ram = None
    try:
        if system == "Windows":
            buffer = (ctypes.c_ulonglong * 8)()
            buffer[0] = ctypes.sizeof(buffer)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(buffer)):
                ram = buffer[1]
        elif system == "Darwin":
            ram = int(command("sysctl", "-n", "hw.memsize"))
        else:
            ram = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError, AttributeError):
        pass

    gpu = None
    vram = None
    reported = command("nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits")
    for line in reported.splitlines():
        name, _, memory = line.rpartition(",")
        if memory.strip().isdigit() and int(memory) * 1024**2 > (vram or 0):
            gpu, vram = name.strip(), int(memory) * 1024**2
    if system == "Linux" and vram is None:
        for path in Path("/sys/class/drm").glob("card*/device/mem_info_vram_total"):
            try:
                size = int(path.read_text())
            except (OSError, ValueError):
                continue
            if size > (vram or 0):
                gpu, vram = "AMD graphics", size
    if system == "Windows" and gpu is None:
        gpu = command("powershell.exe", "-NoProfile", "-Command",
                      "(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join ', '") or None
    unified = system == "Darwin" and arch == "arm64"
    if unified:
        gpu = "Apple silicon ? unified memory"
    graphics_memory = ram if unified else vram
    if graphics_memory is not None:
        tier = 2 if graphics_memory >= 12 * GIB else 1 if graphics_memory >= 6 * GIB else 0
    else:
        tier = 1 if (ram or 0) >= 16 * GIB else 0
    model = MODELS[tier][0]
    return {"system": system, "arch": arch, "cpu": platform.processor() or arch,
            "threads": os.cpu_count(), "ram_bytes": ram, "gpu": gpu, "vram_bytes": vram,
            "unified_memory": unified, "recommended": model}


def download(url, digest, destination, *, on_progress=None):
    checksum = hashlib.sha256()
    with httpx.stream("GET", url, follow_redirects=True, timeout=60) as response:
        response.raise_for_status()
        size = response.headers.get("content-length", "")
        total = int(size) if size.isdecimal() and not response.headers.get("content-encoding") else None
        received = 0
        if on_progress:
            on_progress(received, total)
        with destination.open("wb") as output:
            for chunk in response.iter_bytes(1024 * 1024):
                output.write(chunk)
                checksum.update(chunk)
                if on_progress:
                    received += len(chunk)
                    on_progress(received, total)
    if checksum.hexdigest() != digest:
        raise RuntimeError("The downloaded file failed its integrity check.")


def get_executable(folder, name):
    return next(iter(folder.rglob(name)), None) if folder.is_dir() else None


def install_archive(url, digest, filename, destination, executable, *, on_progress=None, on_install=None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as folder:
        scratch = Path(folder)
        archive = scratch / filename
        download(url, digest, archive, on_progress=on_progress)
        if on_install:
            on_install()
        staged = scratch / "runtime"
        staged.mkdir()
        if filename.endswith(".zip"):
            with zipfile.ZipFile(archive) as source:
                source.extractall(staged)
        elif filename.endswith(".zst"):
            import zstandard
            with archive.open("rb") as compressed, zstandard.ZstdDecompressor().stream_reader(compressed) as stream:
                with tarfile.open(fileobj=stream, mode="r|") as source:
                    source.extractall(staged, filter="data")
        else:
            with tarfile.open(archive) as source:
                source.extractall(staged, filter="data")
        binary = get_executable(staged, executable)
        if not binary or not binary.is_file():
            raise RuntimeError("This package did not contain a compatible executable.")
        relative = binary.relative_to(staged)
        staged.rename(destination)
    return destination / relative


def ollama_autosetup():
    address = urlsplit(settings.OLLAMA_BASE_URL)
    return address.scheme == "http" and address.hostname in ("localhost", "127.0.0.1") and not address.username


def ollama_tags():
    try:
        response = httpx.get(settings.OLLAMA_BASE_URL.rstrip("/") + "/api/tags", timeout=2)
        response.raise_for_status()
        return {entry["name"] for entry in response.json()["models"]}
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None


def ensure_ollama(install=False):
    if not ollama_autosetup():
        return ollama_tags()
    with ollama_lock:
        tags = ollama_tags()
        if tags is not None:
            return tags
        system, _ = machine()
        executable = "ollama.exe" if system == "Windows" else "ollama"
        root = data_directory() / "runtimes" / "ollama-v0.40.17"
        binary = shutil.which(executable) or get_executable(root, executable)
        if not binary and system == "Windows":
            installed = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / executable
            binary = installed if installed.is_file() else None
        if not binary and system == "Darwin":
            installed = Path("/Applications/Ollama.app/Contents/Resources/ollama")
            binary = installed if installed.is_file() else None
        if not binary:
            if not install:
                return None
            asset = OLLAMA_ASSETS.get(machine())
            if not asset:
                raise RuntimeError("Install Ollama for your platform, then retry the model download.")
            filename, digest = asset
            binary = install_archive(OLLAMA_RELEASE + filename, digest, filename, root, executable)
        address = urlsplit(settings.OLLAMA_BASE_URL)
        subprocess.Popen([str(binary), "serve"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                         env={**os.environ, "OLLAMA_HOST": f"127.0.0.1:{address.port or 11434}"})
        for _ in range(30):
            tags = ollama_tags()
            if tags is not None:
                return tags
            time.sleep(.5)
        return None


def whisper_paths():
    executable = shutil.which(settings.WHISPER_EXECUTABLE)
    if not executable:
        executable = get_executable(data_directory() / "runtimes" / "whisper-v1.8.3", "whisper-cli.exe")
    model = Path(settings.WHISPER_MODEL).expanduser() if settings.WHISPER_MODEL else data_directory() / "models" / "ggml-tiny.en.bin"
    return executable, model


def install_voice():
    with voice_lock:
        executable, model = whisper_paths()
        if not executable:
            if machine() != ("Windows", "amd64"):
                raise RuntimeError("Install whisper-cli for your platform, then retry the voice model download.")
            install_archive(*WHISPER_ARCHIVE, "whisper.zip",
                            data_directory() / "runtimes" / "whisper-v1.8.3", "whisper-cli.exe")
        if not model.is_file():
            if settings.WHISPER_MODEL:
                raise RuntimeError("The configured WHISPER_MODEL file could not be found.")
            model.parent.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(dir=model.parent) as folder:
                temporary = Path(folder) / model.name
                download(*WHISPER_WEIGHTS, temporary)
                temporary.replace(model)
