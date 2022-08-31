
# Script contains functions to handle the clt
# input output paired with utils instance class

from concurrent.futures import ThreadPoolExecutor
from time import sleep, time
from ngoto.core.util.interface import commands, output, get_input
from ngoto.core.ngoto import Ngoto
from ngoto.core import constants as const
from ngoto.core.util.tasks import TaskController
from ngoto.core.util.load_scripts import load_scripts


class CLT(Ngoto):
    """ Command line tool class, containing CLT specifc methods """
    commands = []
    tasks = TaskController()

    def __init__(self):
        super().__init__()
        self.commands = load_scripts(const.command_path)

    def run_command(self, command: str, options: list = []) -> bool:
        check_commands = True
        if command in ['c', 'commands', 'h', 'help']:  # display commands
            commands(self.commands)
            check_commands = False
        elif command in ['t', 'task']:
            self.tasks.run_command(options)
            check_commands = False
        if check_commands:
            for cmd in self.commands:
                if command in cmd.get_actions() and (pos := cmd.perform_action(
                        self.curr_pos, options, self.logger)):
                    self.curr_pos = pos
                    return True
            return False
        else:
            return True

    def clt(self):
        """ CLT loop"""
        option = get_input('\n[Ngoto] > ').split()
        if not option:
            pass
        elif (isDigit := option[0].isdigit()) and (
                    num := int(option[0])-1) < self.curr_pos.num_children:
            option = ['openF', option[0]]
        elif isDigit and (
                    num < self.curr_pos.num_children +
                    self.curr_pos.num_plugins):
            option = ['openP', option[0]]
        if option != [] and not self.run_command(option[0], option):
            output("Unknown command")
        self.clt()

    def main(self) -> None:
        """ Main loop """
        with ThreadPoolExecutor(max_workers=3) as executor:
            clt_loop = executor.submit(self.clt)
            while True:
                curr_time = time()
                self.tasks.check_available_tasks(executor, curr_time, self.os)
                self.tasks.check_running_tasks(self.logger)
                if clt_loop.done():
                    break
                sleep(1 - (time() - curr_time))

    def start(self) -> None:
        """ Start CLT """
        self.run_command('clear')  # clear screen
        self.run_command('options')  # options screen
        self.main()
