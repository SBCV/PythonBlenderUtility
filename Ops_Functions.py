from Utility.Logging_Extension import logger
import bpy


def configure_scene_for_basic_ops():
    logger.info('configure_scene_for_basic_ops: ...')
    # =============================== FIX BLENDER BUG ============================
    # OPS CAN ONLY BE EXECUTED IF THE SELECTED OBJECT IS NOT IN EDIT OR POSE MODE
    # ============================================================================
    # Select an object (WHICH IS NOT IN EDIT OR POSE MODE)
    # to ensure that 'bpy.ops.object.select_all(action='DESELECT')' can be called without errors
    dummy_empty_name = 'Dummy_Empty'

    if dummy_empty_name not in bpy.data.objects.items():
        dummy_empty = bpy.data.objects.new(dummy_empty_name, None)
        bpy.context.scene.objects.link(dummy_empty)

    logger.info('dummy_empty: ' + str(bpy.data.objects[dummy_empty_name]))
    # OBJECT MUST BE LINKED, otherwise it cant be the active object

    bpy.context.scene.objects.active = bpy.data.objects[dummy_empty_name]

    logger.info('bpy.context.scene.objects.active: ' + str(bpy.context.scene.objects.active))

    logger.info('configure_scene_for_basic_ops: Done')


def make_object_active(target_object_name):
    """
    Makes the target object the active object and selects it
    """
    bpy.data.objects[target_object_name].hide = False
    bpy.data.objects[target_object_name].select = True
    bpy.context.scene.objects.active = bpy.data.objects[target_object_name]


def _select_object_for_ops(target_object_name, config_scene_for_basic_ops=True):
    """
    After execution, only the target object is selected and active
    """
    if config_scene_for_basic_ops:
        configure_scene_for_basic_ops()
    bpy.ops.object.select_all(action='DESELECT')
    make_object_active(target_object_name)


def set_mode(active_object_name, mode, configure_scene_for_basic_ops=True):

    """
    :param active_object_name
    :param mode: mode='OBJECT', mode='EDIT', mode='POSE'
    :param configure_scene_for_basic_ops
    :return:
    """

    logger.info('set_mode: ...')
    logger.info('target_object_name: ' + str(active_object_name))
    logger.info('mode: ' + str(mode))
    _select_object_for_ops(active_object_name, configure_scene_for_basic_ops)
    # Can't set mode if object is invisible
    assert not bpy.data.objects[active_object_name].hide
    previous_mode = bpy.data.objects[active_object_name].mode
    bpy.ops.object.mode_set(mode=mode, toggle=False)
    logger.info('set_mode: Done')
    return previous_mode


def check_ops_prerequisites(active_object_name, selected_object_names):

    logger.info('check_ops_prerequisites: ...')

    # Check if objects are all visible, otherwise a poll error will be thrown
    assert bpy.data.objects[active_object_name].hide == False
    for selected_obj_name in selected_object_names:
        assert bpy.data.objects[selected_obj_name].hide == False

    # Check if ALL objects are in the same layer, otherwise the execution of the operation will have no effect

    true_active_object_layers = set([index for index in range(0, 20)
                                     if bpy.data.objects[active_object_name].layers[index]])
    true_layers_per_selected_object = []
    for selected_obj_name in selected_object_names:
        true_selected_object_layers = set([index for index in range(0, 20)
                                           if bpy.data.objects[selected_obj_name].layers[index]])
        true_layers_per_selected_object.append(true_selected_object_layers)

    common_layers = set.intersection(*([true_active_object_layers] + true_layers_per_selected_object))
    if len(common_layers) == 0:
        logger.error('COMMON_LAYERS: ' + str(common_layers) + ' EMPTY, THIS MUST NOT HAPPEN')
    assert len(common_layers) > 0

    logger.info('check_ops_prerequisites: Done')
