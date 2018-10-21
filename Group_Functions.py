import bpy
from BlenderUtility.Object_Functions import move_object_to_layer


def move_group_to_layer(group_name, layer_id):
    grp = bpy.data.groups[group_name]

    for obj in grp.objects:
        move_object_to_layer(obj.name, layer_id)
