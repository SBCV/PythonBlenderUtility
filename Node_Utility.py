
import bpy
import os

from collections import defaultdict
from Utility.Logging_Extension import logger

# http://blender.stackexchange.com/questions/8936/does-switching-from-blender-render-to-cycles-mess-things-up
# * All matierals in cycles use nodes (even if you set up the material in the Properties panel, it will create
# nodes in the node editor).
# * Since BI materials don't use nodes by default, when you switch to cycles from BI there won't be any BI
# nodes in the node tree, yet nodes will be enabled. This will make the material render as transparent.

# One must switch / toggle between use_shader nodes

# Remark:
# info pannel in cycles:
#   the info pannel in cycles misses a lot of different commands
#       http://blender.stackexchange.com/questions/18020/print-all-commands-in-the-info-view
#   https://www.blender.org/api/blender_python_api_2_72_release/info_api_reference.html#operators
#       Most key-strokes and buttons in Blender call an operator which is also exposed to python via bpy.ops,
#       To see the Python equivalent hover your mouse over the button and see the tool-tip,
#       eg Python: bpy.ops.render.render(), If there is no tool-tip or the Python: line is missing then this button
# is not using an operator and can't be accessed from Python.
# If you want to use this in a script you can press Control-C while your mouse is over the button to copy it to the
# clipboard.

# =================
# alternative approach (not tested yet)
# http://blender.stackexchange.com/questions/364/how-do-i-convert-materials-from-blender-internal-to-cycles
# https://blenderartists.org/forum/showthread.php?247271-Cycles-Automatic-Material-Textures-Node


def rearrange_nodes():
    logger.info('rearrange_nodes: ...')
    # TODO
    # https://www.blendernation.com/2015/11/03/development-cleaning-up-node-trees/
    # https://github.com/JuhaW/NodeArrange/blob/master/__init__.py
    assert False


def create_viewer_node(scene, preceeding_node_name, preceeding_channel_name):
    """
    For debug purposes. Allows to visualize intermediate nodes.

    :param scene:
    :param preceeding_node_name:
    :param preceeding_channel_name:
    :return:
    """
    logger.info('create_viewer_node: ...')

    scene_nodes = scene.node_tree.nodes
    scene_links = scene.node_tree.links

    mask_id_node = scene_nodes.get(preceeding_node_name)
    viewer_node = scene_nodes.new('CompositorNodeViewer')

    scene_links.new(mask_id_node.outputs[preceeding_channel_name],
                    viewer_node.inputs['Image'])

    logger.info('create_viewer_node: Done')


def create_depth_viewer_node(scene):

    """
    This will save the z buffer in the Viewer Node after rendering

    bpy.ops.render.render()
    rendered_image = bpy.data.images['Viewer Node']
    pixels = rendered_image.pixels

    :param scene:
    :return:
    """

    logger.info('create_depth_output_nodes: ...')

    scene.use_nodes = True
    scene_nodes = scene.node_tree.nodes
    scene_links = scene.node_tree.links

    default_render_layers_node = scene_nodes.get('Render Layers')

    # output_value = default_render_layers_node.outputs[output_type]
    # print(type(output_value))

    viewer_node = scene_nodes.get('Depth Viewer')
    if viewer_node is None:
        viewer_node = scene_nodes.new('CompositorNodeViewer')
        viewer_node.name = 'Depth Viewer'

    logger.vinfo('viewer_node.name', viewer_node.name)

    viewer_node.use_alpha = False

    output_type = 'Depth'
    scene_links.new(
        default_render_layers_node.outputs[output_type],
        viewer_node.inputs[0])  # link Z to output

    logger.info('create_depth_output_nodes: Done')


def create_additional_optical_flow_output_nodes(scene,
                                                output_path=None,
                                                image_stem=None,
                                                leading_zeroes_template='#####'):

    logger.info('create_additional_optical_flow_output_nodes: ...')

    default_render_layer = scene.render.layers.get(scene.render.layers.active.name)
    default_render_layer.use_pass_vector = True

    default_render_layer.pass_alpha_threshold = 0
    scene.use_nodes = True

    scene_links = scene.node_tree.links

    scene_nodes = scene.node_tree.nodes
    default_render_layers_node = scene_nodes.get('Render Layers')

    optical_flow_output_node = scene_nodes.new('CompositorNodeOutputFile')
    optical_flow_output_node.format.file_format = 'OPEN_EXR'
    #optical_flow_output_node.format.use_zbuffer = True       # Store floats

    if output_path is not None:
        optical_flow_output_node.base_path = output_path
    if image_stem is not None:
        optical_flow_output_node.file_slots[0].path = image_stem + leading_zeroes_template
    scene_links.new(default_render_layers_node.outputs['Vector'],
                    optical_flow_output_node.inputs['Image'])

    logger.info('create_additional_optical_flow_output_nodes: Done')
    return optical_flow_output_node


