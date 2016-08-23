import sublime
import sublime_plugin
import os
import os.path
import subprocess

# Borrowed from http://bit.ly/1iDl6f6
def current_dir(window):
    """
    Return the working directory in which the window's commands should run.

    In the common case when the user has one folder open, return that.
    Otherwise, return one of the following (in order of preference):
        1) One of the open folders, preferring a folder containing the active
           file.
        2) The directory containing the active file.
        3) The user's home directory.
    """
    active_view = window.active_view()
    active_file_name = active_view.file_name() if active_view else None
    if active_file_name:
    	return active_file_name
    else:
    	folders = window.folders()
    	if len(folders):
    		return folders[0];


def get_path(paths, window):
	if paths:
		return paths[0]
	else:
		return current_dir(window)


def get_dir(paths, window):
	dir = get_path(paths, window)
	if not dir:
		return
	if os.path.isfile(dir):
		dir = os.path.dirname(dir)
	return dir;


class TortoiseGITBashCommand(sublime_plugin.WindowCommand):
	def run(self, paths=None, isHung=False):
		# dir = current_dir(self.window)
		dir = get_dir(paths, self.window)
		if not dir:
			return

		# sublime.error_message(dir)
		settings = sublime.load_settings('TortoiseGIT.sublime-settings')
		gitbash_path = settings.get('gitbash_path')

		if not os.path.isfile(gitbash_path):
			sublime.error_message(''.join(['can\'t find sh.exe (gitbash),',
				' please config setting file', '\n   --sublime-TortoiseGIT']))
			raise

		proce = subprocess.Popen([gitbash_path], cwd=dir)
		# subprocess.open(gitbash_path)
		# command = 'cd %s & "%s" --login -i' % (dir, gitbash_path)
		# os.system(command)


class TortoiseGITCommand(sublime_plugin.WindowCommand):
	def run(self, cmd, paths=None, isHung=False):
		dir = get_path(paths, self.window)

		if not dir:
			return

		sublime.error_message(dir)
		settings = sublime.load_settings('TortoiseGIT.sublime-settings')
		tortoisegit_path = settings.get('tortoisegit_path')

		if not os.path.isfile(tortoisegit_path):
			sublime.error_message(''.join(['can\'t find TortoiseGitProc.exe,',
				' please config setting file', '\n   --sublime-TortoiseGIT']))
			raise

		proce = subprocess.Popen('"' + tortoisegit_path + '"' +
			' /command:' + cmd + ' /path:"%s"' % dir , stdout=subprocess.PIPE)

		# This is required, cause of ST must wait TortoiseGIT update then revert
		# the file. Otherwise the file reverting occur before SVN update, if the
		# file changed the file content in ST is older.
		if isHung:
			proce.communicate()


class MutatingTortoiseGITCommand(TortoiseGITCommand):
	def run(self, cmd, paths=None):
		TortoiseGITCommand.run(self, cmd, paths, True)

		self.view = sublime.active_window().active_view()
		row, col = self.view.rowcol(self.view.sel()[0].begin())
		self.lastLine = str(row + 1);
		sublime.set_timeout(self.revert, 100)

	def revert(self):
		self.view.run_command('revert')
		sublime.set_timeout(self.revertPoint, 600)

	def revertPoint(self):
		self.view.window().run_command('goto_line',{'line':self.lastLine})


class GitCloneCommand(MutatingTortoiseGITCommand):
	def run(self, paths=None):
		settings = sublime.load_settings('TortoiseGIT.sublime-settings')
		closeonend = ('3' if True == settings.get('autoCloseUpdateDialog') else '0')
		MutatingTortoiseGITCommand.run(self, 'clone /closeonend:' + closeonend, paths)


class GitCommitCommand(TortoiseGITCommand):
	def run(self, paths=None):
		TortoiseGITCommand.run(self, 'commit /closeonend:3', paths)


class GitCheckoutCommand(TortoiseGITCommand):
	def run(self, paths=None):
		TortoiseGITCommand.run(self, 'checkout /closeonend:3', paths)


class GitPushCommand(TortoiseGITCommand):
	def run(self, paths=None):
		TortoiseGITCommand.run(self, 'push /closeonend:3', paths)


class GitPullCommand(TortoiseGITCommand):
	def run(self, paths=None):
		TortoiseGITCommand.run(self, 'pull /closeonend:3', paths)


class GitBashCommand(TortoiseGITBashCommand):
	def run(self, paths=None):
		TortoiseGITBashCommand.run(self, paths)


class GitRevertCommand(MutatingTortoiseGITCommand):
	def run(self, paths=None):
		MutatingTortoiseGITCommand.run(self, 'revert', paths)


class GitLogCommand(TortoiseGITCommand):
	def run(self, paths=None):
		TortoiseGITCommand.run(self, 'log', paths)


class GitDiffCommand(TortoiseGITCommand):
	def run(self, paths=None):
		TortoiseGITCommand.run(self, 'diff', paths)


class GitBlameCommand(TortoiseGITCommand):
	def run(self, paths=None):
		view = sublime.active_window().active_view()
		row = view.rowcol(view.sel()[0].begin())[0] + 1

		TortoiseGITCommand.run(self, 'blame /line:' + str(row), paths)

	def is_visible(self, paths=None):
		file = self.getPath(paths)
		return os.path.isfile(file) if file else False

