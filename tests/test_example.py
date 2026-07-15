def test_tmp_path_example(tmp_path):
    # tmp_path is a pathlib.Path object that points to a temporary directory
    # This directory is unique for each test and cleaned up after the test
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    assert test_file.read_text() == "Hello, World!"
    assert test_file.exists()
