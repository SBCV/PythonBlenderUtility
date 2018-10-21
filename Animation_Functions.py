import os

import bpy
import numpy as np
from BlenderUtility.Camera_Functions import get_calibration_mat
from BlenderUtility.Camera_Functions import get_computer_vision_camera_matrix
from BlenderUtility.Curve_Functions import get_curve_length
from BlenderUtility.Object_Functions import join_copy_of_objects
from BlenderUtility.Import_Export_Functions import export_ply
from Utility.File_Handler.NVM_File_Handler import NVMFileHandler
from Utility.File_Handler.PLY_File_Handler import PLYFileHandler
from Utility.File_Handler.Trajectory_File_Handler import TrajectoryFileHandler
from Utility.Logging_Extension import logger
from Utility.Types.Camera import Camera
from Utility.Types.Camera_Object_Trajectory import CameraObjectTrajectory
from Utility.Types.Point import Point
from Utility.Types.Stereo_Camera import StereoCamera


def clear_animation_data(object_name):

    """ Deletes (also) previously inserted keyframes """

    obj = bpy.data.objects[object_name]
    obj.animation_data_clear()
    bpy.context.scene.update()


def set_animation_extrapolation(object_name, fcurve_extrapolation_type='LINEAR'):
    logger.info('set_animation_extrapolation: ...')

    # bpy.ops.action.extrapolation_type(type='LINEAR')
    logger.info('object_name: ' + str(object_name))
    obj = bpy.data.objects[object_name]
    for fcurve in obj.animation_data.action.fcurves:
        logger.info(fcurve)
        fcurve.extrapolation = fcurve_extrapolation_type  # Set extrapolation type
    logger.info('set_animation_extrapolation: Done')


def configure_curve_animation(number_frames_per_meter, curve_names, unit_scale_factor=1.0):
    logger.info('configure_curve_animation: ...')
    possible_frame_numbers = []
    for curve_obj in bpy.data.objects:
        if curve_obj.type == 'CURVE':
            # don't confuse curve data names with curve object names,
            # each curve object has a corresponding a data entry
            curve_name = curve_obj.data.name
            if curve_name in curve_names:
                logger.info('curve_name: ' + curve_name)
                curve_length = get_curve_length(curve_obj)
                logger.info('curve_length: ' + str(curve_length))
                curve_number_frames = int(curve_length * float(number_frames_per_meter) * unit_scale_factor)
                possible_frame_numbers.append(curve_number_frames)

    logger.info('possible_frame_numbers: ' + str(possible_frame_numbers))
    average_frame_number = int(sum(possible_frame_numbers) / len(possible_frame_numbers))
    logger.info('average_frame_number: ' + str(average_frame_number))

    for curve_obj in bpy.data.objects:
        if curve_obj.type == 'CURVE':
            # don't confuse curve (i.e. data) names with object names
            # (each curve has a corresponding object)
            curve_name = curve_obj.data.name
            if curve_name in curve_names:
                curve_data = bpy.data.curves[curve_name]
                curve_data.path_duration = average_frame_number
    logger.info('configure_curve_animation: Done')
    return average_frame_number


def configure_scene_animation(frame_end_number, fps=12):

    """
    ======== Note ========
    It is NOT possible to set a starting frame number
    Since all frames must be animated to get the correct object pose at frame X
    (And the animation method is called later)
    ======== ======== ========

    # BU = blender units
    # 1 meter == 0.01 BU, 10 meters == 0.1 BU, 100 meters = 1 BU
    :param number_frames_per_meter:
    :param curve_names:
    :param fps:
    :return:
    """

    logger.info('configure_scene_animation: ...')

    bpy.context.scene.frame_end = frame_end_number
    bpy.context.scene.render.fps = fps

    # set the frame index to 0, to reset any previous pose
    bpy.context.scene.frame_current = 0
    # the first index is the starting index
    bpy.context.scene.frame_current = 1

    logger.info('configure_scene_animation: Done')


