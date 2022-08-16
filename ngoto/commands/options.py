# contains function to show options
from ngoto.core.util.command import CommandBase
from ngoto.core.util.interface import options
import os


class Options(CommandBase):
    def get_description(self):
        return "Show plugins/options"

    def get_actions(self):
        return ['o', 'options', 'ls']

    def perform_action(self, *args):
        os.system('cls' if os.name in ('nt', 'dos') else 'clear')
        options(args[0])
        args[2].debug('Showing options', program='Options')
        return args[0]
