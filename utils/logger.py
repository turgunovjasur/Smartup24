import os
import logging
import traceback
from datetime import datetime

LOG_DIR = "test-results/logs"

# ----------------------------------------------------------------------------------------------------------------------

class TestLogger:
    """
    Har bir test funksiyasi uchun alohida log fayl yaratadi.
    test-results/logs/{test_name}_{timestamp}.log
    """

    def __init__(self, test_name):
        self.test_name = test_name
        self.log_path = self._setup_log_file()
        self._logger = self._create_logger()
        self.has_failures = False

    def _setup_log_file(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = self.test_name.replace("::", "__").replace(" ", "_").replace("/", "_")
        filename = f"{safe_name}_{timestamp}.log"
        return os.path.join(LOG_DIR, filename)

    def _create_logger(self):
        logger = logging.getLogger(f"test.{self.test_name}.{id(self)}")
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        logger.propagate = False

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        fh = logging.FileHandler(self.log_path, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        return logger

    # ------------------------------------------------------------------------------------------------------------------

    def info(self, message):
        self._logger.info(message)

    def step(self, message):
        self._logger.info(f"[STEP] {message}")

    def warning(self, message):
        self._logger.warning(f"[WARNING] {message}")

    def fail(self, message, exc=None, raise_error=False):
        self.has_failures = True
        self._logger.error(f"[FAIL] {message}")
        if exc is not None:
            self._logger.error(f"[EXCEPTION] {type(exc).__name__}: {exc}")
            tb = traceback.format_exc()
            if tb.strip() != "NoneType: None":
                self._logger.error(f"[TRACEBACK]\n{tb}")
        if raise_error:
            raise AssertionError(message) from exc

    def close(self):
        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)

    # ------------------------------------------------------------------------------------------------------------------

    def __enter__(self):
        self._logger.info("=" * 60)
        self._logger.info(f"[START] {self.test_name}")
        self._logger.info(f"[TIME]  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._logger.info("=" * 60)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._logger.info("-" * 60)
        if exc_type is not None:
            self.fail(f"Test FAILED: {self.test_name}", exc_val)
            self._logger.error(f"[RESULT] FAILED")
        else:
            self._logger.info(f"[RESULT] PASSED")
        self._logger.info("=" * 60)
        self.close()
        return False

# ----------------------------------------------------------------------------------------------------------------------

def get_logger(test_name):
    """Yangi TestLogger obyekti qaytaradi."""
    return TestLogger(test_name)

# ----------------------------------------------------------------------------------------------------------------------

def write_failure_log(test_name, when, longrepr):
    """
    pytest hook ichidan chaqiriladi.
    Muvaffaqiyatsiz test uchun log fayl yozadi va fayl yo'lini qaytaradi.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = test_name.replace("::", "__").replace(" ", "_").replace("/", "_")
    filename = f"{safe_name}_{timestamp}.log"
    log_path = os.path.join(LOG_DIR, filename)

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"TEST NAME : {test_name}\n")
        f.write(f"PHASE     : {when}\n")
        f.write(f"RESULT    : FAILED\n")
        f.write(f"TIME      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"[XATO]\n{longrepr}\n")

    return log_path
