import platform
import sys

# ************************************************************************************
# ************ MAKE SURE YOU RUN THIS SCRIPT WITH A PYTHON 3 INTERPRETER ************
# ************************************************************************************

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

DEFAULT = 'default'
ANACONDA3 = 'anaconda3'


def add_paths_to_system_path_if_necessary(some_paths):
    for some_path in some_paths:
        if some_path not in sys.path:
            logger.info("Appending to PYTHONPATH: " + str(some_path))
            sys.path.append(some_path)
        else:
            logger.info("Found the following path already in PYTHONPATH" + str(some_path))


def configure_libs_for_blender(python_type=ANACONDA3):
    """
    This method is called by "Blender_Script_Executor"
    :return:
    """

    if platform.system() == 'Windows':
        simple_utility_tool_dir = r'F:\SimpleUtilityTools\SimpleUtilityTools'
        new_system_paths = [simple_utility_tool_dir]
    else:
        logger.info('Adding Thesis Path to Blender Executable')
        add_paths_to_system_path_if_necessary(['/mnt/DataSSD/Thesis'])

        if python_type == DEFAULT:
            logger.info('Adding Default Python Paths to Blender Executable (No Anaconda Paths)')
            python_sys_path_default = '/usr/lib/python3/dist-packages'
            python_sys_path_local = '/usr/local/lib/python3.4/dist-packages'
            new_system_paths = [python_sys_path_default, python_sys_path_local]
        elif python_type == ANACONDA3:
            logger.info('Adding ANACONDA3 Paths to Blender Executable')
            python_sys_path_default = '/home/sebastian/anaconda3/lib/python3.5/site-packages'
            new_system_paths = [python_sys_path_default]
        else:
            assert False

    add_paths_to_system_path_if_necessary(new_system_paths)

    # print('Current System Path is: ' + str(sys.path))


if __name__ == '__main__':
    configure_libs_for_blender()

