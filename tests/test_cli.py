import os
import sys
import pytest
from osdlc.cli import check_git_repo, print_banner, print_summary


class TestCheckGitRepo:

    def test_returns_true_in_git_repo(self, git_init):
        assert check_git_repo(git_init) is True

    def test_returns_false_in_non_git_dir(self, temp_dir):
        assert check_git_repo(temp_dir) is False

    def test_returns_false_for_nonexistent_path(self):
        assert check_git_repo(r"C:\nonexistent_xyzzy_path") is False


class TestPrintFunctions:

    def test_print_banner(self, capsys):
        print_banner()
        captured = capsys.readouterr()
        assert "AI Open SDLC Kit" in captured.out

    def test_print_summary_with_files(self, capsys):
        print_summary(
            generated=["file1.txt", "file2.txt"],
            skipped=[".env"],
            errors=[("bad.txt", "permission denied")]
        )
        captured = capsys.readouterr()
        assert "Generated (2 files)" in captured.out
        assert "file1.txt" in captured.out
        assert "file2.txt" in captured.out
        assert "Skipped (1" in captured.out
        assert ".env" in captured.out
        assert "Errors (1)" in captured.out
        assert "bad.txt" in captured.out

    def test_print_summary_empty(self, capsys):
        print_summary(generated=[], skipped=[], errors=[])
        captured = capsys.readouterr()
        assert "Summary" in captured.out


class TestMainEntryPoint:

    def test_main_init_non_interactive(self, git_init):
        from osdlc.cli import main
        sys.argv = ["run.py", "init", "--non-interactive", "--target", git_init]
        result = main()
        assert result == 0

    def test_main_unknown_command(self, git_init):
        from osdlc.cli import main
        sys.argv = ["run.py", "unknown"]
        with pytest.raises(SystemExit):
            main()

    def test_main_defaults_to_init(self, git_init):
        from osdlc.cli import main
        sys.argv = ["run.py", "--non-interactive", "--target", git_init]
        result = main()
        assert result == 0

    def test_main_nonexistent_target(self):
        from osdlc.cli import main
        sys.argv = ["run.py", "init", "--non-interactive", "--target", r"C:\nonexistent_xyzzy"]
        result = main()
        assert result == 1

    def test_main_force_flag(self, git_init):
        from osdlc.cli import main
        sys.argv = ["run.py", "init", "--non-interactive", "--force", "--target", git_init]
        result = main()
        assert result == 0

    def test_main_force_short_flag(self, git_init):
        from osdlc.cli import main
        sys.argv = ["run.py", "init", "--non-interactive", "-f", "--target", git_init]
        result = main()
        assert result == 0

    def test_main_upgrade_non_scaffolded_fails(self, git_init):
        from osdlc.cli import main
        sys.argv = ["run.py", "upgrade", "--non-interactive", "--target", git_init]
        result = main()
        assert result == 1

    def test_main_upgrade_after_init_succeeds(self, git_init):
        from osdlc.cli import main
        sys.argv = ["run.py", "init", "--non-interactive", "--target", git_init]
        main()
        sys.argv = ["run.py", "upgrade", "--non-interactive", "--target", git_init]
        result = main()
        assert result == 0

    def test_main_upgrade_dry_run(self, git_init):
        from osdlc.cli import main
        sys.argv = ["run.py", "init", "--non-interactive", "--target", git_init]
        main()
        sys.argv = ["run.py", "upgrade", "--non-interactive", "--dry-run", "--target", git_init]
        result = main()
        assert result == 0

    def test_main_upgrade_print_summary(self, git_init):
        from osdlc.cli import main
        sys.argv = ["run.py", "init", "--non-interactive", "--target", git_init]
        main()
        sys.argv = ["run.py", "upgrade", "--non-interactive", "--target", git_init]
        result = main()
        assert result == 0