def collect_camera_object_trajectory_information(virtual_camera_name,
                                                 render_stereo_camera,
                                                 stereo_camera_baseline,
                                                 car_body_name):
    logger.info('collect_camera_object_trajectory_information: ...')
    scene = bpy.context.scene

    blender_camera = bpy.data.objects[virtual_camera_name]
    if not scene.camera:
        scene.camera = blender_camera

    camera_object_trajectory = CameraObjectTrajectory()

    # Gather the blender_camera and object transformations at each frame
    for _frm_idx in range(scene.frame_end):

        # We start the animation at frame
        corrected_frame_index = _frm_idx + 1
        # Blender indexes frames from 1, ..., n
        # Setting the current frame index is required to access
        # the correct values with blender_camera.matrix_world
        bpy.context.scene.frame_set(corrected_frame_index)

        current_frame_stem = 'frame' + str(corrected_frame_index).zfill(5)
        current_frame_name =  current_frame_stem + '.jpg'

        logger.vinfo('current_frame_name', current_frame_name)

        # Only if the objects have a scale of 1,
        # the 3x3 part of the corresponding matrix_world contains a pure rotation
        # Otherwise it also contains scale or shear information
        if tuple(blender_camera.scale) != (1, 1, 1):
            logger.vinfo('blender_camera.scale', blender_camera.scale)
            assert False

        calibration_mat = get_calibration_mat(blender_camera)
        rotated_camera_matrix_around_x_by_180 = get_computer_vision_camera_matrix(
            blender_camera)
        logger.vinfo('rotated_camera_matrix_around_x_by_180', rotated_camera_matrix_around_x_by_180)

        cam = Camera()
        cam.set_4x4_cam_to_world_mat(rotated_camera_matrix_around_x_by_180)
        cam.set_calibration(calibration_mat, 0)

        if render_stereo_camera:
            stereo_cam = StereoCamera(
                left_camera=cam, baseline=stereo_camera_baseline)
            stereo_cam.left_camera.file_name = current_frame_stem + '_left.jpg'
            stereo_cam.right_camera.file_name = current_frame_stem + '_right.jpg'
            camera_object_trajectory.set_camera(
                    current_frame_name, stereo_cam)
        else:
            cam.file_name = current_frame_name
            camera_object_trajectory.set_camera(
                current_frame_name, cam)

        # It is important to access the car_body for each frame
        # to get the most recent animated position
        car_body = bpy.data.objects[car_body_name]
        if tuple(car_body.scale) != (1, 1, 1):
            logger.vinfo('car_body_name', car_body_name)
            logger.vinfo('car_body.scale', car_body.scale)
            assert False

        # Make sure matrix world is up to date
        bpy.context.scene.update()
        object_matrix_world = np.array(car_body.matrix_world)

        camera_object_trajectory.set_object_matrix_world(
            current_frame_name, object_matrix_world)

    bpy.context.scene.frame_set(1)
    logger.info('collect_camera_object_trajectory_information: Done')
    return camera_object_trajectory


def store_animation_ground_truth_mesh(car_body_name,
                                      path_ground_truth_mesh_folder,
                                      add_static_wheels_to_gt_mesh,
                                      car_rig_stem,
                                      car_model_tire_suffix_fl,
                                      car_model_tire_suffix_fr,
                                      car_model_tire_suffix_bl,
                                      car_model_tire_suffix_br):

    scene = bpy.context.scene
    for _frm_idx in range(scene.frame_end):

        # We start the animation at frame
        corrected_frame_index = _frm_idx + 1
        # Blender indexes frames from 1, ..., n
        # Setting the current frame index is required to access
        # the correct values with blender_camera.matrix_world
        bpy.context.scene.frame_set(corrected_frame_index)

        current_frame_name = 'frame' + str(corrected_frame_index).zfill(5) + '.jpg'

        # The matrix world entries are correct,
        # however the original car model may have a different origin
        # (i.e. not at the center of the object)
        # Therefore, it is better to extract the the position of the car
        # during the animation on the fly

        if add_static_wheels_to_gt_mesh:
            car_body_with_wheels = join_copy_of_objects(
                [car_body_name,
                 car_rig_stem + car_model_tire_suffix_fl,
                 car_rig_stem + car_model_tire_suffix_fr,
                 car_rig_stem + car_model_tire_suffix_bl,
                 car_rig_stem + car_model_tire_suffix_br],
                joined_name=car_body_name + '_joined')

            export_ply(
                object_name=car_body_with_wheels.name,
                path_to_ply=os.path.join(
                    path_ground_truth_mesh_folder,
                    current_frame_name + '.ply'))
            bpy.data.objects.remove(car_body_with_wheels, True)
        else:
            export_ply(
                object_name=car_body_name,
                path_to_ply=os.path.join(
                    path_ground_truth_mesh_folder,
                    current_frame_name + '.ply'))

    bpy.context.scene.frame_set(1)


