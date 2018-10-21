import math
import os
import os.path
from math import radians

import bpy
from mathutils import Matrix, Vector

from BlenderUtility.Ops_Functions import set_mode, check_ops_prerequisites
from Utility.Math.Conversion.Conversion_Collection import invert_y_and_z_axis

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


# ==============================================================================================================
#                                               General
# ==============================================================================================================

def get_world_matrix_from_translation_vec(translation_vec, rotation):
    t = Vector(translation_vec).to_4d()
    camera_rotation = Matrix()
    for row in range(3):
        camera_rotation[row][0:3] = rotation[row]

    camera_rotation.transpose()  # = Inverse rotation

    camera_center = -(camera_rotation * t)  # Camera position in world coordinates
    camera_center[3] = 1.0

    camera_rotation = camera_rotation.copy()
    camera_rotation.col[3] = camera_center  # Set translation to camera position
    return camera_rotation


def transform_vec_in_object_coordinates_to_world_coordinates(object_coordinates, object):

    # OPTION 1 DEPRECATED
    # # set rotation mode to quaternion,
    # # otherwise "object.rotation_quaternion" will always return (w=1.0000, x=0.0000, y=0.0000, z=0.0000)
    # object.rotation_mode = 'QUATERNION'
    #object.matrix_world * object_coordinates
    # # http://science-o-matics.com/2014/01/how-to-python-scripting-in-blender-8-rotation-mit-quaternionen/
    # # https://www.blender.org/api/blender_python_api_2_69_release/mathutils.html
    # # todo verify this
    # rotated_object_coordinates = object.rotation_quaternion.to_matrix() * object_coordinates
    # world_coordinates = rotated_object_coordinates + object.location
    #
    # return world_coordinates

    # OPTION 2 RECOMMENDED
    # matrix_world contains the CURRENT position information
    return object.matrix_world * object_coordinates


def get_object_bounding_box_center(object_name):

    current_object = bpy.data.objects[object_name]
    local_bbox_center = 0.125 * sum((Vector(b) for b in current_object.bound_box), Vector())
    global_bbox_center = current_object.matrix_world * local_bbox_center
    return global_bbox_center


def scale_object(object_name, scaling_parameter):
    bpy.data.objects[object_name].scale = [scaling_parameter, scaling_parameter, scaling_parameter]


def select_single_object(obj):
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = obj
    obj.select=True


def move_object_to_layer(object_name, layer_id):
    obj = bpy.data.objects[object_name]
    obj.layers[layer_id] = True

    for i in range(20):
        obj.layers[i] = (i == layer_id)


# ==============================================================================================================
#                                               Add
# ==============================================================================================================


def add_points_as_mesh(points):
    logger.info("Adding point cloud...")
    name = "Point_Cloud"
    mesh = bpy.data.meshes.new(name)
    mesh.update()
    mesh.validate()

    points = [tuple(point.coord) for point in points]

    mesh.from_pydata(points, [], [])
    meshobj = add_obj(mesh, name)

    # TODO replace matrix with identity matrix
    meshobj.matrix_world = Matrix.Rotation(radians(0), 4, 'X')


def add_obj(data, obj_name):
    scene = bpy.context.scene

    for obj in scene.objects:
        obj.select = False

    new_obj = bpy.data.objects.new(obj_name, data)
    scene.objects.link(new_obj)
    new_obj.select = True

    if scene.objects.active is None or scene.objects.active.mode == 'OBJECT':
        scene.objects.active = new_obj
    return new_obj

def add_copy(original_obj_name, new_obj_name):
    src_obj = bpy.data.objects[original_obj_name]
    new_obj = src_obj.copy()
    new_obj.data = src_obj.data.copy()
    #new_obj.animation_data_clear()
    new_obj.name = new_obj_name
    bpy.context.scene.objects.link(new_obj)
    return new_obj

def add_empty(empty_name):
    empty_obj = bpy.data.objects.new(empty_name, None)
    bpy.context.scene.objects.link(empty_obj)
    return empty_obj


