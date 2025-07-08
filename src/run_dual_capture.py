import subprocess
import sys
import os
import signal
import time
from typing import List


def launch_processes() -> List[subprocess.Popen]:
    """Launch screen and speaker capture scripts in independent processes.

    Returns a list with the two Popen objects (screen, speaker).
    """
    # Resolve absolute paths of the capture scripts relative to this file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    screen_script = os.path.join(base_dir, "capture", "capture_screen_text_in_continue.py")
    speaker_script = os.path.join(base_dir, "capture", "capture_speaker_text_in_continue.py")

    if not os.path.exists(screen_script):
        raise FileNotFoundError(f"Screen capture script not found: {screen_script}")
    if not os.path.exists(speaker_script):
        raise FileNotFoundError(f"Speaker capture script not found: {speaker_script}")

    print("🚀 Launching capture processes…")

    processes: List[subprocess.Popen] = []
    # NOTE: We *do not* create new process groups so that Ctrl+C pressed in the console
    # is delivered automatically to *all* processes attached to the console, including
    # these children. This lets each script execute its own SIGINT handler.
    processes.append(
        subprocess.Popen([sys.executable, screen_script])
    )
    processes.append(
        subprocess.Popen([sys.executable, speaker_script])
    )

    for proc, name in zip(processes, ["screen", "speaker"]):
        print(f"✅ {name.capitalize()} capture started (pid={proc.pid})")

    return processes


def wait_for_processes(processes: List[subprocess.Popen]):
    """Block until all provided processes exit (or Ctrl+C)."""
    try:
        while True:
            # Poll processes periodically to detect unexpected exits.
            all_exited = True
            for proc in processes:
                if proc.poll() is None:
                    all_exited = False
                elif proc.returncode != 0:
                    print(f"⚠️  Process pid={proc.pid} exited unexpectedly with code {proc.returncode}")
            if all_exited:
                break
            time.sleep(1.0)
    except KeyboardInterrupt:
        # Parent received Ctrl+C – child processes already got it as well.
        print("\n🛑 Ctrl+C detected – waiting for child processes to shut down…")
        _graceful_terminate(processes)

    # Final cleanup in any case
    _ensure_killed(processes)
    print("🏁 All capture processes stopped.")


def _graceful_terminate(processes: List[subprocess.Popen]):
    """Ask each still-running child process to terminate gracefully."""
    # Send SIGINT to any process that is still alive; they already have handlers.
    for proc in processes:
        if proc.poll() is None:  # Still running
            try:
                proc.send_signal(signal.SIGINT)
            except Exception as e:
                print(f"⚠️  Could not send SIGINT to pid {proc.pid}: {e}")

    # Wait up to 30 s for each process to stop by itself.
    for proc in processes:
        if proc.poll() is None:
            try:
                proc.wait(timeout=30.0)
                print(f"✅ Process pid={proc.pid} exited with code {proc.returncode}")
            except subprocess.TimeoutExpired:
                print(f"⌛ Process pid={proc.pid} did not exit within timeout – will kill.")


def _ensure_killed(processes: List[subprocess.Popen]):
    """Force-kill any process that is still running."""
    for proc in processes:
        if proc.poll() is None:
            try:
                proc.kill()
                print(f"🔪 Force-killed pid={proc.pid}")
            except Exception:
                pass


def main():
    """Entry-point for running dual capture."""
    try:
        processes = launch_processes()
        wait_for_processes(processes)
    except KeyboardInterrupt:
        # KeyboardInterrupt could happen very early (before processes list).
        print("\n🛑 Ctrl+C detected – nothing to do (processes not fully started)")
    except Exception as err:
        print(f"❌ Error: {err}")


if __name__ == "__main__":
    main() 