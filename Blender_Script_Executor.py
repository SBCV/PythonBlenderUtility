# executes the module loader in blender
import os
import subprocess
from Utility.OS_Extension import get_first_valid_path
from Utility.Config import Config

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

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


def execute_blender_script(path_and_name_to_script_file,
                           path_to_execute_config,
                           background_mode=True,
                           path_to_blend_file=None,
                           debug_output=False):
    # ****
    # IF THE SCRIPT IS RUNNING IN FOREGROUND MODE NO PRINT INFORMATION
    # IS FLUSHED TO COMMAND LINE DURING EXECUTION
    # ****

    execute_config = Config(path_to_config_file=path_to_execute_config)
    path_to_blender = get_first_valid_path(
        execute_config.get_option_value(
            'path_to_blender', list)
    )

    options = []

    if path_to_blend_file is not None:
        logger.info('path_to_blend_file: ' + path_to_blend_file)
        options += [path_to_blend_file]

    if background_mode:
        options += ['--background']  # without gui

    # https://docs.blender.org/api/blender_python_api_2_61_release/info_tips_and_tricks.html#show-all-operators
    if debug_output:
        options += ['--debug']

    path_to_blender_scripts_parent_folder = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    # This calls the script Blender.BlenderUtility.Config_Blender_Environment.py,
    # which will add additional modules to the python path
    path_to_module_loader = os.path.join(
        path_to_blender_scripts_parent_folder, 'BlenderUtility', 'Config_Blender_Environment.py')
    options += ['--python', path_to_module_loader]

    path_to_blender_script = os.path.join(
        path_to_blender_scripts_parent_folder, path_and_name_to_script_file)
    options += ['--python', path_to_blender_script]

    # options += ['--']  # this tells blender to treat the following arguments as custom arguments
    # options += ['--module_path_1', str('some_path')]

    print('Call scripts in blender ... (' + path_to_blender + ')')
    subprocess.call([path_to_blender] + options)