def add_line(start_point, end_point, mesh_object_name='line', mesh_data_name='line_data'):

    bpy.ops.object.select_all(action='DESELECT')
    verts = [start_point, end_point]
    mesh_data = bpy.data.meshes.new(mesh_data_name)
    # from_pydata(vertices, edges, faces)
    mesh_data.from_pydata(verts, [(0, 1)], [])
    mesh_data.update()

    obj = bpy.data.objects.new(mesh_object_name, mesh_data)
    scene = bpy.context.scene
    scene.objects.link(obj)

    bpy.ops.object.select_all(action='DESELECT')


def add_plane(plane_name, radius=None, texture_path=None):

    # clipping_distance = bpy.data.cameras['Camera'].clip_end

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_plane_add(radius=radius)
    bpy.context.scene.objects.active.name = plane_name
    bpy.ops.object.select_all(action='DESELECT')

def add_cube(cube_name, radius=None, texture_path=None):

    # clipping_distance = bpy.data.cameras['Camera'].clip_end

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_cube_add()
    bpy.context.scene.objects.active.name = cube_name
    bpy.ops.object.select_all(action='DESELECT')

def add_camera(camera_name):
    rendering_camera_data = bpy.data.cameras.new(name=camera_name)
    rendering_camera_object = bpy.data.objects.new(camera_name, rendering_camera_data)
    bpy.context.scene.objects.link(rendering_camera_object)
    rendering_camera_object.location = [0, 0, 0]

def add_noise_to_camera(noisy_virtual_camera_name, noisy_camera_viewing_direction, noisy_camera_roll):
    noisy_virtual_camera = bpy.data.objects[noisy_virtual_camera_name]
    noisy_virtual_camera.keyframe_insert("rotation_euler")  # ensures animation_data and action are not None
    action = noisy_virtual_camera.animation_data.action
    for fcu in action.fcurves:

        mod = None
        if noisy_camera_viewing_direction or noisy_camera_roll:
            mod = fcu.modifiers.new("NOISE")

        arr_idx = fcu.array_index

        # https://docs.blender.org/manual/en/dev/editors/graph_editor/fcurves/fmodifiers.html
        # These settings are visible in the Animation view

        # X Euler Rotation
        if noisy_camera_viewing_direction:
            if arr_idx == 0:
                mod.scale = 10.0
                mod.strength = 0.02
                mod.phase = 0   # 2.0 * 3.141 * 0.0 / 3.0   # 1/3 of the circumference
                mod.offset = 0
            # Y Euler Rotation
            if arr_idx == 1:
                mod.scale = 10.0
                mod.strength = 0.02
                #mod.phase = 2.0 * 3.141 * 1.0 / 3.0     # 2/3 of the circumference
                mod.phase = 100
                mod.offset = 100

        if noisy_camera_roll:
            # Z Euler Rotation
            if arr_idx == 2:
                mod.scale = 10.0
                mod.strength = 1.0
                #mod.phase = 2.0 * 3.141 * 2.0 / 3.0     # 3/3 of the circumference
                mod.phase = 200
                mod.offset = 200


