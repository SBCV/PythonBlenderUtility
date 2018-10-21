import os
import bpy

from Utility.Logging_Extension import logger


def find_3dview_space():
    # Find 3D_View window and its scren space
    area = None
    for a in bpy.data.window_managers[0].windows[0].screen.areas:
        if a.type == 'VIEW_3D':
            area = a
            break
    if area:
        space = area.spaces[0]
    else:
        space = bpy.context.space_data
    return space


def opengl_hide_elements_for_rendering():
    space = find_3dview_space()
    space.show_floor = False
    space.show_relationship_lines = False
    space.show_outline_selected = False
    space.show_axis_x = False
    space.show_axis_y = False
    space.show_axis_z = False


def opengl_set_camera_vizualization_color(color):
    """
    This function call has no effect, if the camera belongs to a group
    :param color: e.g. color=(0.0, 1.0, 1.0)
    :return:
    """
    bpy.context.user_preferences.themes[0].view_3d.camera = color


def opengl_set_object_grouped_active_vizualization_color(color):
    """
    :param color: e.g. color=(0.0, 1.0, 1.0)
    :return:
    """
    bpy.context.user_preferences.themes[0].view_3d.object_grouped_active = color


def opengl_set_object_grouped_vizualization_color(color):
    """
    :param color: e.g. color=(0.0, 1.0, 1.0)
    :return:
    """
    bpy.context.user_preferences.themes[0].view_3d.object_grouped = color


def set_3D_view_to_camera(camera_name):
    logger.info('set_3D_view_to_camera : ...')
    result_cam = bpy.data.objects[camera_name]
    bpy.context.scene.camera = result_cam
    area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
    area.spaces[0].region_3d.view_perspective = 'CAMERA'
    logger.info('set_3D_view_to_camera : Done')


def _log_animation_render_settings():
    logger.info('_log_animation_render_settings: ...')
    scene = bpy.context.scene
    logger.info('bpy.context.scene.cycles.device: ' + str(bpy.context.scene.cycles.device))
    logger.info('scene.render.filepath: ' + str(scene.render.filepath))
    logger.info('scene.render.resolution_percentage: ' + str(scene.render.resolution_percentage))
    logger.info('scene.render.resolution_x: ' + str(scene.render.resolution_x))
    logger.info('scene.render.resolution_y: ' + str(scene.render.resolution_y))
    logger.info('bpy.context.scene.render.tile_x: ' + str(bpy.context.scene.render.tile_x))
    logger.info('bpy.context.scene.render.tile_y: ' + str(bpy.context.scene.render.tile_y))
    logger.info('scene.render.image_settings.file_format: ' + str(scene.render.image_settings.file_format))
    logger.info('scene.render.image_settings.quality: ' + str(scene.render.image_settings.quality))
    logger.info('scene.cycles.sample_clamp_direct: ' + str(scene.cycles.sample_clamp_direct))
    logger.info('scene.cycles.sample_clamp_indirect: ' + str(scene.cycles.sample_clamp_indirect))
    logger.info('scene.cycles.caustics_reflective: ' + str(scene.cycles.caustics_reflective))
    logger.info('scene.cycles.caustics_refractive: ' + str(scene.cycles.caustics_refractive))
    logger.info('scene.cycles.samples: ' + str(scene.cycles.samples))
    logger.info('_log_animation_render_settings: Done')


def set_render_output_path(path_to_output_images,
                           image_stem='frame',
                           leading_zeroes_template='#####',
                           frame_number=None):

    scene = bpy.context.scene

    if frame_number is None:
        # the amount of '#' define the padding zeros
        scene.render.filepath = os.path.join(
            path_to_output_images,
            image_stem + leading_zeroes_template)
    else:
        zero_leading_str = str(frame_number).zfill(len(leading_zeroes_template))
        scene.render.filepath = os.path.join(
            path_to_output_images,
            image_stem + zero_leading_str)


