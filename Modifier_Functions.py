import bpy
from BlenderUtility.Ops_Functions import configure_scene_for_basic_ops


def apply_modifiers(target_modifier_list):
    """
    Applies only modiefies - NO CONSTRAINTS
    :param input_blender_file_path:
    :param output_blender_file_path:
    :param target_modifier_list:
    :return:
    """

    configure_scene_for_basic_ops()  # IMPORTANT TO AVOID POLL ERRORS

    bpy.ops.object.select_all(action='DESELECT')

    for obj in bpy.data.objects:
        obj.select = True
        bpy.context.scene.objects.active = obj

        # Make sure to use the correct order of the modifiers
        # (otherwise the application may result in an unexpected behaviour)
        for target_modifier_name in obj.modifiers:
            if target_modifier_name in target_modifier_list:
                # Make data single user copy - otherwise modifiers cannot be applied
                if obj.data.users > 1:
                    obj.data = obj.data.copy()
                bpy.ops.object.modifier_apply(
                    apply_as='DATA', modifier=target_modifier_name)
        obj.select = False