def add_cameras(cameras, path_to_images=None,
                add_image_planes=False,
                convert_camera_coordinate_system=True,
                cameras_parent='Cameras',
                camera_group_name='Camera Group',
                image_planes_parent='Image Planes',
                image_plane_group_name='Image Plane Group'):

    """
    ======== The images are currently only shown in BLENDER RENDER ========
    ======== Make sure to enable TEXTURE SHADING in the 3D view to make the images visible ========

    :param cameras:
    :param path_to_images:
    :param add_image_planes:
    :param convert_camera_coordinate_system:
    :param cameras_parent:
    :param camera_group_name:
    :param image_plane_group_name:
    :return:
    """

    logger.info('add_cameras: ...')

    cameras_parent = add_empty(cameras_parent)
    camera_group = bpy.data.groups.new(camera_group_name)

    if add_image_planes:
        image_planes_parent = add_empty(image_planes_parent)
        image_planes_group = bpy.data.groups.new(image_plane_group_name)

    # Adding cameras and image planes:
    for index, camera in enumerate(cameras):

        assert camera.width is not None and camera.height is not None

        # camera_name = "Camera %d" % index     # original code
        # Replace the camera name so it matches the image name (without extension)
        image_file_name_stem = os.path.splitext(os.path.basename(camera.file_name))[0]
        camera_name = image_file_name_stem + '_cam'

        focal_length = camera.calibration_mat[0][0]

        # Add camera:
        bcamera = bpy.data.cameras.new(camera_name)
        bcamera.angle_x = math.atan(camera.width / (focal_length * 2.0)) * 2.0
        bcamera.angle_y = math.atan(camera.height / (focal_length * 2.0)) * 2.0
        camera_object = add_obj(bcamera, camera_name)

        # TODO if convert_camera_coordinate_system:
        translation_vec = camera.get_translation_vec()
        rotation_mat = camera.get_rotation_mat()
        # Transform the camera coordinate system from the computer vision camera coordinate frame to the computer
        # vision camera coordinate frame (i.e. rotate the camera matrix around the x axis by 180 degree)
        # (i.e. INVERT X AND Y AXIS )
        rotation_mat = invert_y_and_z_axis(rotation_mat)
        translation_vec = invert_y_and_z_axis(translation_vec)
        camera_object.matrix_world = get_world_matrix_from_translation_vec(translation_vec, rotation_mat)

        set_object_parent(camera_object, cameras_parent, keep_transform=True)
        camera_group.objects.link(camera_object)

        if add_image_planes:

            # Group image plane and camera:
            camera_image_plane_pair = bpy.data.groups.new("Camera Image Plane Pair Group %s" % image_file_name_stem)
            camera_image_plane_pair.objects.link(camera_object)

            image_plane_name = image_file_name_stem + '_image_plane'
            # do not add image planes by default, this is slow !
            bimage = bpy.data.images.load(os.path.join(path_to_images, camera.file_name))
            image_plane_obj = add_camera_image_plane(rotation_mat, translation_vec, bimage, camera.width, camera.height, focal_length, name=image_plane_name)
            camera_image_plane_pair.objects.link(image_plane_obj)

            set_object_parent(image_plane_obj, image_planes_parent, keep_transform=True)
            image_planes_group.objects.link(image_plane_obj)


def add_camera_image_plane(rotation_mat, translation_vec, bimage, width, height, focal_length, name):
    # Create mesh for image plane:
    mesh = bpy.data.meshes.new(name)
    mesh.update()
    mesh.validate()

    # world_matrix = camera.world
    plane_distance = 1.0  # Distance from camera position
    # Right vector in view frustum at plane_distance:
    right = Vector((1, 0, 0)) * (width / focal_length) * plane_distance
    # Up vector in view frustum at plane_distance:
    up = Vector((0, 1, 0)) * (height / focal_length) * plane_distance
    # Camera view direction:
    view_dir = -Vector((0, 0, 1)) * plane_distance
    plane_center = view_dir

    corners = ((-0.5, -0.5),
               (+0.5, -0.5),
               (+0.5, +0.5),
               (-0.5, +0.5))
    points = [(plane_center + c[0] * right + c[1] * up)[0:3] for c in corners]
    mesh.from_pydata(points, [], [[0, 1, 2, 3]])

    # Assign image to face of image plane:
    uvmap = mesh.uv_textures.new()
    face = uvmap.data[0]
    face.image = bimage

    # Add mesh to new image plane object:
    mesh_obj = add_obj(mesh, name)

    image_plane_material = bpy.data.materials.new(name="image_plane_material")
    image_plane_material.use_shadeless = True

    # Assign it to object
    if mesh_obj.data.materials:
        # assign to 1st material slot
        mesh_obj.data.materials[0] = image_plane_material
    else:
        # no slots
        mesh_obj.data.materials.append(image_plane_material)

    world_matrix = get_world_matrix_from_translation_vec(translation_vec, rotation_mat)
    mesh_obj.matrix_world = world_matrix
    mesh.update()
    mesh.validate()
    return mesh_obj

# ==============================================================================================================
#                                               Join
# ==============================================================================================================

