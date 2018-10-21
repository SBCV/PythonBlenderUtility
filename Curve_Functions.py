import logging

import bpy
from mathutils import Vector

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


def get_curve_length(curve_obj):
    """
    Return the length (in Blender distance units) of the path.
    """

    # # Convert the path to a mesh and use the edges to compute the path length
    # https://docs.blender.org/api/blender_python_api_current/bpy.types.Curve.html
    # curve to mesh

    # this does not alter the curve_obj
    curve_mesh = curve_obj.to_mesh(bpy.context.scene, False, 'PREVIEW')

    curve_length_in_curve_coord = 0
    # https://docs.blender.org/api/blender_python_api_current/bpy.types.MeshEdges.html
    # https://docs.blender.org/api/blender_python_api_current/bpy.types.MeshVertex.html
    for edge in curve_mesh.edges:
        vert_0 = curve_mesh.vertices[edge.vertices[0]].co
        vert_1 = curve_mesh.vertices[edge.vertices[1]].co
        curve_length_in_curve_coord += (vert_0 - vert_1).length

    scale_vec = curve_obj.matrix_world.to_scale()
    assert scale_vec[0] == scale_vec[1] == scale_vec[2]
    curve_length_in_world_coord = scale_vec[0] * curve_length_in_curve_coord

    # The curve length may be negative
    curve_length_in_world_coord = abs(curve_length_in_world_coord)

    # https://docs.blender.org/api/blender_python_api_2_76_release/bpy.types.Object.html?highlight=to_mesh#bpy.types.Object.to_mesh
    # https://docs.blender.org/api/blender_python_api_current/bpy.types.MeshEdge.html

    return curve_length_in_world_coord


def get_curve_start_coordinate(curve_name):
    curve = bpy.data.objects[curve_name]
    assert len(curve.data.splines) == 1
    first_car_curve_point_in_object_coords = Vector(curve.data.splines[0].points[0].co[0:3])
    # first_car_curve_point_in_world_coords = transform_vec_in_object_coordinates_to_world_coordinates(
    #   first_car_curve_point_in_object_coords, curve)
    first_car_curve_point_in_world_coords = curve.matrix_world * first_car_curve_point_in_object_coords

    return first_car_curve_point_in_world_coords


def attach_camera_or_object_to_path(camera_or_object_name,
                                    path_name,
                                    follow_path=True,
                                    forward_axis='TRACK_NEGATIVE_Y',
                                    up_axis='UP_X',
                                    clear_previous_constraints=False):

    """
    :param camera_or_object_name
    :param path_name
    :param follow_path
    :param forward_axis: Possible Values:
        'FORWARD_X', 'FORWARD_Y', 'FORWARD_Z',
        'TRACK_NEGATIVE_X', 'TRACK_NEGATIVE_Y', 'TRACK_NEGATIVE_Z'
    :param up_axis: Possible Values 'UP_X', 'UP_Y', 'UP_Z'
    :param clear_previous_constraints:
    :return:
    """

    logger.info('attach_camera_or_object_to_path: ...')
    # fprint('Old Matrix_World: ', il=il+1)
    # fprint(bpy.data.objects[object_name].matrix_world, il=il+1)
    logger.info('camera_or_object_name: ' + camera_or_object_name)
    logger.info('path_name: ' + path_name)

    bpy.ops.object.select_all(action='DESELECT')
    # bpy.context.scene.update()

    camera_or_object = bpy.data.objects[camera_or_object_name]

    if clear_previous_constraints:
        # https://docs.blender.org/api/blender_python_api_2_62_release/bpy.types.ObjectConstraints.html#bpy.types.ObjectConstraints.clear
        #   clear()  Remove all constraint from this object
        # https://docs.blender.org/api/blender_python_api_2_62_release/bpy.types.ObjectConstraints.html#bpy.types.ObjectConstraints.remove
        #   Parameters:	constraint (Constraint, (never None)) - Removed constraint
        #       https://docs.blender.org/api/blender_python_api_2_62_release/bpy.types.Constraint.html#bpy.types.Constraint
        camera_or_object.constraints.clear()

    path_object = bpy.context.scene.objects[path_name]
    constraint = camera_or_object.constraints.new('FOLLOW_PATH')
    constraint.target = path_object

    if follow_path:
        constraint.use_curve_follow = True
        constraint.forward_axis = forward_axis
        constraint.up_axis = up_axis

    # https://blenderartists.org/forum/archive/index.php/t-351947.html
    # without 'followpath_path_animate' nothing happens
    # 'followpath_path_animate' creates a default animation for 'camera_or_object'
    bpy.context.scene.objects.active = camera_or_object
    context_with_extra_attributes = bpy.context.copy()
    # bpy.ops.constraint.followpath_path_animate(...):
    # Add default animation for path used by constraint if it isn't animated already
    # follow_path_animate may print the following messages
    #   * "Warning: Path is already animated" (this is not a problem)
    #   * something like the following (this IS a problem)
    #           PyContext 'constraint' not found
    #           PyContext 'object' not found
    #           PyContext 'active_object' not found
    #       This means that the context object (i.e. context_with_extra_attributes) does not have the following
    #       properties: 'constraint', 'object', 'active_object'
    context_with_extra_attributes['constraint'] = constraint
    context_with_extra_attributes['object']= camera_or_object
    context_with_extra_attributes['active_object'] = camera_or_object
    # OBJECT Object, Edit a constraint on the active object.
    bpy.ops.constraint.followpath_path_animate(
        context_with_extra_attributes,
        constraint='Follow Path',
        owner='OBJECT')

    # Alternative approach: Build the context from scratch (is a dictionary)
    # https://blender.stackexchange.com/questions/15307/scripting-cant-figure-out-how-to-use-correct-contexts
    # override = {'constraint': camera_or_object.constraints["Follow Path"]}
    # bpy.ops.constraint.followpath_path_animate(override, constraint='Follow Path', owner='OBJECT')

    # THE DESELECTION IS KEY !!!!
    # OTHERWISE the object.matrix_world of the car IS NOT UPDATED AND CONTAINS ONLY THE OLD INFORMATION
    # i.e. the attaching moves the object to the starting point of the path
    bpy.ops.object.select_all(action='DESELECT')        # Todo does that implicitely call update()?

    # logger.info('New Matrix_World: ', il=il+1)
    # logger.info(bpy.data.objects[object_name].matrix_world, il=il+1)
    logger.info('attach_camera_or_object_to_path: Done')


