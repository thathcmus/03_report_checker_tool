"""One-Touch Audio Recording Utility for StandupCoach.

Records spoken daily standup from the microphone and saves as a WAV file.
Provides interactive prompts:
  "Press Enter to start recording, speak into your microphone..."
  "Press Enter to stop recording..."
Supports Windows native multimedia recording (winmm.dll), sounddevice, and pyaudio.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
import threading
import time

# Ensure UTF-8 output encoding on Windows consoles/pipes
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("recorder")

DEFAULT_OUTPUT_PATH = Path("records/latest_report.wav")


def _record_with_sounddevice(
    output_path: Path,
    stop_event: threading.Event,
    sample_rate: int = 16000,
    channels: int = 1,
    duration: float | None = None,
) -> bool:
    """Record using sounddevice and scipy.io.wavfile or wave if available."""
    try:
        import sounddevice as sd  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        return False

    frames: list[np.ndarray] = []

    def callback(indata, frame_count, time_info, status):
        if status:
            logger.warning("Audio input status: %s", status)
        frames.append(indata.copy())

    try:
        with sd.InputStream(samplerate=sample_rate, channels=channels, dtype="int16", callback=callback):
            start_time = time.time()
            while not stop_event.is_set():
                if duration and (time.time() - start_time) >= duration:
                    break
                time.sleep(0.05)

        if not frames:
            return False

        audio_data = np.concatenate(frames, axis=0)

        # Try scipy first, then wave
        try:
            from scipy.io import wavfile  # type: ignore
            wavfile.write(str(output_path), sample_rate, audio_data)
        except ImportError:
            import wave
            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())

        return output_path.exists() and output_path.stat().st_size > 0
    except Exception as err:
        logger.warning("sounddevice recording encountered error: %s", err)
        return False


def _record_with_pyaudio(
    output_path: Path,
    stop_event: threading.Event,
    sample_rate: int = 16000,
    channels: int = 1,
    duration: float | None = None,
) -> bool:
    """Record using pyaudio and standard library wave if available."""
    try:
        import pyaudio  # type: ignore
        import wave
    except ImportError:
        return False

    try:
        p = pyaudio.PyAudio()
        chunk = 1024
        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk,
        )

        frames: list[bytes] = []
        start_time = time.time()
        while not stop_event.is_set():
            if duration and (time.time() - start_time) >= duration:
                break
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b"".join(frames))

        return output_path.exists() and output_path.stat().st_size > 0
    except Exception as err:
        logger.warning("pyaudio recording encountered error: %s", err)
        return False


def _record_with_winmm(
    output_path: Path,
    stop_event: threading.Event,
    sample_rate: int = 16000,
    channels: int = 1,
    duration: float | None = None,
) -> bool:
    """Record audio on Windows using native winmm.dll via ctypes (zero external dependencies)."""
    if sys.platform != "win32":
        return False

    try:
        import ctypes
        winmm = ctypes.windll.winmm

        # Close any lingering session
        winmm.mciSendStringW("close recsound", None, 0, 0)

        # Open waveaudio device
        res_open = winmm.mciSendStringW("open new type waveaudio alias recsound", None, 0, 0)
        if res_open != 0:
            return False

        bytes_per_sample = 2  # 16-bit
        block_align = channels * bytes_per_sample
        bytes_per_sec = sample_rate * block_align
        cmd_set = (
            f"set recsound time format ms bitspersample {bytes_per_sample * 8} "
            f"channels {channels} samplespersec {sample_rate} "
            f"bytespersec {bytes_per_sec} alignment {block_align}"
        )
        winmm.mciSendStringW(cmd_set, None, 0, 0)

        # Start recording
        res_record = winmm.mciSendStringW("record recsound", None, 0, 0)
        if res_record != 0:
            winmm.mciSendStringW("close recsound", None, 0, 0)
            return False

        start_time = time.time()
        while not stop_event.is_set():
            if duration and (time.time() - start_time) >= duration:
                break
            time.sleep(0.05)

        # Stop and save to target wav file
        abs_path = str(output_path.resolve())
        res_save = winmm.mciSendStringW(f'save recsound "{abs_path}"', None, 0, 0)
        winmm.mciSendStringW("close recsound", None, 0, 0)

        return res_save == 0 and output_path.exists() and output_path.stat().st_size > 0
    except Exception as err:
        logger.warning("Windows winmm recording error: %s", err)
        return False


def record_audio(
    output_file: str | Path = DEFAULT_OUTPUT_PATH,
    duration: float | None = None,
    interactive: bool = True,
    sample_rate: int = 16000,
    channels: int = 1,
) -> Path:
    """Record audio interactively or for a fixed duration.

    Args:
        output_file: Target WAV file path (defaults to records/latest_report.wav).
        duration: Optional fixed duration in seconds.
        interactive: If True, prompts the user to press Enter to start and stop.
        sample_rate: Sample rate in Hz (default: 16000).
        channels: Channel count (default: 1 mono).

    Returns:
        Path to the saved WAV file.
    """
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if interactive:
        print("\n" + "=" * 60)
        print("🎙️ StandupCoach Audio Recorder")
        print("=" * 60)
        input("Press Enter to start recording, speak into your microphone...")

    stop_event = threading.Event()

    print("🔴 Recording started... Speak clearly into your microphone.")
    if interactive:
        # Launch worker thread to monitor Enter key
        def wait_for_stop():
            input("Press Enter to stop recording...\n")
            stop_event.set()

        listener_thread = threading.Thread(target=wait_for_stop, daemon=True)
        listener_thread.start()

    # Try recording backends in priority order:
    # 1. sounddevice (cross-platform, high performance)
    # 2. pyaudio (cross-platform)
    # 3. winmm (Windows native, zero external dependencies)
    recorded = False
    start_record_time = time.time()

    for backend_fn in (_record_with_sounddevice, _record_with_pyaudio, _record_with_winmm):
        if backend_fn(out_path, stop_event, sample_rate, channels, duration):
            recorded = True
            break

    elapsed = round(time.time() - start_record_time, 1)

    if not recorded:
        err_msg = (
            "❌ Error: Unable to record audio.\n"
            "Action required: Please install the recommended audio recording package:\n"
            "    pip install sounddevice numpy scipy\n"
        )
        sys.stderr.write(err_msg)
        sys.exit(1)

    file_size_kb = round(out_path.stat().st_size / 1024, 1)
    print("=" * 60)
    print("✅ Recording completed successfully!")
    print(f"File saved:    {out_path.resolve()}")
    print(f"Duration:      ~{elapsed}s")
    print(f"File size:     {file_size_kb} KB")
    print("=" * 60)

    return out_path


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="One-touch interactive audio recorder for StandupCoach.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Target output audio file path (defaults to records/latest_report.wav)",
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=None,
        help="Optional recording duration limit in seconds",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Non-interactive mode (requires --duration to stop automatically)",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Sampling rate in Hz (default: 16000)",
    )
    return parser


def main() -> None:
    """CLI Entrypoint for recording."""
    parser = build_parser()
    args = parser.parse_args()

    interactive = not args.non_interactive
    if not interactive and args.duration is None:
        parser.error("--non-interactive mode requires specifying --duration in seconds.")

    record_audio(
        output_file=args.output,
        duration=args.duration,
        interactive=interactive,
        sample_rate=args.sample_rate,
    )


if __name__ == "__main__":
    main()
