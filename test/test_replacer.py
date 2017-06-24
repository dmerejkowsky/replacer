import replacer

import path
import pytest


@pytest.fixture
def tmp_path(tmpdir, monkeypatch):
    monkeypatch.chdir(tmpdir)
    return path.Path(tmpdir)


def test_help(capsys):
    with pytest.raises(SystemExit) as e:
        replacer.main(["--help"])
    stdout, _ = capsys.readouterr()
    assert "usage" in stdout
    assert(e.value.code) == 0


def test_replace_in_files(capsys, tmp_path):
    a_path = tmp_path.joinpath("a")
    a_path.mkdir()
    foo_path = a_path.joinpath("foo.txt")
    foo_path.write_text("This is bar")
    spam_path = a_path.joinpath("spam")
    spam_path.write_text("bar is good")
    other_path = a_path.joinpath("other.txt")
    other_path.write_text("Other contents")

    replacer.main(["bar", "baz"])
    stdout, _ = capsys.readouterr()

    assert "a/foo.txt" in stdout
    assert "a/other.txt" not in stdout

    # Dry-run: files should not have changed:
    assert foo_path.text() == "This is bar"

    # Now re-run with --go
    replacer.main(["bar", "baz", "--go"])
    assert foo_path.text() == "This is baz"
