import time

def timed(label):
    """Print start/end with elapsed time for any operation."""
    class Timer:
        def __enter__(self):
            print(f"[START] {label}")
            self.start = time.perf_counter()
            return self
        def __exit__(self, *args):
            elapsed = (time.perf_counter() - self.start) * 1000
            print(f"[DONE]  {label} — {elapsed:.2f} ms")
    return Timer()