def configure_render_settings(
        number_samples_in_cycles=128,
        render_resolution_width=1920,
        render_resolution_height=1080,
        resolution_percentage=100,
        render_tile_x=480,  # 1920 / 4 = 480
        render_tile_y=270,  # 1080 / 4 = 270
        sample_clamp_direct=5.0,  # 0 means disabled
        sample_clamp_indirect=5.0,  # 0 means disabled
        caustics_reflective=True,
        caustics_refractive=True,
        transparent_max_bounces=4,
        transparent_min_bounces=0,
        max_bounces=6,
        min_bounces=0,
        diffuse_bounces=2,
        glossy_bounces=2,
        transmission_bounces=6,
        use_denoising=True
                              ):

    logger.info('configure_render_settings: ...')

    scene = bpy.context.scene

    # https://docs.blender.org/manual/en/dev/render/blender_render/settings/index.html

    # RENDER SETTINGS (RENDER SPEED)
    # https://www.blenderguru.com/articles/4-easy-ways-to-speed-up-cycles/
    # Make sure GPU RENDERING IS ENABLED:
    #   * Go to "File/User Preferences...",
    #       * Click on CUDA (must be blue)
    #       * Make sure the graphic cards are selected (dark grey)
    #   * If the graphic cards are not selected (light grey) bpy.context.scene.device = 'GPU' can't be used
    scene.cycles.device = 'GPU'

    # ======= PERSISTENT DATA ==================
    # This will almost half the render speed for the second, third, ... frame
    scene.render.use_persistent_data = True
    # ===========================================

    scene.render.resolution_percentage = resolution_percentage

    scene.render.resolution_x = render_resolution_width
    scene.render.resolution_y = render_resolution_height

    # Adjust the tile size to the render resolution !!! (Tiles fit in image)
    scene.render.tile_x = render_tile_x  # 1920 / 4 = 480
    scene.render.tile_y = render_tile_y  # 1080 / 4 = 270

    scene.render.image_settings.file_format = 'JPEG'
    scene.render.image_settings.quality = 95

    scene.cycles.sample_clamp_direct = sample_clamp_direct           # 0 means disabled
    scene.cycles.sample_clamp_indirect = sample_clamp_indirect       # 0 means disabled

    scene.cycles.caustics_reflective = caustics_reflective
    scene.cycles.caustics_refractive = caustics_refractive

    scene.cycles.transparent_max_bounces = transparent_max_bounces
    scene.cycles.transparent_min_bounces = transparent_min_bounces

    scene.cycles.max_bounces = max_bounces
    scene.cycles.min_bounces = min_bounces

    scene.cycles.diffuse_bounces = diffuse_bounces
    scene.cycles.glossy_bounces = glossy_bounces

    scene.cycles.transmission_bounces = transmission_bounces

    scene.cycles.samples = number_samples_in_cycles

    scene.render.layers[0].cycles.use_denoising = use_denoising

    logger.vinfo('use_denoising', use_denoising)

    _log_animation_render_settings()

    logger.info('configure_render_settings: Done')


def render_scene_from_virtual_camera_positions(output_file_path):
    logger.info('render_scene_from_virtual_camera_positions: ...')

    scene = bpy.context.scene
    # make the background transparent
    scene.render.image_settings.color_mode = 'RGBA'  # in ['BW', 'RGB', 'RGBA']
    scene.render.image_settings.file_format = 'PNG'  # in ['JPEG', 'PNG', ...]
    scene.render.alpha_mode = 'TRANSPARENT'  # in ['TRANSPARENT', 'SKY']
    # makes sure that the images are created using the original image size
    scene.render.resolution_percentage = 100

    current_camera = bpy.context.scene.camera
    logger.info('Current camera: ' + str(current_camera))

    # set the material to "shadeless"
    for data in bpy.data.materials:
        data.use_shadeless = True
        data.translucency = 0.0

    for current_object in scene.objects:
        if current_object.type == 'CAMERA':
            # print(current_object.name)

            # set the current camera as active camera
            bpy.context.scene.camera = current_object
            camera_name = current_object.name
            # adjust the starting index
            scene.render.filepath = os.path.join(output_file_path, camera_name)

            # render the image seen from the current camera and write it to disc
            bpy.ops.render.render(write_still=True)


def configure_stereo_camera_settings(camera_name, baseline, left_suffix='_left', right_suffix='_right'):

    """
    The baseline is provided in Blender Units
    :param baseline:
    :param left_suffix:
    :param right_suffix:
    :return:
    """

    scene = bpy.context.scene
    scene.render.use_multiview = True
    scene.render.views['left'].file_suffix = left_suffix
    scene.render.views['right'].file_suffix = right_suffix

    camera = bpy.data.objects[camera_name]

    camera.data.stereo.convergence_mode = 'PARALLEL'
    camera.data.stereo.interocular_distance = baseline