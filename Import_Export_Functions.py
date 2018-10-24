import os
from collections import OrderedDict

import bpy
from BlenderUtility.Ops_Functions import make_object_active
from BlenderUtility.Point_Cloud_Tool import PointCloudTool, VertexType
from Utility.File_Handler.PLY_File_Handler import PLYFileHandler
from Utility.Logging_Extension import logger


def ensure_trailing_slash(some_path):
    return os.path.join(some_path, '')


def high_level_object_import_from_other_blend_file(blend_file, folder_name, target_name):

    # Several Possibilities
    #   Option: bpy.ops.wm.link()       # the object can only be edited in the original file
    #   Option: bpy.ops.wm.append()     # the object is copied and can be edited

    if not os.path.isfile(blend_file):
        assert False    # Invalid Input Path
    file_path = os.path.join(blend_file, folder_name, target_name)
    directory = ensure_trailing_slash(os.path.join(blend_file, folder_name))

    bpy.ops.wm.append(
        filepath=file_path,
        filename=target_name,
        directory=directory)


def low_level_object_import_from_other_blend_file(path_to_blend_file, path_to_textures_folder=None):
    # https://www.blender.org/api/blender_python_api_2_72_release/bpy.types.BlendDataLibraries.html

    # Option: bpy.types.BlendDataLibraries.load()
    #   BlendDataLibraries is a lower-level API to import datablocks (selectively) from .blends

    logger.info('Import Objects from blend file: ...')
    logger.info('Path: ' + str(path_to_blend_file))

    # newly_added_data is a subset of bpy.data
    newly_added_data = _load_blend_file(path_to_blend_file)
    # Deprecated! Paths should be fixed using blender make relative
    # if path_to_textures_folder != None:
    #     logger.info('Updating Texture paths')
    #     update_texture_paths_of_objects(newly_added_data, path_to_textures_folder)
    _link_or_append_objects_from_new_datablock_to_scene(newly_added_data)

    bpy.ops.object.select_all(action='DESELECT')
    logger.info('Import Objects from blend file: Done')


def _load_blend_file(path_to_blend_file):

    # https://www.blender.org/api/blender_python_api_2_72b_release/bpy.types.BlendDataLibraries.html

    # append the data block from .blend file
    with bpy.data.libraries.load(path_to_blend_file) as (data_from, data_to):
        # the loaded objects can be accessed from 'data_to' outside of the context
        # since loading the data replaces the strings for the datablocks or None
        # if the datablock could not be loaded.

        logger.info(len(data_from.objects))
        # We copy the objects, since we want to manually add them to the our scene
        # This is not compatible with ALL object types ?!?!?
        data_to.objects = data_from.objects

        # https://blender.stackexchange.com/questions/6357/is-it-possible-to-append-objects-to-the-same-layer-as-they-are-in-the-source-fil

        # we could also copy
        # data_to.materials = data_from.materials
        # data_to.images = data_from.images
        # data_to_textures = data_from.textures

    # ====== IMPORTANT ======
    # * after finishing the call " bpy.data.libraries.load" all elements are automatically added / appended to bpy.data
    # ====== ====== ======
    return data_to


def _link_or_append_objects_from_new_datablock_to_scene(data_to, mode='link'):

    scn = bpy.context.scene
    # iterate over the newly added objects (this set DIFFERS from bpy.data.objects)
    for obj in data_to.objects:
        if obj is not None:
            if mode == 'link':
                # link object to current scene (not possible to modify)
                scn.objects.link(obj)
            else:
                # append objects to current scene (possible to modify)
                scn.objects.append(obj)


def export_obj(object_name, path_to_obj):
    logger.info('export_obj: ...')

    bpy.ops.object.select_all(action='DESELECT')
    hidden = bpy.data.objects[object_name].hide
    make_object_active(object_name)

    bpy.ops.export_scene.obj(
        filepath=path_to_obj,
        check_existing=True,
        axis_forward='Y',
        axis_up='Z',
        filter_glob="*.obj;*.mtl",
        use_mesh_modifiers=True,
        use_normals=True,
        use_uvs=True,
        global_scale=1,
        use_selection=True)     # This is important, to only export the current object

    bpy.data.objects[object_name].hide = hidden
    bpy.ops.object.select_all(action='DESELECT')

    logger.info('export_obj: Done')


def import_ply(ifp, obj_name=None):

    """ By default Blender assings the file stem as blender object name """

    bpy.ops.import_mesh.ply(filepath=ifp)
    active_obj = bpy.context.object
    if obj_name is not None:
        active_obj.name = obj_name
    return active_obj


def import_ply_s(ifp_s, get_index_str_of_ply, prefix=None):
    """ Asume the file names show a numbering
        e.g. frame00000.jpg.ply, frame00001.jpg.ply, etc
    """

    index_str_to_obj = OrderedDict()
    for ifp in ifp_s:
        index_str = get_index_str_of_ply(ifp)
        obj_name = prefix + index_str

        active_obj = import_ply(ifp, obj_name)

        index_str_to_obj[index_str] = active_obj

        logger.vinfo('ifp', ifp)
        logger.vinfo('index_str', index_str)
        logger.vinfo('active_obj.name', active_obj.name)
    return index_str_to_obj


def import_ply_as_point_cloud(object_fps, get_index_str_of_ply, prefix=None, point_scale_factor=1):

    index_str_to_obj = OrderedDict()
    for object_fp in object_fps:
        logger.info('Importing ' + str(object_fp))

        index_str = get_index_str_of_ply(object_fp)
        obj_name = prefix + index_str

        points, _ = PLYFileHandler.parse_ply_file(object_fp)
        point_obj_names = PointCloudTool.add_point_cloud_using_dupliverts(
            points,
            add_meshes_at_vertex_positions=True,
            mesh_type=VertexType.CUBE,
            mesh_scale=point_scale_factor)

        bpy.context.scene.objects.active = bpy.data.objects[obj_name]

        index_str_to_obj[index_str] = bpy.data.objects[obj_name]

    return index_str_to_obj


def export_ply(object_name, path_to_ply, export_triangulated_mesh=True):

    logger.info('export_ply: ...')
    logger.vinfo('object_name', object_name)
    logger.vinfo('path_to_ply', path_to_ply)
    hidden = bpy.data.objects[object_name].hide
    make_object_active(object_name)

    if export_triangulated_mesh:
        logger.info('triangulate mesh before export')
        # Object may consist of quads instead of triangles
        # Exporting quads instead of triangles may be a problem for other software tools like cloud compare

        obj = bpy.context.scene.objects.active

        # Make sure to use the correct order of the modifiers
        # (otherwise the application may result in an unexpected behaviour)
        modifier_type_list = [target_modifier.type for target_modifier in obj.modifiers]
        logger.vinfo('modifier_type_list', modifier_type_list)

        if not 'TRIANGULATE' in modifier_type_list:
            # We do not need to apply the modifier,
            # since export_mesh.ply has a use_mesh_modifiers option
            bpy.ops.object.modifier_add(type='TRIANGULATE')

    bpy.ops.export_mesh.ply(
        filepath=path_to_ply,
        check_existing=True,
        axis_forward='Y',
        axis_up='Z',
        filter_glob="*.ply",
        use_mesh_modifiers=True,
        use_normals=True,
        use_uv_coords=True,
        global_scale=1)

    bpy.data.objects[object_name].hide = hidden
    bpy.ops.object.select_all(action='DESELECT')
    logger.info('export_ply: Done')