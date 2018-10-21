from __future__ import print_function

import os
from Utility.Printing import ils

# Documentation
# https://www.blender.org/api/blender_python_api_2_78_release/


# ======= DATA =======
# https://www.blender.org/api/blender_python_api_2_63_17/bpy.types.BlendData.html
# https://www.blender.org/api/blender_python_api_2_78_release/bpy.ops.html

# ======= ======= =======

# ======= OPS =======
# 	https://www.blender.org/api/blender_python_api_2_69_release/bpy.ops.html
# ======= OPS =======

import bpy


def fprint(text, il=0):
    # Blender does not flush the output to stdout,
    # therefore we offer an alternative print function
    # On the other hand: Standard logger output is not buffered
    if il is not None:
        print(ils(il) + str(text), flush=True)


def fprint_iterable(list_to_print):
    for el in list_to_print:
        fprint(el)

# ======= IMPORT ================


def import_obj_file(pathToOBJFile):
    fprint('Import Obj File ...')
    bpy.ops.import_scene.obj(filepath=pathToOBJFile)


def fprint_data_objects():
    fprint('Reading data.objects ...')
    for obj in bpy.data.objects:
        fprint(obj.name, il=1)


def clean_meshes():
    fprint('Cleaning meshes ...')
    bpy.ops.object.select_by_type(extend=False, type='MESH')
    #Extend, Extend selection instead of deselecting everything first.
    bpy.ops.object.delete()


def clean_objects():
    fprint('Cleaning objects ...')
    bpy.ops.object.select_all(action='SELECT')
    # remove all selected meshes
    bpy.ops.object.delete()

# ============ some other methods


def convert_blender_mat_to_numpy_arr(blender_mat):
    """
    Deprecated: A simple cast should work
    (Printing a numpy array using the internal command line of blender crashes blender)
    """
    import numpy as np
    mat_as_lists_of_lists = []
    for row in blender_mat:
        mat_as_lists_of_lists.append([entry for entry in row])
    return np.array(mat_as_lists_of_lists)


def update_texture_paths_of_single_material(path_to_textures_folder, material):

    for texture_slot in material.texture_slots:
        if texture_slot:
            texture = texture_slot.texture
            if hasattr(texture, 'image'):
                # test if path is valid
                if not os.path.isfile(texture.image.filepath):
                    fprint('Correcting invalid image path of texture')
                    file_name = os.path.basename(texture.image.filepath)
                    new_file_path = os.path.join(path_to_textures_folder, file_name)
                    texture.image.filepath = new_file_path

                    fprint('texture.image.name: ' + str(texture.image.name))
                    fprint('new_file_path: ' + str(new_file_path))


def update_texture_paths_of_materials(path_to_textures_folder, material_names=None):

    fprint('update_texture_paths_of_materials: ...')

    if material_names:
        for material_name in material_names:
            material = bpy.data.materials[material_name]
            update_texture_paths_of_single_material(path_to_textures_folder, material)
    else:
        for material in bpy.data.materials:
            update_texture_paths_of_single_material(path_to_textures_folder, material)

    fprint('update_texture_paths_of_materials: Done')


def update_texture_image_paths(path_to_textures_folder):
    fprint('update_texture_image_paths: ...')

    for img in bpy.data.images:

        # REPLACE ONLY INVALID OLD PATHS
        if not os.path.isfile(img.filepath):
            file_name = os.path.basename(img.filepath)
            new_file_path = os.path.join(path_to_textures_folder, file_name)

            # REPLACE ONLY VALID NEW PATHS
            if os.path.isfile(new_file_path):
                img.filepath = new_file_path

    fprint('update_texture_image_paths: Done')


def update_texture_paths_of_objects(data, path_to_textures_folder):

    fprint('update_texture_paths_of_objects: ...')
    fprint('path_to_textures_folder: ' + path_to_textures_folder)

    # get all material names used by the objects
    used_material_names = []
    fprint('used_material_names: ' + str(used_material_names))

    # iterate over the newly added objects (this set DIFFERS from bpy.data.objects)
    for obj in data.objects:
        if obj is not None:

            for material_slot in obj.material_slots:
                # get the materials of the material_slots
                material = material_slot.material
                used_material_names.append(material.name)
                # this is equivalent to: bpy.data.materials[material_slot.material.name]

    # update paths (blender stores absolute paths, so if textures are moved this will break the blend file)
    # update_texture_paths_of_materials DOES NOT COVER ALL TEXTURES!
    # update_texture_paths_of_materials(path_to_textures_folder, used_material_names)
    # update_texture_image_paths DOES WORK
    update_texture_image_paths(path_to_textures_folder)

    fprint('update_texture_paths_of_objects: Done')

