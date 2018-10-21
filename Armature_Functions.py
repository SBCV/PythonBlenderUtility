import bpy
from mathutils import Vector
from BlenderUtility.Object_Functions import add_empty
from BlenderUtility.Object_Functions import get_object_bounding_box_center
from BlenderUtility.Ops_Functions import set_mode
from Utility.Logging_Extension import logger


# ============= IMPORTANT ==================
# Three ways to add an armature
# https://wiki.blender.org/index.php/Dev:Py/Scripts/Cookbook/Code_snippets/Three_ways_to_create_objects

# Armature Examples
# https://wiki.blender.org/index.php/Dev:Py/Scripts/Cookbook/Code_snippets/Armatures
# ============= ==================

# *************** Tripping Bone Hazzards ***************
# https://docs.blender.org/api/blender_python_api_2_75_0/info_gotcha.html#editbones-posebones-bone-bones
# https://docs.blender.org/api/blender_python_api_2_75_0/info_gotcha.html#edit-bones
# https://docs.blender.org/api/blender_python_api_2_75_0/info_gotcha.html#bones-object-mode
# https://docs.blender.org/api/blender_python_api_2_75_0/info_gotcha.html#pose-bones
# Note
#   Notice the pose is accessed from the object rather than the object data, this is why blender can have 2 or
#   more objects sharing the same armature in different poses.
# Note
#   Strictly speaking PoseBone’s are not bones, they are just the state of the armature, stored in the
#   bpy.types.Object rather than the bpy.types.Armature, the real bones are however accessible
#   from the pose bones - bpy.types.PoseBone.bone
# *********************************************


class ConstraintTypes:
    IK = 'IK'
    DAMPED_TRACK = 'DAMPED_TRACK'
    LOCKED_TRACK = 'LOCKED_TRACK'
    TRANSFORM = 'TRANSFORM'
    FOLLOW_PATH = 'FOLLOW_PATH'


def create_armature_from_data(name_stem, origin, object_suffix='_obj', data_suffix='_data'):
    # Create armature and object
    armature_data = bpy.data.armatures.new(name_stem + data_suffix)
    armature_object = bpy.data.objects.new(name_stem + object_suffix, armature_data)
    armature_object.location = origin
    armature_object.show_x_ray = True
    armature_object.show_name = True

    # Link object to scene and make active
    scn = bpy.context.scene
    scn.objects.link(armature_object)
    scn.objects.active = armature_object
    armature_object.select = True

    return armature_object.name


def create_armature_from_operator(name_stem, origin, object_suffix='_obj', data_suffix='_data'):
    bpy.ops.object.add(
        type='ARMATURE',
        enter_editmode=True,
        location=origin)
    armature_object = bpy.context.object
    armature_object.name = name_stem + object_suffix
    armature_object.show_x_ray = True
    armature_object.show_name = True
    armature_object.data.name = name_stem + data_suffix

    bpy.ops.object.mode_set(mode='OBJECT')
    return armature_object.name


def create_armature_from_primitive(name_stem, origin, object_suffix='_obj', data_suffix='_data'):
    bpy.ops.object.armature_add()
    bpy.ops.transform.translate(value=origin)
    armature_object = bpy.context.object
    armature_object.name = name_stem + object_suffix
    armature_object.show_name = True
    armature_data = armature_object.data
    armature_data.name = name_stem + data_suffix
    return armature_object.name


def add_bone_to_armature_at_object_center(armature_object_name, bone_name, target_object_name, front_axis_vector):
    target_obj = bpy.data.objects[target_object_name]
    center = get_object_bounding_box_center(target_obj.name)
    add_bone_to_armature(armature_object_name,
                         bone_name,
                         bone_head_pos=center,  # local coordinates
                         bone_tail_pos=center + front_axis_vector,
                         world_coordinates=True)  # local coordinates