def create_additional_depth_output_nodes(scene,
                                         output_path=None,
                                         image_stem=None,
                                         leading_zeroes_template='#####'):

    logger.info('create_additional_depth_output_nodes: ...')

    default_render_layer = scene.render.layers.get(scene.render.layers.active.name)

    default_render_layer.pass_alpha_threshold = 0
    scene.use_nodes = True
    scene_nodes = scene.node_tree.nodes
    scene_links = scene.node_tree.links

    default_render_layers_node = scene_nodes.get('Render Layers')

    depth_image_output_node = scene_nodes.new('CompositorNodeOutputFile')
    depth_image_output_node.format.file_format = 'OPEN_EXR'
    depth_image_output_node.format.use_zbuffer = True       # Store floats

    if output_path is not None:
        depth_image_output_node.base_path = output_path
    if image_stem is not None:
        depth_image_output_node.file_slots[0].path = image_stem + leading_zeroes_template
    scene_links.new(default_render_layers_node.outputs['Depth'],
                    depth_image_output_node.inputs['Image'])

    logger.info('create_additional_depth_output_nodes: Done')
    return depth_image_output_node


def create_additional_mask_output_nodes(scene,
                                        object_index,
                                        output_path=None,
                                        image_stem=None,
                                        leading_zeroes_template='#####'):

    logger.info('create_additional_mask_output_nodes: ...')
    # Make sure that the render layer passes the object index
    default_render_layer = scene.render.layers.get(scene.render.layers.active.name)
    # Add additional pass values
    # default_render_layer.use_pass_combined = True
    # default_render_layer.use_pass_mist = True
    # default_render_layer.use_pass_normal = True
    # default_render_layer.use_pass_vector = True
    # default_render_layer.use_pass_uv = True
    default_render_layer.use_pass_object_index = True
    # default_render_layer.use_pass_material_index = True
    # default_render_layer.use_pass_shadow = True

    # ========== IMPORTANT FOR TRANSPARENT MATERIALS =========
    default_render_layer.pass_alpha_threshold = 0

    scene.use_nodes = True
    scene_nodes = scene.node_tree.nodes
    scene_links = scene.node_tree.links

    default_render_layers_node = scene_nodes.get('Render Layers')

    mask_node = scene_nodes.new('CompositorNodeIDMask')
    mask_node.index = object_index
    mask_node.use_antialiasing = True
    image_output_node = scene_nodes.new('CompositorNodeOutputFile')
    if output_path is not None:
        image_output_node.base_path = output_path
    if image_stem is not None:
        image_output_node.file_slots[0].path = image_stem + leading_zeroes_template
    scene_links.new(
        default_render_layers_node.outputs['IndexOB'],
        mask_node.inputs['ID value'])
    scene_links.new(
        mask_node.outputs['Alpha'],
        image_output_node.inputs['Image'])

    logger.info('create_additional_mask_output_nodes: Done')

    return mask_node, image_output_node


def create_simple_material():

    logger.info('Create Simple Material: ...')
    simple_material = bpy.data.materials.new('simple_material')
    simple_material.use_nodes = True
    simple_material_nodes = simple_material.node_tree.nodes
    simple_material_links = simple_material.node_tree.links

    shader_node_diffuse_bsdf = simple_material_nodes.get(NodeUtility.DIFFUSE_BSDF)
    shader_node_diffuse_bsdf.inputs[0].default_value = [255,0,0, 1]

    return simple_material


def enable_backdrop(enable=True):
    logger.info('enable_backdrop: ...')
    # Enable backdrop
    for area in bpy.context.screen.areas:
        if area.type == 'NODE_EDITOR':
            for space in area.spaces:
                if space.type == 'NODE_EDITOR':
                    logger.info('Backdrop Enabled')
                    space.show_backdrop = enable
                    break
    logger.info('enable_backdrop: Done')


