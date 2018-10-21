import bpy
from Utility.Logging_Extension import logger


def set_scene_keyframe_number(start_frame_number=1, end_frame_number=100):
    scn = bpy.context.scene
    scn.frame_start = start_frame_number
    scn.frame_end = end_frame_number


def _enclose_with_quotation_mark(some_string):
    return '"{0}"'.format(some_string)


def add_bone_constraint_keyframe(object_name,
                                 bone_name,
                                 constraint_name,
                                 frame_number,
                                 constraint_attribute_name,
                                 constraint_attribute_value):

    """
    https://docs.blender.org/api/blender_python_api_current/bpy.ops.ui.html#bpy.ops.ui.copy_data_path_button
        Copy the RNA data path for this property to the clipboard

    Adds a Keyframe to an ARBITRARY constraint attribute (-> constraint_attribute_name)

    :param object_name:
    :param bone_name:
    :param constraint_name:
    :param frame_number:
    :param constraint_attribute_name
    :param constraint_attribute_value:
    :return:
    """
    logger.info('add_bone_constraint_keyframe: ...')
    logger.vinfo('constraint_attribute_name', constraint_attribute_name)
    logger.vinfo('constraint_attribute_value', constraint_attribute_value)
    bpy.ops.object.mode_set(mode='POSE')
    # set_mode(active_object_name=object_name, mode='POSE', configure_scene_for_basic_ops=False)
    keyframe_object = bpy.data.objects[object_name]

    # bpy.ops.anim.change_frame(frame=frame_number)
    # bpy.context.object.pose.bones["MainControl"].constraints["Follow Path"].offset_factor = 0.01
    # bpy.context.object.keyframe_insert(
    #   data_path='pose.bones["MainControl"].constraints["Follow Path"].offset_factor', frame=1)

    # set the attribute to value
    setattr(keyframe_object.pose.bones[bone_name].constraints[constraint_name],
            constraint_attribute_name,
            constraint_attribute_value)

    keyframe_object.keyframe_insert(
        data_path='pose.bones[' + _enclose_with_quotation_mark(bone_name) + ']' +
                  '.constraints[' + _enclose_with_quotation_mark(constraint_name) + '].' +
                  constraint_attribute_name,
        frame=frame_number)

    bpy.ops.object.mode_set(mode='OBJECT')
    logger.info('add_bone_constraint_keyframe: Done')