def add_bone_to_armature(armature_object_name,
                         bone_name,
                         bone_head_pos,
                         bone_tail_pos,
                         world_coordinates=False):  # set to true, to use world coordinates

    """

    :param armature_object_name:
    :param bone_name:
    :param bone_head_pos: in local or world coordinates (point which is attached to parent)
    :param bone_tail_pos: in local or world coordinates
    :param world_coordinates
    :return:
    """

    logger.info('add_bone_to_armature: ...')

    # https://docs.blender.org/api/blender_python_api_2_75_0/info_gotcha.html#editbones-posebones-bone-bones

    set_mode(active_object_name=armature_object_name, mode='EDIT', configure_scene_for_basic_ops=False)

    # if parent_bone is not None:
    #     armature_object.data.bones[parent_bone.name].select = True

    armature_object = bpy.data.objects[armature_object_name]

    # Create single bone
    bone = armature_object.data.edit_bones.new(bone_name)

    # https://docs.blender.org/api/blender_python_api_current/bpy.types.Object.html#bpy.types.Object.matrix_world
    if world_coordinates:
        world_to_object_matrix = armature_object.matrix_world.inverted()
        bone_head_pos = (world_to_object_matrix * bone_head_pos.to_4d()).to_3d()
        bone_tail_pos = (world_to_object_matrix * bone_tail_pos.to_4d()).to_3d()

    bone.head = bone_head_pos
    bone.tail = bone_tail_pos

    # logger.info('parent_bone')
    # logger.info(parent_bone)

    # if parent_bone is not None:
    #     bone.parent = parent_bone
    #     # Connect this bone with its parent (or not)
    #     # (i.e. moving parent/child moves also child/parent)
    #     bone.use_connect = use_connect

    # https://docs.blender.org/api/blender_python_api_2_75_0/info_gotcha.html#armature-mode-switching
    #   While writing scripts that deal with armatures you may find you have to switch between modes,
    #   when doing so take care when switching out of editmode not to keep references to the edit-bones or
    #   their head/tail vectors. Further access to these will crash blender so its important the script clearly
    #   separates sections of the code which operate in different modes.

    bpy.ops.object.mode_set(mode='OBJECT')

    logger.info('add_bone_to_armature: Done')


def set_bone_parent(armature_object_name,
                    child_bone_name,
                    parent_bone_name,
                    connected=False,
                    inherit_rotation=True,
                    inherit_scale=True):

    logger.info('set_bone_parent: ...')

    set_mode(active_object_name=armature_object_name, mode='EDIT', configure_scene_for_basic_ops=False)
    # bpy.ops.object.mode_set(mode='EDIT')    # TODO use set_mode

    armature_object = bpy.data.objects[armature_object_name]
    armature_object.data.edit_bones[child_bone_name].parent = armature_object.data.edit_bones[parent_bone_name]
    armature_object.data.edit_bones[child_bone_name].use_connect = connected
    armature_object.data.edit_bones[child_bone_name].use_inherit_rotation = inherit_rotation
    armature_object.data.edit_bones[child_bone_name].use_inherit_scale = inherit_scale

    # armature_object.data.edit_bones[child_bone_name].parent = armature_object.data.edit_bones[parent_bone_name]
    bpy.ops.object.mode_set(mode='OBJECT')

    logger.info('set_bone_parent: Done')


def set_bone_head_tail(armature_object_name, bone_name, head_location=None, tail_location=None):

    """ A CHILD is attached with its HEAD to the TAIL of the PARENT """

    logger.info('set_bone_head_tail: ...')

    # ===================
    # If head_location and tail_location is set to the same value, THE BONE DISAPPEARS
    # ===================
    assert not head_location == tail_location

    set_mode(
        active_object_name=armature_object_name,
        mode='EDIT',
        configure_scene_for_basic_ops=False)
    armature_object = bpy.data.objects[armature_object_name]

    if head_location is not None:
        logger.debug('head_location: ' + str(head_location))
        armature_object.data.edit_bones[bone_name].head = Vector(head_location)

    if tail_location is not None:
        logger.debug('tail_location: ' + str(tail_location))
        armature_object.data.edit_bones[bone_name].tail = Vector(tail_location)

    bpy.ops.object.mode_set(mode='OBJECT')
    logger.info('set_bone_head_tail: Done')