class NodeUtility:

    USE_MAP_COLOR_DIFFUSE = 'use_map_color_diffuse'
    USE_MAP_NORMAL = 'use_map_normal'

    DIFFUSE_BSDF = 'Diffuse BSDF'
    GLOSSY_BSDF = 'Glossy BSDF'
    TRANSPARENT_BSDF = 'Transparent BSDF'
    GLASS_BSDF = 'Glass BSDF'
    EMISSION = 'Emission'
    OBJECT_INFO = 'Object Info'
    MATERIAL_OUTPUT = 'Material Output'

    SHADER_NODE_RGB = 'ShaderNodeRGB'
    SHADER_NODE_MIX_RGB = 'ShaderNodeMixRGB'
    SHADER_NODE_EMISSION = 'ShaderNodeEmission'
    SHADER_NODE_BSDF_GLASS = 'ShaderNodeBsdfGlass'
    SHADER_NODE_OBJECT_INFO = 'ShaderNodeObjectInfo'

    @staticmethod
    def _collect_texture(type_to_texture_file_path, use_map_type, filepath):
        logger.debug('filepath: ' + filepath)
        if type_to_texture_file_path[use_map_type] is None:
            type_to_texture_file_path[use_map_type] = filepath
        else:
            logger.warning('Two Textures with the same use_type:')
            logger.warning('First: ' + use_map_type + ', ' + type_to_texture_file_path[use_map_type])
            logger.warning('Second: ' + use_map_type + ', ' + filepath)
            logger.warning('We use the first texture as : ' + use_map_type)

    @staticmethod
    def _get_blender_internal_texture_type_to_file_paths(material):

        some_other_name = material.name
        logger.debug(some_other_name)

        # fprint('material: ' + material.name)
        texture_name_set = set()
        texture_type_to_file_path = defaultdict(lambda: None)
        for texture_slot in material.texture_slots:

            if texture_slot:
                texture = texture_slot.texture

                texture_name_set.add(texture)
                # fprint('texture: ' + texture.name)
                if hasattr(texture, 'image'):
                    logger.debug('Material: ' + material.name + ', Texture: ' + texture.name)

                    logger.debug('use_map_color_diffuse: ' + str(texture_slot.use_map_color_diffuse))
                    logger.debug('use_map_normal: ' + str(texture_slot.use_map_normal))

                    # ==== Remark ====
                    # Relative paths start with '//' and are relative to the blend file.
                    # The prefix of paths to textures packed inside the .blend file are dependent on the original
                    # file path. For example <blend_file_folder>/textures/texture_file.ext, i.e. look like the
                    # following '//textures/<texturename>.<textureextension>'

                    if texture.image.packed_file is not None:
                        logger.debug('Image is packed')
                        # If the texture is packed, the file is definitively valid, otherwise check the file
                        image_is_valid = True
                    else:
                        logger.debug('Image is an external source')
                        image_is_valid = os.path.isfile(bpy.path.abspath(texture.image.filepath))

                    if image_is_valid:
                        if texture_slot.use_map_color_diffuse:
                            NodeUtility._collect_texture(texture_type_to_file_path,
                                                         NodeUtility.USE_MAP_COLOR_DIFFUSE,
                                                         texture.image.filepath)

                        elif texture_slot.use_map_normal:
                            NodeUtility._collect_texture(texture_type_to_file_path,
                                                         NodeUtility.USE_MAP_NORMAL,
                                                         texture.image.filepath)

        logger.info('texture_type_to_file_path: ' + str(texture_type_to_file_path))

        return texture_type_to_file_path

    @staticmethod
    def replace_bsdf_node_in_material(material, old_node, new_node, preceding_node=None, next_node=None):

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # we replace the oldf bsdf with a new one
        nodes.remove(old_node)

        if preceding_node is not None:
            links.new(preceding_node.outputs[0], new_node.inputs[0])

        if next_node is not None:
            links.new(new_node.outputs[0], next_node.inputs[0])

    @staticmethod
    def create_material_nodes_for_cycle_using_blender_internal_textures(material_default_bsdf_type=DIFFUSE_BSDF,
                                                                        transparent_default_bsdf_type=TRANSPARENT_BSDF):

        """

        :param material_default_bsdf_type: DIFFUSE_BSDF or GLOSSY_BSDF
        :param transparent_default_bsdf_type: TRANSPARENT_BSDF or GLASS_BSDF
        :return:
        """

        logger.info('create_material_nodes_for_cycle_using_blender_internal_textures: ...')

        bpy.context.scene.render.engine = 'CYCLES'

        # # each object has several material slots, which link to the materials provided in bpy.data.materials
        # for material in bpy.data.materials:

        for object in bpy.data.objects:

            logger.debug('object.name: ' + object.name)

            for material_slot in object.material_slots:
                material = material_slot.material

                # https://wiki.blender.org/index.php/Dev:Py/Scripts/Cookbook/Code_snippets/Nodes
                logger.info('material.name: ' + material.name)

                # change only blender internal materials (keep cycle materials as is)
                if not material.use_nodes:

                    logger.debug('Adding nodes ...')

                    # this adds by default a node "Material Output" and a node "Diffuse BSDF"
                    material.use_nodes = True

                    # get the "Diffuse BSDF" node
                    nodes = material.node_tree.nodes
                    links = material.node_tree.links

                    # this diffuse node does automatically inherit the color of the material
                    shader_node_diffuse_bsdf = nodes.get(NodeUtility.DIFFUSE_BSDF)
                    shader_node_material_output = nodes.get("Material Output")

                    # These texture file path should be valid
                    texture_type_to_file_path = NodeUtility._get_blender_internal_texture_type_to_file_paths(material)

                    # 1 Case: Material is just a texture
                    #         Image Texture -> Diffuse BSDF/Glossy BSDF -> Material Output
                    color_texture_file_path = texture_type_to_file_path[NodeUtility.USE_MAP_COLOR_DIFFUSE]
                    logger.debug('color_texture_file_path: ' + str(color_texture_file_path))

                    if color_texture_file_path is not None:

                        logger.debug('Converting Material With Texture: ' + color_texture_file_path)

                        logger.debug('Texture path is valid')

                        # test if the image texture node has already been created
                        shader_node_tex_image = nodes.get("Image Texture")
                        if not shader_node_tex_image:

                            shader_node_tex_image = nodes.new(type='ShaderNodeTexImage')
                            shader_node_tex_image.image = bpy.data.images.load(color_texture_file_path)

                            # link the nodes
                            links.new(shader_node_tex_image.outputs[0], shader_node_diffuse_bsdf.inputs[0])

                        # if material_default_bsdf_type == BICyclesMaterialConverter.GLOSSY_BSDF:
                        #
                        #     logger.debug('Replace Diffuse Material Node with Glossy Material Node' )
                        #     shader_node_glossy_bsdf = nodes.get(BICyclesMaterialConverter.GLOSSY_BSDF)
                        #     if not shader_node_glossy_bsdf:
                        #
                        #         shader_node_glossy_bsdf = nodes.new(type='ShaderNodeBsdfGlossy')
                        #
                        #         BICyclesMaterialConverter._replace_bsdf_node(material,
                        #                                                      old_node=shader_node_diffuse_bsdf,
                        #                                                      new_node=shader_node_glossy_bsdf,
                        #                                                      preceding_node=shader_node_tex_image,
                        #                                                      next_node=shader_node_material_output)

                    # 2 Case: Material is transparent
                    #         RGB -> Transparent BSDF/Glass BSDF -> Material Output
                    elif material.use_transparency:

                        logger.debug('Converting Transparent Material')

                        shader_node_transparent_or_glass_bsdf = nodes.get(transparent_default_bsdf_type)
                        if not shader_node_transparent_or_glass_bsdf:

                            if transparent_default_bsdf_type == NodeUtility.GLASS_BSDF:
                                shader_node_transparent_or_glass_bsdf = nodes.new(type='ShaderNodeBsdfGlass')
                            else:
                                shader_node_transparent_or_glass_bsdf = nodes.new(type='ShaderNodeBsdfTransparent')

                            shader_node_RGB = nodes.new(type='ShaderNodeRGB')

                            NodeUtility.replace_bsdf_node_in_material(material,
                                                                      old_node=shader_node_diffuse_bsdf,
                                                                      new_node=shader_node_transparent_or_glass_bsdf,
                                                                      preceding_node=shader_node_RGB,
                                                                      next_node=shader_node_material_output)

                    else:
                        logger.debug('Converting Material With Simple Color')
                        # by default there is just a diffuse bsdf created using the color of the material

                        if material_default_bsdf_type == NodeUtility.GLOSSY_BSDF:

                            logger.debug('Replace Diffuse Material Node with Glossy Material Node')
                            shader_node_glossy_bsdf = nodes.get(NodeUtility.GLOSSY_BSDF)
                            if not shader_node_glossy_bsdf:
                                shader_node_glossy_bsdf = nodes.new(type='ShaderNodeBsdfGlossy')

                                NodeUtility.replace_bsdf_node_in_material(material,
                                                                          old_node=shader_node_diffuse_bsdf,
                                                                          new_node=shader_node_glossy_bsdf,
                                                                          preceding_node=None,
                                                                          next_node=shader_node_material_output)

                else:
                    logger.debug('Material has already a node ...')

        logger.info('create_material_nodes_for_cycle_using_blender_internal_textures: Done')