def create_curve_from_coordinates(path_name, vertices):

    # https://www.blender.org/api/blender_python_api_current/bpy.types.Curve.html

    logger.info('Create curve from coordinates: ...')
    if len(vertices):
        logger.info('Len of vertices is ' + str(len(vertices)) + '. The resulting animation could be slow!')

    # https://www.blender.org/api/blender_python_api_2_77_release/bpy.types.Curve.html#bpy.types.Curve
    nurbs_path_object_data = bpy.data.curves.new(name=path_name, type='CURVE')
    nurbs_path_object_data.dimensions = '3D'

    nurbs_path_object = bpy.data.objects.new(path_name, nurbs_path_object_data)
    nurbs_path_object.location = (0, 0, 0)
    bpy.context.scene.objects.link(nurbs_path_object)

    # 'CurveSplines' is a 'bpy_prop_collection' of 'Spline'
    # https://www.blender.org/api/blender_python_api_2_77_release/bpy.types.bpy_prop_collection.html#bpy.types.bpy_prop_collection
    # https://www.blender.org/api/blender_python_api_2_77_release/bpy.types.Spline.html#bpy.types.Spline

    nurbs_spline = nurbs_path_object.data.splines.new(type='NURBS')
    nurbs_spline.points.add(len(vertices) - 1)

    # https://www.blender.org/api/blender_python_api_2_78a_release/bpy.types.CurveSplines.html

    for index in range(len(vertices)):
        x, y, z = vertices[index]
        nurbs_spline.points[index].co = (x, y, z, 1)

    # =================== deprecated ===================
    # to expensive when many objects are in the scene

    # bpy.ops.curve.primitive_nurbs_path_add(location=vertices[0], enter_editmode=True)
    # nurbs_path_object = bpy.context.scene.objects.active

    # there is only one Spline with 5 SplinePoints after creation
    # delete all points
    # bpy.ops.curve.delete(type='VERT')

    # # the nurbs path is created by default with 5 vertices, delete these vertices
    # # they are selected after creation, and therefore deleted by the following call
    # bpy.ops.curve.delete(type='VERT')
    #
    # for vertex in vertices:
    #     # THIS IS VERY EXPENSIVE (UPDATES THE SCENE (i.e. ALL OBJECTS) EACH TIME )
    #     #bpy.ops.curve.vertex_add(location=vertex)

    # recompute the normals, otherwise the first point may have incorrect handles / control points
    # bpy.ops.curve.normals_make_consistent()

    # bpy.ops.object.mode_set(mode='OBJECT')

    logger.info('Create curve from coordinates: Done')
    return nurbs_path_object



