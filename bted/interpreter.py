import sys
from os import system, path, popen
import subprocess
from .token_tree import TokenTree
import bted.definitions as definitions
from .arg_process import process_args


class Interpreter:
    accepted_flags = {'-t'}

    def __init__(self, command_tree_file, translations_file):
        self.tree = TokenTree.from_json(command_tree_file, translations_file)

    def print_commands(self):
        print("Supported commands:", file=sys.stderr)
        for k in self.tree.command_translations:
            print(' >', k, file=sys.stderr)

    def build_command(self, command_args, file_arg) -> (str, [str]):
        if file_arg is None:
            file_arg = ''
        cmd_statement, flags = process_args(command_args)
        unsupported_flags = [f for f in flags if f not in Interpreter.accepted_flags]
        if len(unsupported_flags) > 0:
            print('Invalid flags:', unsupported_flags, file=sys.stderr)
            return None, None

        # tree.print_command_tree()
        cmd, user_text_inputs = self.tree.validate_command(cmd_statement)
        if cmd is None:
            return None, None
        args = [file_arg] + user_text_inputs
        cmd = cmd.format(*args)
        return cmd, flags

    @classmethod
    def execute_command(cls, cmd, flags, return_output=False, stdin=sys.stdin):
        res = None
        translation_only = '-t' in flags
        if translation_only:
            print('Translation:\n >', cmd)
        else:
            # if return_output:
            #     with popen(cmd) as fout:
            #         return fout.read()
            stdout = subprocess.PIPE if return_output else None
            with subprocess.Popen(cmd, shell=True, stdout=stdout, stdin=stdin) as p:
                try:
                    # exit_code = subprocess.call(cmd, shell=True, stdout=stdout)
                    exit_code = p.wait()
                    if exit_code < 0:
                        print("Child was terminated by signal", -exit_code, file=sys.stderr)
                except OSError as e:
                    print("Execution failed:", e, file=sys.stderr)
                if return_output:
                    res = p.stdout
        return res


def default_interpreter():
    command_tree_fp = definitions.COMMAND_TOKEN_TREE
    translations_fp = definitions.COMMAND_TRANSLATIONS_FILE
    return Interpreter(command_tree_fp, translations_fp)


def print_commands():
    default_interpreter().print_commands()


def main():
    if len(sys.argv) < 2:
        print('Insufficient arguments. Format: \'bted <input-file> <command statement>\'\n'
              'Examples: \n'
              '> bted example.txt delete lines starting with "example Phrase"\n'
              '> bted example.txt select lines containing Andrew\n'
              '> bted example.txt prepend beat with "Don\'t stop the "', file=sys.stderr)
        exit(1)

    # std_in = None
    # if sys.stdin is not None:
    #     file_arg = None
    #     command_args = sys.argv[1:]
    #     std_in = sys.stdin
    file_arg = None
    if path.exists(sys.argv[1]):
        file_arg = sys.argv[1]
        command_args = sys.argv[2:]
    elif path.exists(sys.argv[-1]):
        file_arg = sys.argv[-1]
        command_args = sys.argv[1:-1]
    else:
        # print('File not found. Reading from standard input.', file=sys.stderr)
        command_args = sys.argv[1:]

    interpreter = default_interpreter()
    cmd, flags = interpreter.build_command(command_args, file_arg)
    if cmd is not None:
        interpreter.execute_command(cmd, flags)
    else:
        print('Invalid command.', file=sys.stderr)
