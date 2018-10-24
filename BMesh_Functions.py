import bpy

def add_faces_of_object_to_bmesh(some_bmesh, source_object, some_matrix_world=None):

    # https://docs.blender.org/api/2.78a/bmesh.types.html#bmesh.types.BMesh

    source_object_faces_object = [[v for v in p.vertices] for p in source_object.data.polygons]
    source_object_vertices_object_coord = [v.co for v in source_object.data.vertices]

    if some_matrix_world is None:
        some_matrix_world = source_object.matrix_world

    vertices_world_coord = [(some_matrix_world * v_coord.to_4d()).to_3d() for v_coord in
                            source_object_vertices_object_coord]

    # append pydata to ground_volume_mesh_data
    mesh_data_temp = bpy.data.meshes.new('unused_name')
    # let faces take care of edges
    mesh_data_temp.from_pydata(
        vertices=vertices_world_coord,
        edges=[],
        faces=source_object_faces_object)
    some_bmesh.from_mesh(mesh_data_temp)