def snap_single_bone_to_cursor(armature_object_name, bone_name):
    """
    This emulates blender's GUI snapping functionality.
    The translation vector is determined using the bones head
    location and the cursor position.
    """
    logger.info('snap_single_bone_to_cursor: ...')
    logger.info('armature_object_name: ' + armature_object_name)
    logger.info('bone_name: ' + bone_name)

    previous_mode = set_mode(
        active_object_name=armature_object_name,
        mode='OBJECT',
        configure_scene_for_basic_ops=False)

    armature_object = bpy.data.objects[armature_object_name]

    # NOTE:
    # IN armature_object.data.bones (NOT armature_object.data.edit_bones) there are 2 TYPES of coordinates
    # armature_object.data.bones[bone_name].head
    # head: Location of head end of the bone relative to its parent (the parent can be a BONE or the ARMATURE)
    # armature_object.data.bones[bone_name].head_local        # => Armature coordinates
    # head_local: Location of head end of the bone relative to armature (SAME as under Head in the GUI)

    # armature_object.data.bones[bone_name].tail and armature_object.data.bones[bone_name].tail_local same as for head

    # NOTE:
    # For the highest bone in the hierarchy .head and .head_local are equal (and .tail and .tail_local)
    # The GUI values are the same as in head_local and tail_local

    world_to_object_matrix = armature_object.matrix_world.inverted()
    # Cursor location is in WORLD COORDINATES
    cursor_location_in_armature_coordinates = \
        (world_to_object_matrix * bpy.context.scene.cursor_location.to_4d()).to_3d()

    shift_vec_armature_coordinates = \
        cursor_location_in_armature_coordinates - \
        armature_object.data.bones[bone_name].head_local

    # logger.debug('armature_object.data.bones[bone_name].head: ' +
    #   str(armature_object.data.bones[bone_name].head))
    # logger.debug('armature_object.data.bones[bone_name].head_local: ' +
    #   str(armature_object.data.bones[bone_name].head_local))

    new_head_pos = armature_object.data.bones[bone_name].head_local + shift_vec_armature_coordinates
    new_tail_pos = armature_object.data.bones[bone_name].tail_local + shift_vec_armature_coordinates

    set_bone_head_tail(
        armature_object_name,
        bone_name,
        head_location=new_head_pos,
        tail_location=new_tail_pos)

    bpy.ops.object.mode_set(mode=previous_mode)

    logger.info('snap_single_bone_to_cursor: Done')


def snap_bones_to_cursor(armature_object_name, bone_names_list):
    logger.info('snap_bones_to_cursor: ...')
    for bone_name in bone_names_list:
        snap_single_bone_to_cursor(armature_object_name, bone_name)
    logger.info('snap_bones_to_cursor: Done')


def add_bone_constraint_IK(armature_object_name,
                           bone_name,
                           constraint_name,
                           target_object_name,
                           chain_count=None,
                           subtarget_name=None):

    """
    :param armature_object_name:
    :param bone_name:
    :param constraint_name:
    :param target_object_name:
    :param chain_count:
    :param subtarget_name:
    :return:
    """

    # Bone constraints. Armature must be in pose mode.
    set_mode(
        active_object_name=armature_object_name,
        mode='POSE',
        configure_scene_for_basic_ops=False)
    armature_object = bpy.data.objects[armature_object_name]

    current_bone = armature_object.pose.bones[bone_name]

    current_constraint = current_bone.constraints.new(ConstraintTypes.IK)
    current_constraint.name = constraint_name
    if chain_count is not None:
        current_constraint.chain_count = chain_count
    current_constraint.target = bpy.data.objects[target_object_name]
    if subtarget_name is not None:
        current_constraint.subtarget = subtarget_name

    bpy.ops.object.mode_set(mode='OBJECT')


