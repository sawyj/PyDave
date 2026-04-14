from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
VENDOR_ROOT = PROJECT_ROOT / "vendor"
LIBDAVE_ROOT = VENDOR_ROOT / "libdave"