def join_copy_of_objects(obj_name_list, joined_name):

    # Overall only one new object with joined_name is created

    copy_list = []
    for obj_name in obj_name_list:
        obj = bpy.data.objects[obj_name]
        obj_copy = add_copy(original_obj_name=obj.name, new_obj_name=obj.name + '_copy')
        copy_list.append(obj_copy)

    ctx = bpy.context.copy()

    # one of the objects to join
    ctx['active_object'] = copy_list[0]
    ctx['selected_objects'] = copy_list
    # we need the scene bases as well for joining
    ctx['selected_editable_bases'] = [bpy.context.scene.object_bases[ob.name] for ob in copy_list]
    bpy.ops.object.join(ctx)

    copy_list[0].name = joined_name

    return bpy.data.objects[joined_name]

# ==============================================================================================================
#                                               Meshes
# ==============================================================================================================

def convert_object_to_mesh_or_curve(original_object, target, keep_original=False):

    """

    :param original_object:
    :param target: enum in ['CURVE', 'MESH']
    :param keep_original:
    :return:
    """
    logger.info('convert_object_to_mesh_or_curve: ...')
    #logger.info('object name: ' + str(original_object.name))

    data_name = original_object.data.name

    #view_3d_area = [area for area in bpy.context.screen.areas if area.type == 'VIEW_3D'][0]
    #logger.info(view_3d_area)

    bpy.ops.object.select_all(action='DESELECT')

    # SELECTING the target object AND (!!!) making it the active object IS ABSOLUTELY CRUCIAL,
    # otherwise the following error is thrown:
    # RuntimeError: Operator bpy.ops.object.convert.poll() failed, context is incorrect
    # https://docs.blender.org/api/blender_python_api_current/info_quickstart.html#operator-poll
    bpy.data.objects[original_object.name].select = True
    bpy.context.scene.objects.active = bpy.data.objects[original_object.name]

    # https://docs.blender.org/api/blender_python_api_2_77_0/bpy.ops.html#keywords-and-positional-arguments
    # https://docs.blender.org/api/blender_python_api_2_77_0/bpy.ops.html#overriding-context

    # https://docs.blender.org/api/blender_python_api_current/bpy.ops.html
    # https://docs.blender.org/api/blender_python_api_current/bpy.ops.object.html
    # https://docs.blender.org/api/blender_python_api_current/bpy.ops.object.html#bpy.ops.object.convert
    #   Convert selected objects to another type
    #       target (enum in ['CURVE', 'MESH'', (optional)) - Target, Type of object to convert to
    #       keep_original (boolean, (optional)) - Keep Original, Keep original objects instead of replacing them

    bpy.ops.object.convert(target=target, keep_original=keep_original)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[original_object.name].select = False

    original_object.data.name = data_name

    logger.info('convert_object_to_mesh_or_curve: Done')


def get_mesh_vertex_world_coordinates(mesh_object_name):

    mesh_vertex_coordinates = []
    mesh_object = bpy.data.objects[mesh_object_name]
    mesh = mesh_object.data
    for vert in mesh.vertices:
        #vertex_world_coords = transform_vec_in_object_coordinates_to_world_coordinates(vert.co, mesh_object)
        vertex_world_coords = mesh_object.matrix_world * vert.co
        mesh_vertex_coordinates.append(vertex_world_coords)

    return mesh_vertex_coordinates


# ==============================================================================================================
#                                               Parent / Child
# ==============================================================================================================


def set_object_parent(child_object, parent_object, keep_transform=False):
    # logger.info('set_object_parent: ...')

    child_object.parent = parent_object
    if keep_transform:
        child_object.matrix_parent_inverse = parent_object.matrix_world.inverted()

    # logger.info('set_object_parent: ...')