def add_bone_constraint_locked_track(armature_object_name,
                                     bone_name,
                                     constraint_name,
                                     target_object_name,
                                     target_bone_name=None):

    # Note: "track to" is outdated and should be replaced with "damped track" or "locked track"

    # Bone constraints. Armature must be in pose mode.
    set_mode(
        active_object_name=armature_object_name,
        mode='POSE',
        configure_scene_for_basic_ops=False)
    armature_object = bpy.data.objects[armature_object_name]
    current_bone = armature_object.pose.bones[bone_name]
    current_constraint = current_bone.constraints.new(ConstraintTypes.LOCKED_TRACK)
    current_constraint.name = constraint_name
    current_constraint.target = bpy.data.objects[target_object_name]

    if target_bone_name is not None:
        current_constraint.subtarget = target_bone_name

    bpy.ops.object.mode_set(mode='OBJECT')


def add_or_overwrite_bone_constraint_follow_path(armature_object_name,
                                                 bone_name,
                                                 constraint_name,
                                                 target_curve_name,
                                                 use_curve_follow=False,  # default blender value
                                                 use_fixed_location=False,  # default blender value
                                                 forward_axis='FORWARD_Y'
                                                 ):

    logger.info('add_bone_constraint_follow_path: ...')

    set_mode(
        active_object_name=armature_object_name,
        mode='POSE',
        configure_scene_for_basic_ops=False)
    armature_object = bpy.data.objects[armature_object_name]
    current_bone = armature_object.pose.bones[bone_name]

    # Note: The name / identifier of a constraint of a specific object is UNIQUE
    if constraint_name in current_bone.constraints:
        logger.warning('Follow Path constraint exists already')
        # Make sure the constraint has the correct type
        assert current_bone.constraints[constraint_name].type == ConstraintTypes.FOLLOW_PATH
        current_constraint = current_bone.constraints[constraint_name]
    else:
        current_constraint = current_bone.constraints.new(ConstraintTypes.FOLLOW_PATH)
    current_constraint.name = constraint_name
    current_constraint.target = bpy.data.objects[target_curve_name]
    current_constraint.use_curve_follow = use_curve_follow
    current_constraint.use_fixed_location = use_fixed_location
    current_constraint.forward_axis = forward_axis

    bpy.ops.object.mode_set(mode='OBJECT')
    logger.info('add_bone_constraint_follow_path: Done')


def add_bone_constraint_transformation(armature_object_name,
                                       bone_name,
                                       constraint_name,
                                       target_object_name,
                                       target_bone_name=None,
                                       extrapolate=True):

    set_mode(
        active_object_name=armature_object_name,
        mode='POSE',
        configure_scene_for_basic_ops=False)
    armature_object = bpy.data.objects[armature_object_name]
    current_bone = armature_object.pose.bones[bone_name]
    current_constraint = current_bone.constraints.new(ConstraintTypes.TRANSFORM)
    current_constraint.name = constraint_name
    current_constraint.target = bpy.data.objects[target_object_name]

    if target_bone_name is not None:
        current_constraint.subtarget = target_bone_name

    current_constraint.use_motion_extrapolate = extrapolate

    # Source
    current_constraint.map_from = 'LOCATION'
    current_constraint.from_min_y = -1
    current_constraint.from_max_y = 1

    current_constraint.map_to_x_from = 'Y'
    current_constraint.map_to_y_from = 'Y'
    current_constraint.map_to_z_from = 'Y'

    # Destination
    current_constraint.map_to = 'ROTATION'
    current_constraint.to_min_x_rot = -360  # degrees
    current_constraint.to_max_x_rot = 360  # degrees

    current_constraint.target_space = 'LOCAL'
    current_constraint.owner_space = 'LOCAL'

    bpy.ops.object.mode_set(mode='OBJECT')


def set_pose_position(armature_object_name, pose_position):

    previous_mode = set_mode(
        active_object_name=armature_object_name,
        mode='POSE',
        configure_scene_for_basic_ops=False)
    armature_object = bpy.data.objects[armature_object_name]
    armature_object.data.pose_position = pose_position

    bpy.ops.object.mode_set(mode=previous_mode)


