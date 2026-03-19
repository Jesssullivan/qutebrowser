# SPDX-FileCopyrightText: Freya Bruhin (The Compiler) <mail@qutebrowser.org>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import os

import pytest
from qutebrowser.qt.core import Qt

from qutebrowser.mainwindow import prompt as promptmod
from qutebrowser.utils import usertypes


class TestPasswordPrompt:

    @pytest.fixture
    def prompt(self, qtbot, config_stub, key_config_stub):
        config_stub.val.bindings.default = {}
        question = usertypes.Question()
        question.title = "Enter PIN"
        question.mode = usertypes.PromptMode.pwd
        p = promptmod.PasswordPrompt(question)
        qtbot.add_widget(p)
        return p

    def test_echo_mode(self, prompt):
        """Password prompt should mask input."""
        from qutebrowser.qt.widgets import QLineEdit
        assert prompt._lineedit.echoMode() == QLineEdit.EchoMode.Password

    def test_accept_value(self, prompt):
        """Accept with explicit value."""
        assert prompt.accept("1234") is True
        assert prompt.question.answer == "1234"

    def test_accept_typed(self, prompt, qtbot):
        """Accept with typed text."""
        prompt._lineedit.setText("mypin")
        assert prompt.accept() is True
        assert prompt.question.answer == "mypin"


class TestSelectPrompt:

    @pytest.fixture
    def prompt(self, qtbot, config_stub, key_config_stub):
        config_stub.val.bindings.default = {}
        question = usertypes.Question()
        question.title = "Select account"
        question.mode = usertypes.PromptMode.select
        question.choices = ["alice@example.com", "bob@example.com", "carol@example.com"]
        p = promptmod.SelectPrompt(question)
        qtbot.add_widget(p)
        return p

    def test_numeric_selection(self, prompt):
        """Select by 1-based numeric index."""
        assert prompt.accept("1") is True
        assert prompt.question.answer == "alice@example.com"

    def test_numeric_selection_last(self, prompt):
        """Select last item by index."""
        assert prompt.accept("3") is True
        assert prompt.question.answer == "carol@example.com"

    def test_string_match(self, prompt):
        """Select by exact string match."""
        assert prompt.accept("bob@example.com") is True
        assert prompt.question.answer == "bob@example.com"

    def test_invalid_index(self, prompt, caplog):
        """Reject out-of-range index."""
        with caplog.at_level(logging.ERROR, 'message'):
            assert prompt.accept("0") is False
            assert prompt.accept("4") is False

    def test_invalid_string(self, prompt, caplog):
        """Reject string not in choices."""
        with caplog.at_level(logging.ERROR, 'message'):
            assert prompt.accept("nobody@example.com") is False


class TestFileCompletion:

    @pytest.fixture
    def get_prompt(self, qtbot, config_stub, key_config_stub):
        """Get a function to display a prompt with a path."""
        config_stub.val.bindings.default = {}

        def _get_prompt_func(path):
            question = usertypes.Question()
            question.title = "test"
            question.default = path

            prompt = promptmod.DownloadFilenamePrompt(question)
            qtbot.add_widget(prompt)
            with qtbot.wait_signal(prompt._file_model.directoryLoaded):
                pass
            assert prompt._lineedit.text() == path

            return prompt
        return _get_prompt_func

    @pytest.mark.parametrize('steps, where, subfolder', [
        (1, 'next', 'a'),
        (1, 'prev', 'c'),
        (2, 'next', 'b'),
        (2, 'prev', 'b'),
    ])
    def test_simple_completion(self, tmp_path, get_prompt, steps, where,
                               subfolder):
        """Simply trying to tab through items."""
        testdir = tmp_path / 'test'
        for directory in 'abc':
            (testdir / directory).mkdir(parents=True)

        prompt = get_prompt(str(testdir) + os.sep)

        for _ in range(steps):
            prompt.item_focus(where)

        assert prompt._lineedit.text() == str((testdir / subfolder).resolve())

    def test_backspacing_path(self, qtbot, tmp_path, get_prompt):
        """When we start deleting a path we want to see the subdir."""
        testdir = tmp_path / 'test'

        for directory in ['bar', 'foo']:
            (testdir / directory).mkdir(parents=True)

        prompt = get_prompt(str(testdir / 'foo') + os.sep)

        # Deleting /f[oo/]
        with qtbot.wait_signal(prompt._file_model.directoryLoaded):
            for _ in range(3):
                qtbot.keyPress(prompt._lineedit, Qt.Key.Key_Backspace)

        # For some reason, this isn't always called when using qtbot.keyPress.
        prompt._set_fileview_root(prompt._lineedit.text())

        # 'foo' should get completed from 'f'
        prompt.item_focus('next')
        assert prompt._lineedit.text() == str(testdir / 'foo')

        # Deleting /[foo]
        for _ in range(3):
            qtbot.keyPress(prompt._lineedit, Qt.Key.Key_Backspace)

        # We should now show / again, so tabbing twice gives us bar -> foo
        prompt.item_focus('next')
        prompt.item_focus('next')
        assert prompt._lineedit.text() == str(testdir / 'foo')

    @pytest.mark.parametrize("keys, expected", [
        ([], ['bar', 'bat', 'foo']),
        ([Qt.Key.Key_F], ['foo']),
        ([Qt.Key.Key_A], ['bar', 'bat']),
    ])
    def test_filtering_path(self, qtbot, tmp_path, get_prompt, keys, expected):
        testdir = tmp_path / 'test'

        for directory in ['bar', 'foo', 'bat']:
            (testdir / directory).mkdir(parents=True)

        prompt = get_prompt(str(testdir) + os.sep)
        for key in keys:
            qtbot.keyPress(prompt._lineedit, key)
        prompt._set_fileview_root(prompt._lineedit.text())

        num_rows = prompt._file_model.rowCount(prompt._file_view.rootIndex())
        visible = []
        for row in range(num_rows):
            parent = prompt._file_model.index(
                os.path.dirname(prompt._lineedit.text()))
            index = prompt._file_model.index(row, 0, parent)
            if not prompt._file_view.isRowHidden(index.row(), index.parent()):
                visible.append(index.data())
        assert visible == expected

    @pytest.mark.linux
    def test_root_path(self, get_prompt):
        """With / as path, show root contents."""
        prompt = get_prompt('/')
        assert prompt._file_model.rootPath() == '/'
