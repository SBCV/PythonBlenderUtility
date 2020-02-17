# executes the module loader in blender
import os
import subprocess
from shutil import copyfile
from Utility.OS_Extension import get_first_valid_path
from Utility.Config import Config
from Utility.Logging_Extension import logger


# ====== Warning when starting blender ======
# "connect failed: No such file or directory"
# "Color management: using fallback mode for management"

# === "connect failed: No such file or directory"
#   IGNORE THIS MESSAGE, IT EVEN APPEARS IF BLENDER IS DIRECTLY CALLED FROM THE COMMANDLINE
#   This could be due to deleting blenders own python folder (THIS IS THE DEFAULT IN UBUNTU)
#

# === "Color management: using fallback mode for management"
#   IGNORE THIS MESSAGE
#   http://blender.stackexchange.com/questions/5436/how-do-i-solve-color-management-using-fallback-mode-for-management
#   This is normal but you can make this message go away by building with OpenColorIO.
# ====== ====== ====== ====== ====== ======


# ************************************************************************************
# ************ MAKE SURE YOU RUN THIS SCRIPT WITH A PYTHON 3 INTERPRETER ************
# ************************************************************************************


def execute_blender_script(blender_script_ifp,
                           background_mode=True,
                           path_to_blend_file=None,
                           debug_output=False):
    # ****
    # IF THE SCRIPT IS RUNNING IN FOREGROUND MODE NO PRINT INFORMATION
    # IS FLUSHED TO COMMAND LINE DURING EXECUTION
    # ****

    logger.info('execute_blender_script: ...')
    logger.vinfo('blender_script_ifp', blender_script_ifp)

    parent_dp = os.path.dirname(os.path.realpath(__file__))
    example_config_path = os.path.join(parent_dp, 'Config', 'blender_script_executor_example.cfg')
    config_path = os.path.join(parent_dp, 'Config', 'blender_script_executor.cfg')
    if not os.path.isfile(config_path):
        copyfile(example_config_path, config_path)

    blender_script_config = Config(path_to_config_file=config_path)
    path_to_blender_list = blender_script_config.get_option_value(
        'path_to_blender', list)
    path_to_blender = get_first_valid_path(
        path_to_blender_list)

    if path_to_blender is None:
        logger.info('No valid blender path provided!')
        logger.info('Adjust the value in Config/blender_script_executor.cfg')
        assert False

    options = []

    if path_to_blend_file is not None:
        logger.info('path_to_blend_file: ' + path_to_blend_file)
        options += [path_to_blend_file]

    if background_mode:
        options += ['--background']  # without gui

    # https://docs.blender.org/api/blender_python_api_2_61_release/info_tips_and_tricks.html#show-all-operators
    if debug_output:
        options += ['--debug']

    path_to_blender_scripts_parent_folder = os.path.dirname(os.path.realpath(__file__))

    # This calls the script Blender.BlenderUtility.Config_Blender_Environment.py,
    # which will add additional modules to the python path
    path_to_module_loader = os.path.join(
        path_to_blender_scripts_parent_folder, 'Blender_Library_Configuration.py')

    options += ['--python', path_to_module_loader]

    options += ['--python', blender_script_ifp]

    # options += ['--']  # this tells blender to treat the following arguments as custom arguments
    # options += ['--module_path_1', str('some_path')]

    logger.info('Call scripts in blender ... (' + path_to_blender + ')')
    subprocess.call([path_to_blender] + options)

    logger.info('execute_blender_script: Done')


