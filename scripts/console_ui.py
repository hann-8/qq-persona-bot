"""Small line-input console UI; redirected input/output never gets terminal controls."""
import os
import subprocess
import sys


class Console:
    def __init__(self, read=None, write=None, interactive=None):
        self.read = read or input
        self.write = write or print
        try:
            self.interactive = (sys.stdin.isatty() and sys.stdout.isatty()) if interactive is None else interactive
        except (AttributeError, OSError):
            self.interactive = False

    def clear(self):
        if not self.interactive:
            return
        if os.name == 'nt':
            try:
                result = subprocess.run(['cmd.exe', '/d', '/c', 'cls'], check=False)
                if result.returncode:self.interactive = False
            except OSError:
                self.interactive = False
        else:
            self.write('\033[2J\033[H', end='', flush=True)

    def page(self, title):
        self.clear()
        self.write(title + '\n')

    def choose(self, choices):
        while True:
            choice = self.read('请选择编号：').strip()
            if choice in choices:
                return choice
            self.write('请输入页面上列出的编号。')

    def pause(self):
        self.read('\n按回车返回：')