def write_camera_centers_as_ply(camera_object_trajectory, camera_trajectory_ply_file_path):
    camera_centers = []
    for frame_name in camera_object_trajectory.get_frame_names_sorted():
        cam = camera_object_trajectory.get_camera(frame_name)

        if cam.is_monocular_cam():
            camera_centers.append(cam.get_camera_center())
        else:
            camera_centers.append(cam.get_left_camera().get_camera_center())
            camera_centers.append(cam.get_right_camera().get_camera_center())

    camera_center_points = []
    for center in camera_centers:
        camera_center_points.append(Point(
            coord=center,
            color=(0, 255, 0)))

    PLYFileHandler.write_ply_file(
        ofp=camera_trajectory_ply_file_path,
        vertices=camera_center_points,
        plain_text_output=True)     # Binary output does only work


def write_cameras_as_nvm(camera_object_trajectory, camera_trajectory_nvm_file_path):

    cameras = []
    for frame_name in camera_object_trajectory.get_frame_names_sorted():
        cam = camera_object_trajectory.get_camera(frame_name)
        if cam.is_monocular_cam():
            cameras.append(cam)
        else:
            cameras.append(cam.get_left_camera())
            cameras.append(cam.get_right_camera())

    NVMFileHandler.write_nvm_file(
        output_nvm_file_name=camera_trajectory_nvm_file_path,
        cameras=cameras,
        points=[])


def write_animation_ground_truth_to_disc(
        virtual_camera_name,
        car_body_name,
        path_to_output_render_folder,
        output_file_folder='ground_truth_files',
        output_animation_transformation_txt_file_name='animation_transformations.txt',
        output_camera_trajectory_ply_file_name='camera_trajectory.ply',
        output_camera_trajectory_nvm_file_name='output_camera_trajectory_nvm_file_name',
        write_animation_ground_truth_mesh=True,
        output_ground_truth_mesh_folder='object_ground_truth_in_world_ground_truth_coordinates',
        render_stereo_camera=False,
        stereo_camera_baseline=None,
        add_static_wheels_to_gt_mesh=False,
        car_rig_stem=None,
        car_model_tire_suffix_fl=None,
        car_model_tire_suffix_fr=None,
        car_model_tire_suffix_bl=None,
        car_model_tire_suffix_br=None
):

    logger.info('write_animation_ground_truth_to_disc: ...')
    path_to_ground_truth_folder = os.path.join(
        path_to_output_render_folder, output_file_folder)
    if not os.path.isdir(path_to_ground_truth_folder):
        os.mkdir(path_to_ground_truth_folder)
    path_ground_truth_mesh_folder = os.path.join(
        path_to_ground_truth_folder, output_ground_truth_mesh_folder)
    if not os.path.isdir(path_ground_truth_mesh_folder):
        os.mkdir(path_ground_truth_mesh_folder)
    animation_transformation_file_path = os.path.join(
        path_to_ground_truth_folder, output_animation_transformation_txt_file_name)
    camera_trajectory_ply_file_path = os.path.join(
        path_to_ground_truth_folder, output_camera_trajectory_ply_file_name)
    camera_trajectory_nvm_file_path = os.path.join(
        path_to_ground_truth_folder, output_camera_trajectory_nvm_file_name)


    camera_object_trajectory = collect_camera_object_trajectory_information(
        virtual_camera_name,
        render_stereo_camera,
        stereo_camera_baseline,
        car_body_name)

    if write_animation_ground_truth_mesh:
        store_animation_ground_truth_mesh(
            car_body_name,
            path_ground_truth_mesh_folder,
            add_static_wheels_to_gt_mesh,
            car_rig_stem,
            car_model_tire_suffix_fl,
            car_model_tire_suffix_fr,
            car_model_tire_suffix_bl,
            car_model_tire_suffix_br
        )

    # In Blender the stereo camera uses by default the position
    # of the monocular camera as left camera
    # To visualize both cameras in the 3D view
    #   * Enable "Views" for the current Renderlayer
    #   * Then an entry "Stereoscopy" appears in the toolbar of the "3D View"
    #   * Then click on "Cameras" under "Stereoscopy"
    # See also:
    # https://docs.blender.org/manual/de/dev/render/workflows/multiview/usage.html#viewport-stereo-3d
    TrajectoryFileHandler.write_camera_and_object_trajectory_file(
        path_to_trajectory_file=animation_transformation_file_path,
        camera_object_trajectory=camera_object_trajectory,
        camera_to_world_transformation_name=virtual_camera_name,
        object_to_world_transformation_name=car_body_name)

    write_camera_centers_as_ply(
        camera_object_trajectory,
        camera_trajectory_ply_file_path)

    write_cameras_as_nvm(
        camera_object_trajectory,
        camera_trajectory_nvm_file_path)

    logger.info('write_animation_ground_truth_to_disc: Done')




