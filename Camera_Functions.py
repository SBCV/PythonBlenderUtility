import bpy
import numpy as np
from Utility.Types.Camera import Camera
from Utility.Math.Conversion.Conversion_Collection import convert_opengl_to_computer_vision_camera
from Utility.Logging_Extension import logger


def get_calibration_mat(blender_camera):
    #logger.info('get_calibration_mat: ...')
    scene = bpy.context.scene
    render_resolution_width = scene.render.resolution_x
    render_resolution_height = scene.render.resolution_y
    focal_length_in_mm = float(blender_camera.data.lens)
    sensor_width_in_mm = float(blender_camera.data.sensor_width)
    focal_length_in_pixel = \
        float(max(scene.render.resolution_x, scene.render.resolution_y)) * \
        focal_length_in_mm / sensor_width_in_mm

    max_extent = max(render_resolution_width, render_resolution_height)
    p_x = render_resolution_width / 2.0 - blender_camera.data.shift_x * max_extent
    p_y = render_resolution_height / 2.0 - blender_camera.data.shift_y * max_extent

    calibration_mat = Camera.compute_calibration_mat(
        focal_length_in_pixel, cx=p_x, cy=p_y)

    #logger.info('get_calibration_mat: Done')
    return calibration_mat


def get_computer_vision_camera_matrix(blender_camera):

    """
    Blender and Computer Vision Camera Coordinate Frame Systems (like VisualSfM, Bundler)
    differ by their y and z axis
    :param blender_camera:
    :return:
    """

    # Only if the objects have a scale of 1,
    # the 3x3 part of the corresponding matrix_world contains a pure rotation
    # Otherwise it also contains scale or shear information
    if tuple(blender_camera.scale) != (1, 1, 1):
        logger.vinfo('blender_camera.scale', blender_camera.scale)
        assert False

    opengl_cam_mat = np.array(blender_camera.matrix_world)
    computer_vision_cam_mat = convert_opengl_to_computer_vision_camera(
        opengl_cam_mat)

    return computer_vision_cam_mat
