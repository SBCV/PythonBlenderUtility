import os
import sys
from shutil import copyfile

# ************************************************************************************
# ************ MAKE SURE YOU RUN THIS SCRIPT WITH A PYTHON 3 INTERPRETER ************
# ************************************************************************************

DEFAULT = 'DEFAULT'
ANACONDA = 'ANACONDA'

def add_paths_to_system_path_if_necessary(some_paths):
    for some_path in some_paths:
        if some_path not in sys.path:
            print("Appending to PYTHONPATH: " + str(some_path))
            sys.path.append(some_path)
        else:
            print("Found the following path already in PYTHONPATH" + str(some_path))


def configure_libs_for_blender():
    """
    This method is called by "Blender_Script_Executor"
    :return:
    """

    # Add the parent folder of the BlenderUtility to the python path
    # in order to enable acess the BlenderUtility package and all subpackages (e.g. Utility)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

    from Utility.Logging_Extension import logger
    from Utility.Config import Config

    additional_system_paths = []

    parent_dp = os.path.dirname(os.path.realpath(__file__))
    example_config_path = os.path.join(parent_dp, 'Config', 'blender_script_executor_example.cfg')
    config_path = os.path.join(parent_dp, 'Config', 'blender_script_executor.cfg')
    if not os.path.isfile(config_path):
        copyfile(example_config_path, config_path)

    blender_script_config = Config(path_to_config_file=config_path)
    custom_paths = blender_script_config.get_option_value(
        'custom_paths', list)

    additional_system_paths += custom_paths

    python_type = blender_script_config.get_option_value(
        'python_type', str)

    assert python_type in [DEFAULT, ANACONDA]

    if python_type == DEFAULT:
        logger.info('Adding Default Python Paths to Blender Executable (No Anaconda Paths)')
        python_sys_path_default_list = blender_script_config.get_option_value(
            'python_sys_path_default', list)
        additional_system_paths += python_sys_path_default_list

        python_sys_path_local_list = blender_script_config.get_option_value(
            'python_sys_path_local', list)
        additional_system_paths += python_sys_path_local_list

    elif python_type == ANACONDA:

        logger.info('Adding ANACONDA3 Paths to Blender Executable')
        python_anaconda_path_list = blender_script_config.get_option_value(
            'python_anaconda_path', list)
        additional_system_paths += python_anaconda_path_list
    else:
        assert False

    add_paths_to_system_path_if_necessary(additional_system_paths)

    # print('Current System Path is: ' + str(sys.path))


if __name__ == '__main__':
    configure_libs_for_blender()

