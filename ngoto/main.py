# script contains two main classes:
# OSINT (controls osint modules and api keys)  
# HazzahCLT (Controls Command line tool interface)

from ngoto.utilities import Workplace, Interface, Table, Node
from os.path import exists # check config file exists
import logging
import sys
import os
import json

class Ngoto:
    """ Contains API information aswell as OSINT modules """
    __version__ = '0.0.15'
    clearConsole = lambda self: os.system('cls' if os.name in ('nt', 'dos') else 'clear') 
    api_keys = {} # dict of api keys
    root = Node('root') # root plugin nodes

    def add_api(self, name, key):
        self.api_keys[name] = key
    def get_api(self, name):
        return self.api_keys[name]

class Module(Ngoto):
    """ Module class """

    def __init__(self):
        import requests
        if not exists('configuration/'):
            os.mkdir('configuration/')
        if not exists('configuration/plugin/'):
            os.mkdir('configuration/plugin/')
            
            # get current pre installed plugins into list
            modules = []
            url = 'https://github.com/HarryLudemann/Hazzah-OSINT/tree/main/configuration/plugin'
            open_tag = '<span class="css-truncate css-truncate-target d-block width-fit"><a class="js-navigation-open Link--primary" title="'
            r = requests.get(url)
            for line in r.text.split('\n'):
                if open_tag in line:
                    modules.append(line.replace(open_tag, '').split('"', 1)[0].strip())

            # download modules
            for module in modules:
                r = requests.get('https://raw.githubusercontent.com/HarryLudemann/Hazzah-OSINT/main/configuration/plugin/' + module.lower())
                with open(f'configuration/plugin/{module.lower()}.py', 'w') as f:
                    f.write(r.text)
        # load plugins
        for file in os.listdir("configuration/plugin/"): 
            if file.endswith(".py"):    # if python script
                mod = __import__('configuration.plugin.' + file[:-3], fromlist=['Plugin'])
                plugin = getattr(mod, 'Plugin')()
                new_node = Node(plugin.name)
                new_node.set_plugin( plugin )
                self.root.add_child( new_node )
            if '.' not in file:         # if folder
                pass

    # def get_plugin_context(self, plugin_name, args):
    #     """ Get context from plugin, given plugin name & list of args """
    #     return self.get_plugin(plugin_name)().get_context(args)

class CLT(Ngoto):
    """ Command line tool class """
    current_pos = "[Ngoto]"
    current_workplace = "None" # Name
    workplace = None # current workplace object
    file_path ='configuration/workplace/' # workplace file path
    interface = Interface()

    def load_config(self):
        """ Loads plugins from plugins directory """
        # check Configuration, workplace and plugins folder exist else create
        if not exists('configuration/'):
            os.mkdir('configuration/')
        if not exists('configuration/workplace/'):
            os.mkdir('configuration/workplace/')
        if not exists('configuration/plugin/'):
            os.mkdir('configuration/plugin/')
        # load config file of api keys and set
        if exists('configuration/config.json'):
            with open("configuration/config.json") as json_data_file:
                data = json.load(json_data_file)
                for name in data['API']:
                    self.add_api(name, data['API'][name])
        else:
            logging.warning("No config.json found")

        self.load_config_helper(self.root, "configuration/plugin/")

        #self.print_nodes(self.root)


    def load_config_helper(self, curr_node, file_path):
        """ load config recursive helper method """
        for file in os.listdir(file_path): 
            if file.endswith(".py"):    # if python script
                print( str(curr_node.num_children), curr_node.name, file_path + file)
                mod = __import__(file_path.replace('/', '.') + file[:-3], fromlist=['Plugin'])
                plugin = getattr(mod, 'Plugin')()
                new_node = Node(plugin.name)
                new_node.set_plugin( plugin )
                curr_node.add_child( new_node )
            elif '__pycache__' not in file:         # if folder
                print( str(curr_node.num_children), curr_node.name, file_path + file)
                new_node = Node(file + '/')
                curr_node.add_child( self.load_config_helper(new_node, 'configuration/plugin/' + file + '/') )
        return curr_node

    def print_nodes(self, node, indent=''):
        for child in node.get_children():
            print(indent + child.name)


    # Workplace command method
    def workplace_command(self, options):
        """ determines requested wp option, given list of options """
        if len(options) >= 2:
            if options[1] == 'create':  # create wp
                self.workplace = Workplace(self.file_path)
                self.current_workplace = options[2]
                self.workplace.create_workplace(options[2])
                self.interface.output(f"Successfully created {options[2]} workplace")
            elif options[1] == 'join':
                self.workplace = Workplace(self.file_path)
                self.current_workplace = options[2]
                self.workplace.run_command(options[2], '')  # test connection to db
                self.interface.output(f"Successfully joined {options[2]} workplace")
            elif options[1] == 'setup':
                query = ''
                for plugin in self.plugins:
                    plugin = plugin()
                    query += '\n' + plugin.create_table()
                self.workplace.run_script(self.current_workplace, query)  # test connection to db
                self.interface.output(f"Successfully setup {self.current_workplace} workplace tables")
            elif options[1] == 'delete':
                file_exists = exists(f"{self.file_path}{options[2]}.sqlite")
                if file_exists:
                    os.remove(f"{self.file_path}{options[2]}.sqlite")
                    self.workplace = None
                    self.current_workplace = "None"
                    logging.info(f"Deleted workplace {options[2]}")
                    self.interface.output(f"Successfully deleted {options[2]} workplace")
                else:
                    logging.warning("Workplace already does not exist")
            elif options[1] == 'leave':  # create wp
                self.workplace = None
                self.current_workplace = ''
                self.interface.output(f"Successfully left workplace")
        else:
            logging.warning("No such command")

    def save_to_workplace(self, context, plugin_name):
        """ Saves context dict to given plugins name table in current workplace if any
        either adds all vars in context to array, or if item is array creates row of that array """
        values = []
        added_row = False
        first_var = True
        for name in context:
            if first_var and type(context[name]) == list:
                added_row = True
                for item in context[name]:
                    self.workplace.add_row(self.current_workplace, plugin_name, [item])
            else:
                values.append(context[name])
            first_var = False
        if not added_row:
            self.workplace.add_row(self.current_workplace, plugin_name, values)

    # main operation function to start
    def main(self):
        context = {}                  
        option = self.interface.get_input('', '', self.current_pos)
        if option not in ['1', '2', '3', '4', '5']:   # if option is command not plugin/module
            option = option.split()
            if not option: # if empty string 
                pass
            elif option[0] in ['wp', 'workplace']:
                self.workplace_command(option)
            elif option[0] in ['o', 'options']:
                self.interface.options(self.current_workplace, self.root)
            elif option[0] in ['c', 'commands']:
                self.interface.commands()
            elif option[0] in ['cls', 'clear']:
                self.clearConsole()
            elif option[0] in ['0', 'exit']:
                sys.exit()
            else:
                self.interface.output("Unknown command")
        else:   # must be osint function
            # load and call plugin
            plugin = self.root.get_child( int(option[0]) - 1 ).get_plugin()
            context = plugin.main(self)
            plugin.print_info(self, context, Table())

            if self.workplace: # save if within workplace
                self.save_to_workplace(context, plugin.name)

        self.main()