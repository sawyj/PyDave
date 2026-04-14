from pydave.paths import LIBDAVE_ROOT


def test_libdave_repo_exists():
    assert LIBDAVE_ROOT.exists()
    assert (LIBDAVE_ROOT / "README.md").exists()
