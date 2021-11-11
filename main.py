# this script is to launch command line tool
import logging
import traceback
from ngoto import CLT

if __name__ == '__main__':
    hz = CLT()
    try:
        hz.load_config()
        hz.clearConsole()
        hz.interface.options(hz.curr_workplace, hz.root)
        hz.main()
    except Exception as e:
        print(f"{hz.interface.bcolors.ENDC}")
        logging.error(traceback.format_exc())
    finally:
        print(f"{hz.interface.bcolors.ENDC}")
        