import replacer

import path
import pytest


@pytest.fixture
def test_path(tmpdir, monkeypatch):
    tmp_path = path.Path(tmpdir)
    this_path = path.Path(__file__).parent
    src = this_path.joinpath("test_path")
    dest = tmp_path.joinpath("test_path")
    src.copytree(dest)

    monkeypatch.chdir(dest)
    return dest


def assert_replaced(filename):
    assert "new" in path.Path(filename).text()


def assert_not_replaced(filename):
    assert "old" in path.Path(filename).text()


def test_help(capsys):
    with pytest.raises(SystemExit) as e:
        replacer.main(["--help"])
    stdout, _ = capsys.readouterr()
    assert "usage" in stdout
    assert(e.value.code) == 0


def test_replace_in_files(capsys, test_path):

    replacer.main(["old", "new"])
    stdout, _ = capsys.readouterr()

    assert "top.txt" in stdout
    assert "other.txt" not in stdout

    # Dry-run: files should not have changed:
    assert_not_replaced("top.txt")

    # Now re-run with --go
    replacer.main(["old", "new", "--go"])
    assert_replaced("top.txt")


def test_hidden(test_path):
    replacer.main(["old", "new", "--go"])
    assert_not_replaced(".hidden/hidden.txt")

    replacer.main(["old", "new", "--go", "--no-skip-hidden"])
    assert_replaced(".hidden/hidden.txt")


def test_include(test_path):
    replacer.main(["old", "new", "--go", "--include", "*.txt"])
    assert_replaced("top.txt")
    assert_not_replaced("b_dir/file.noext")
