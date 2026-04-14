from pydave.native import candidate_library_paths


def test_candidate_library_paths_are_project_local():
    candidates = candidate_library_paths()
    assert candidates
    assert all('PyDAVE' in str(path) for path in candidates)
