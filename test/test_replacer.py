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
    as_path = path.Path(filename)
    if replacer.is_binary(as_path):
        assert b"new" in as_path.bytes()
    else:
        assert "new" in as_path.text()


def assert_not_replaced(filename):
    as_path = path.Path(filename)
    if replacer.is_binary(as_path):
        assert b"old" in as_path.bytes()
    else:
        assert "old" in as_path.text()


def ensure_matching_file(src, binary=False):
    src = path.Path(src)
    if src.parent:
        src.parent.makedirs_p()
    if binary:
        src.write_bytes(b"MAGIC\0old\xca\xff\xee")
    else:
        src.write_text("this is old")


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


def test_exclude_extension(test_path):
    replacer.main(["old", "new", "--go", "--exclude", "*.txt"])
    assert_not_replaced("top.txt")
    assert_replaced("b_dir/file.noext")


def test_exclude_directory(test_path):
    one = "node_modules/one.js"
    two = "packages/foo/node_modules/two.js"
    for f in one, two:
        ensure_matching_file(f)

    replacer.main(["old", "new", "--go", "--exclude", "node_modules/*"])
    assert_not_replaced(one)
    assert_not_replaced(two)


def test_skip_binaries(test_path):
    ensure_matching_file("foo.exe", binary=True)
    replacer.main(["old", "new"])
    assert_not_replaced("foo.exe")