def set_object_parent_bone(child_object_name, armature_object_name, bone_name, keep_transform=False):

    logger.info('set_object_parent_bone: ...')
    # https://docs.blender.org/api/blender_python_api_current/bpy.ops.object.html#bpy.ops.object.parent_set

    logger.info('child_object_name:' + str(child_object_name))
    logger.info('armature_object_name: ' + str(armature_object_name))

    #  Idea taken from:
    # http://nullege.com/codes/show/src%40b%40l%40blender_mmd_tools-HEAD%40mmd_tools%40utils.py/32/bpy.ops.object.parent_set/python

    set_mode(armature_object_name, mode='POSE', configure_scene_for_basic_ops=True)


    parent_object = bpy.data.objects[armature_object_name]
    bpy.data.objects[child_object_name].select = True

    # make the object active in pose mode
    parent_armature_data = parent_object.data
    parent_bone = parent_armature_data.bones[bone_name]
    parent_armature_data.bones.active = parent_bone
    parent_bone.select = False

    logger.info('parent_armature_data.name: ' + str(parent_armature_data))
    logger.debug('bpy.context.scene.objects.active: (before ops) ' + str(bpy.context.scene.objects.active))
    logger.debug('Selected objects: (before ops) ' + str([obj for obj in bpy.data.objects if obj.select]))
    logger.debug('parent_armature_data.bones.active: (before ops) ' + str(parent_armature_data.bones.active))
    #logger.debug('Selected bones: (before ops) ' + str([bone for bone in parent_armature_data.bones if bone.select]))

    check_ops_prerequisites(active_object_name=armature_object_name,
                            selected_object_names=[child_object_name])

    bpy.ops.object.parent_set(type='BONE', xmirror=False, keep_transform=keep_transform)

    bpy.ops.object.mode_set(mode='OBJECT')

    logger.info('set_object_parent_bone: Done')


def clear_and_set_inverse_object_constraint_child_of(object_name, constraint_name):

    previous_mode = set_mode(active_object_name=object_name, mode='OBJECT', configure_scene_for_basic_ops=False)

    current_object = bpy.data.objects[object_name]

    override_context = bpy.context.copy()
    override_context['constraint'] = current_object.constraints[constraint_name]

    bpy.ops.constraint.childof_clear_inverse(override_context, constraint=constraint_name, owner='OBJECT')
    bpy.ops.constraint.childof_set_inverse(override_context, constraint=constraint_name, owner='OBJECT')

    bpy.ops.object.mode_set(mode=previous_mode)


# ==============================================================================================================
#                                               CONSTRAINTS
# ==============================================================================================================

def _compute_centroid_of_object_locations(object_names):
    centroid_location = Vector([0.0, 0.0, 0.0])
    for object_name in object_names:
        centroid_location += bpy.data.objects[object_name].location
    centroid_location /= float(len(object_names))
    return centroid_location


def set_cursor_to_objects(object_names):
    """
    This emulates blender's "curser to selected" GUI functionality.
    As in blender's GUI the position the objects is represented by the centroid of the obj.location attributes.
    """
    bpy.context.scene.cursor_location = _compute_centroid_of_object_locations(object_names)


def snap_objects_to_cursor(object_names):
    """
    This emulates blender's GUI snapping functionality, i.e. translate the centroid of the obj.location attributes onto
    the cursor position.
    """
    centroid = _compute_centroid_of_object_locations(object_names)
    shift_vec = bpy.context.scene.cursor_location - centroid

    for obj_name in object_names:
        obj = bpy.data.objects[obj_name]
        obj.location += shift_vec


# ==============================================================================================================
#                                               CONSTRAINTS
# ==============================================================================================================


def mute_object_constraint(object_name, constraint_name, mute):
    previous_mode = set_mode(active_object_name=object_name, mode='OBJECT',
                             configure_scene_for_basic_ops=False)
    armature_object = bpy.data.objects[object_name]
    armature_object.constraints[constraint_name].mute = mute
    bpy.ops.object.mode_set(mode=previous_mode)


def _get_or_create_constraint(object_name, constraint_name, constraint_type):
    """
    :param object_name:
    :param constraint_name:
    :param constraint_type: 'TRACK_TO', COPY_LOCATION
    :return:
    """
    if constraint_name in bpy.data.objects[object_name].constraints:
        constraint = bpy.data.objects[object_name].constraints[constraint_name]
    else:
        constraint = bpy.data.objects[object_name].constraints.new(type=constraint_type)
    return constraint