def clear_and_set_inverse_bone_constraint_child_of(armature_object_name,
                                                   bone_name,
                                                   constraint_name,
                                                   toggle_pose_position=False):

    previous_mode = set_mode(
        active_object_name=armature_object_name,
        mode='POSE',
        configure_scene_for_basic_ops=False)
    armature_object = bpy.data.objects[armature_object_name]

    if toggle_pose_position:
        old_pose_position = armature_object.data.pose_position
        armature_object.data.pose_position = 'POSE'

    # pose position must be in 'POSE', otherwise the resetting of the inverse has no effect
    assert armature_object.data.pose_position == 'POSE'

    current_bone = armature_object.pose.bones[bone_name]

    # active bone
    override_context = bpy.context.copy()
    override_context['constraint'] = current_bone.constraints[constraint_name]
    armature_object.data.bones.active = armature_object.data.bones[bone_name]

    bpy.ops.constraint.childof_clear_inverse(
        override_context,
        constraint=constraint_name,
        owner='BONE')
    bpy.ops.constraint.childof_set_inverse(
        override_context,
        constraint=constraint_name,
        owner='BONE')

    if toggle_pose_position:
        armature_object.data.pose_position = old_pose_position

    bpy.ops.object.mode_set(mode=previous_mode)


def mute_bone_constraint(armature_object_name, bone_name, constraint_name, mute):
    previous_mode = set_mode(
        active_object_name=armature_object_name,
        mode='POSE',
        configure_scene_for_basic_ops=False)
    armature_object = bpy.data.objects[armature_object_name]
    current_bone = armature_object.pose.bones[bone_name]
    current_bone.constraints[constraint_name].mute = mute
    bpy.ops.object.mode_set(mode=previous_mode)


def create_example_armature(origin):

    armature_object_name = 'car_rig'
    create_armature_from_data(armature_object_name, origin)

    base_bone_name = 'Base'
    mid_bone_name = 'Mid'
    tip_bone_name = 'Tip'

    add_bone_to_armature(armature_object_name,
                        base_bone_name,
                        bone_head_pos=(0, 0, 5),
                        bone_tail_pos=(0, 0, 4)
                        )

    add_bone_to_armature(armature_object_name,
                         mid_bone_name,
                         bone_head_pos=(0, 0, 3),
                         bone_tail_pos=(0, 0, 2)
                         )

    add_bone_to_armature(armature_object_name,
                         tip_bone_name,
                         bone_head_pos=(0, 0, 1),
                         bone_tail_pos=(0, 0, 0)
                         )

    # set_bone_head_tail(
    #   armature_object_name,
    #   mid_bone_name, head_location=(2, 0, 1),
    #   tail_location=(2,0,2))
    # set_bone_head_tail(
    #   armature_object_name,
    #   tip_bone_name,
    #   head_location=(1, 0, 3))

    set_bone_parent(armature_object_name,
                    child_bone_name=mid_bone_name,
                    parent_bone_name=base_bone_name,
                    connected=True,
                    inherit_rotation=False,
                    inherit_scale=False)
    set_bone_parent(armature_object_name,
                    child_bone_name=tip_bone_name,
                    parent_bone_name=mid_bone_name,
                    connected=True,
                    inherit_rotation=False,
                    inherit_scale=False
                    )

    empty_obj = add_empty('empty_obj')
    add_bone_constraint_IK(armature_object_name=armature_object_name,
                           bone_name=tip_bone_name,
                           constraint_name='inverse kinematics',
                           target_object_name=empty_obj.name
                           )

    return armature_object_name


def run(origin):
    origin_vec = Vector(origin)

    rig1 = create_armature_from_data('DataRig', origin_vec + Vector((0, 6, 0)))
    #rig2 = create_armature_from_operator('OpsRig', origin_vec + Vector((0, 8, 0)))
    #rig3 = create_armature_from_primitive('PrimRig', origin_vec+Vector((0,10,0)))
    return


if __name__ == "__main__":
    run((0, 0, 0))