def set_constraint_track_to(object_name, target_object_name, constraint_name='Track To',
                            subtarget_name=None, update=True, use_target_z=False):

    """
    Legacy tracking constraint prone to twisting artifacts !!!
    "track to" is outdated and should be replaced with "damped track".

    :param object_name:
    :param target_object_name:
    :param subtarget_name:
    :param update:
    :return:
    """
    # TODO "track to" is outdated and should be replaced with "damped track"

    logger.info('set_constraint_track_to: ...')
    constraint = _get_or_create_constraint(object_name, constraint_name, constraint_type='TRACK_TO')
    constraint.target = bpy.data.objects[target_object_name]
    if subtarget_name is not None:
        constraint.subtarget = subtarget_name
    # http://blender.stackexchange.com/questions/43/whats-the-quickest-easiest-way-to-point-the-camera-somewhere-in-blender
    # Track To constraint to it (constraints can be added in the Constraints tab),
    #   choose the object in the Target field,
    #   -Z in the To field
    #   Y in the Up field.
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.use_target_z = use_target_z
    constraint.up_axis = 'UP_Y'
    logger.info('Object ' + object_name + ' is looking at target ' + target_object_name)
    if update:
        bpy.context.scene.update()
    logger.info('set_constraint_track_to: Done')

def set_constraint_damped_track(object_name, target_object_name, constraint_name='Damped Track',
                                subtarget_name=None, update=True):

    logger.info('set_constraint_damped_track: ...')
    constraint = _get_or_create_constraint(object_name, constraint_name, constraint_type='DAMPED_TRACK')
    constraint.target = bpy.data.objects[target_object_name]
    constraint.track_axis = 'TRACK_NEGATIVE_Z'

    if subtarget_name is not None:
        constraint.subtarget = subtarget_name
    if update:
        bpy.context.scene.update()
    logger.info('set_constraint_damped_track: Done')


def set_constraint_locked_track(object_name, target_object_name, lock_axis='LOCK_Z', constraint_name='Locked Track',
                                subtarget_name=None, update=True):

    """
    In contrast to set_constraint_damped_track, here is one degree of freedom locked
    :param object_name:
    :param target_object_name:
    :param constraint_name:
    :param subtarget_name:
    :param update:
    :return:
    """

    logger.info('set_constraint_damped_track: ...')
    constraint = _get_or_create_constraint(object_name, constraint_name, constraint_type='LOCKED_TRACK')
    constraint.target = bpy.data.objects[target_object_name]
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.track_axis = lock_axis

    if subtarget_name is not None:
        constraint.subtarget = subtarget_name
    if update:
        bpy.context.scene.update()
    logger.info('set_constraint_damped_track: Done')

def set_constraint_copy_location(object_name, target_object_name, constraint_name='Copy Location',
                                 subtarget_name=None, use_offset=True):
    """
    Adds or overwrites the copy location constraint with constraint_name and the given parameters
    """
    logger.info('set_constraint_copy_location: ...')
    constraint = _get_or_create_constraint(object_name, constraint_name, constraint_type='COPY_LOCATION')
    constraint.target = bpy.data.objects[target_object_name]
    if subtarget_name is not None:
        constraint.subtarget = subtarget_name
    constraint.use_offset = use_offset
    logger.info('set_constraint_copy_location: Done')

# ==============================================================================================================
#                                               Modifiers
# ==============================================================================================================


def show_viewport_object_modifier(object_name, modifier_name, show_viewport):
    previous_mode = set_mode(active_object_name=object_name, mode='OBJECT',
                             configure_scene_for_basic_ops=False)
    armature_object = bpy.data.objects[object_name]
    armature_object.modifiers[modifier_name].show_viewport = show_viewport
    bpy.ops.object.mode_set(mode=previous_mode)


# ==============================================================================================================
#                                               Deprecated
# ==============================================================================================================

        # DEPRECATED
# def scale_object(object_name, scaling_parameter, scale_in_edit_mode=False):
#     bpy.ops.object.select_all(action='DESELECT')
#     bpy.context.scene.objects.active = bpy.context.scene.objects[object_name]
#     bpy.context.scene.objects[object_name].select = True
#
#     if scale_in_edit_mode:
#         # change to edit mode, so the resizing is directly applied to geometry
#         bpy.ops.object.mode_set(mode='EDIT')
#
#     bpy.ops.transform.resize(value=(scaling_parameter, scaling_parameter, scaling_parameter))
#
#     bpy.ops.object.mode_set(mode='OBJECT')
#     bpy.context.scene.objects[object_name].select = False
#     bpy.ops.object.select_all(action='DESELECT')