from math import radians

import bpy
import numpy as np
from BlenderUtility.Object_Functions import set_constraint_track_to
from BlenderUtility.Object_Functions import add_obj
from Utility.Math.Geometry.Geometry_Collection import GeometryCollection
from Utility.Logging_Extension import logger


class VertexType:
    SPHERE = 'SPHERE'
    CUBE = 'CUBE'
    PLANE = 'PLANE'


class PointCloudTool:

    # ===== Performance in Blender ========
    # http://blender.stackexchange.com/questions/7358/python-performance-with-blender-operators
    #   Most operators cause implicit scene updates. It means that every object in the scene is checked and updated
    # if necessary. If you add e.g. mesh primitives using bpy.ops.mesh.primitive_cube_add() in a loop, every iteration
    # creates a new cube, starts a scene update and Blender iterates over all objects in the scene and updates objects
    # if it has to.
    # there are n (n + 1) / 2 checks performed, where n is the number of objects => THIS IS NOT LINEAR!
    # Solution: Replace the code with some lower api code to improve performance

    @staticmethod
    def make_material(name, diffuse_pseudo_color, specular_color=None, alpha=1):

        mat = bpy.data.materials.new(name)
        mat.diffuse_color = diffuse_pseudo_color
        mat.diffuse_shader = 'LAMBERT'
        mat.diffuse_intensity = 1.0

        if specular_color is not None:
            # we do not want specular effects
            mat.specular_color = specular_color
            mat.specular_shader = 'COOKTORR'
            mat.specular_intensity = 1
        else:
            mat.specular_intensity = 0

        mat.alpha = alpha
        mat.ambient = 1
        return mat

    @staticmethod
    def create_vertex(point_cloud, scale_factor, vertex_type=VertexType.CUBE):

        if vertex_type == VertexType.SPHERE:
            bpy.ops.mesh.primitive_uv_sphere_add()
        elif vertex_type == VertexType.CUBE:
            bpy.ops.mesh.primitive_cube_add()
        else:
            bpy.ops.mesh.primitive_plane_add()

        current_vertex = bpy.context.active_object
        current_vertex.parent = point_cloud
        current_vertex.scale = (scale_factor, scale_factor, scale_factor)

        return current_vertex

    @staticmethod
    def add_point_cloud_as_mesh(points, point_cloud_name):
        point_cloud_mesh = bpy.data.meshes.new(point_cloud_name)
        point_cloud_mesh.update()
        point_cloud_mesh.validate()

        point_world_coordinates = [tuple(point.coord) for point in points]

        point_cloud_mesh.from_pydata(point_world_coordinates, [], [])
        point_cloud_obj = add_obj(point_cloud_mesh, point_cloud_name)

        # point_cloud_obj.matrix_world = Matrix.Rotation(radians(0), 4, 'X')
        return point_cloud_obj

    @staticmethod
    def toggle_hide_point_cloud(point_obj_names, hide_value):
        for point_obj_name in point_obj_names:
            bpy.data.objects[point_obj_name].hide = hide_value
            bpy.data.objects[point_obj_name].hide_render = hide_value

    @staticmethod
    def update_point_cloud_object_positions(points, point_obj_names):
        """ This method assumes the point cloud is represented by a set of points """
        assert len(points) == len(point_obj_names)
        for point, point_obj_name in zip(points, point_obj_names):
            bpy.data.objects[point_obj_name].location = point.coord

    @staticmethod
    def update_point_cloud_mesh(points, point_cloud_mesh_name):
        """ This method assumes the point cloud is represented by a single mesh (with a particle system) """
        point_cloud_vertices = bpy.data.objects[point_cloud_mesh_name].data.vertices
        for index, point in enumerate(points):
            point_cloud_vertices[index].co = point.coord


    @staticmethod
    def add_point_cloud_using_dupliverts(points,
                                         add_meshes_at_vertex_positions,
                                         mesh_type=VertexType.CUBE,
                                         mesh_scale=1.0):
        """
        http://blender.stackexchange.com/questions/1829/is-it-possible-to-render-vertices-in-blender
        :param points:
        :param add_meshes_at_vertex_positions:
        :param mesh_type: VertexType.PLANE, VertexType.CUBE, VertexType.SPHERE
        :param mesh_scale:
        :return:
        """
        logger.info("add_point_cloud_using_dupliverts: ...")

        point_obj_names = []

        if add_meshes_at_vertex_positions:
            bpy.ops.object.select_all(action='DESELECT')
            if mesh_type == VertexType.PLANE:
                bpy.ops.mesh.primitive_plane_add(radius=mesh_scale)
            elif mesh_type == VertexType.CUBE:
                bpy.ops.mesh.primitive_cube_add(radius=mesh_scale)
            elif mesh_type == VertexType.SPHERE:
                bpy.ops.mesh.primitive_uv_sphere_add(size=mesh_scale)
            else:
                bpy.ops.mesh.primitive_uv_sphere_add(size=mesh_scale)
            viz_mesh = bpy.context.object

            for index, point in enumerate(points):

                if index % 1000 == 0:
                    logger.info("Creating Representation for Vertex " + str(index) + " of " + str(len(points)))
                coord = tuple(point.coord)
                color = tuple(point.color)  # must be in between 0 and 1

                ob = viz_mesh.copy()
                ob.location = coord
                bpy.context.scene.objects.link(ob)

                mat = bpy.data.materials.new("materialName")
                mat.diffuse_color = [color[0]/255.0, color[1]/255.0, color[2]/255.0]
                ob.active_material = mat
                ob.material_slots[0].link = 'OBJECT'
                ob.material_slots[0].material = mat
                point_obj_names.append(ob.name)
            bpy.context.scene.update()

            # Delete the original primitive
            bpy.data.objects.remove(bpy.data.objects[viz_mesh.name], True)
        bpy.ops.object.select_all(action='DESELECT')
        logger.info("add_point_cloud_using_dupliverts: Done")
        return point_obj_names

    @staticmethod
    def add_point_cloud_using_parent(points,
                                     point_cloud_name,
                                     recenter_point_cloud_around_centroid=False,
                                     rotation_angles_degrees=None,
                                     scale_factor=0.01,
                                     vertex_type=VertexType.CUBE,
                                     camera_name_for_billboarding=None):

        logger.info('Add Point Cloud: ...')

        """
        Determine the rotation_angles by running the script without a rotation argument,
        apply the transformation in blender, read the Rotation values, and provide them as argument in the second run
        :param points:
        :param rotation_angles_degrees:
        :param scale_factor:
        :return:
        """

        # create an empty object, which will represent the point cloud / be the parent of the points
        point_cloud = bpy.data.objects.new(point_cloud_name, None)
        point_cloud.location = [0, 0, 0]
        bpy.context.scene.objects.link(point_cloud)

        if rotation_angles_degrees is not None: # custom rotation of the object
            point_cloud.rotation_euler[0] = radians(rotation_angles_degrees[0])
            point_cloud.rotation_euler[1] = radians(rotation_angles_degrees[1])
            point_cloud.rotation_euler[2] = radians(rotation_angles_degrees[2])

        centroid = GeometryCollection.compute_centroid_coord(points)

        # create template vertex (this one will be copied in order to safe time)
        template_vertex = PointCloudTool.create_vertex(point_cloud, scale_factor, vertex_type)

        # each channel of a pseudo colors is in range [0 .. 1]
        template_material = PointCloudTool.make_material(name='color', diffuse_pseudo_color=np.array([0, 0, 0]))

        point_cloud_vertices = []
        for index, point in enumerate(points):

            current_vertex = template_vertex.copy()

            if recenter_point_cloud_around_centroid:
                # we resenter the object to the woorld coordinate frame
                current_vertex.location = point.coord - centroid
            else:
                current_vertex.location = point.coord

            # also duplicate mesh
            current_vertex.data = current_vertex.data.copy()

            current_vertex.data.materials.append(template_material.copy())

            # assign a pseudo color, range (0,1)
            pseudo_color = np.array(point.color) / 255.0
            current_vertex.data.materials[0].diffuse_color = pseudo_color

            if camera_name_for_billboarding:
                set_constraint_track_to(
                    current_vertex.name,
                    camera_name_for_billboarding,
                    update=False)

            point_cloud_vertices.append(current_vertex)

            if index % 100 == 0:
                logger.info(str(index))

        logger.info('point_cloud_vertices[0].location')
        logger.info(point_cloud_vertices[0].location)

        # link all objects
        for ob in point_cloud_vertices:
            bpy.context.scene.objects.link(ob)

        # delete the template vertex (make sure no other object is selected)
        bpy.ops.object.select_all(action='DESELECT')
        template_vertex.select = True
        bpy.ops.object.delete()

        # don't place this in either of the above loops!
        bpy.context.scene.update()

        logger.info('Add Point Cloud: Done')

    @staticmethod
    def add_point_cloud_using_particle_system(point_cloud_name,
                                              points,
                                              add_points_as_particle_system,
                                              mesh_type=VertexType.CUBE,
                                              point_extent=1.0,
                                              default_point_color=(255, 255, 255),
                                              overwrite_color=False):

        logger.info('add_point_cloud_using_particle_system: ...')

        name = point_cloud_name
        mesh = bpy.data.meshes.new(name)
        mesh.update()
        mesh.validate()

        point_world_coordinates = [tuple(point.coord) for point in points]

        mesh.from_pydata(point_world_coordinates, [], [])
        meshobj = add_obj(mesh, name)

        if add_points_as_particle_system:
            # logger.info("Representing Points in the Point Cloud with Meshes: True")
            # logger.info("Mesh Type: " + str(mesh_type))

            # The default size of elements added with
            #   primitive_cube_add, primitive_uv_sphere_add, etc. is (2,2,2)
            point_scale = point_extent * 0.5

            bpy.ops.object.select_all(action='DESELECT')
            if mesh_type == "PLANE":
                bpy.ops.mesh.primitive_plane_add(radius=point_scale)
            elif mesh_type == "CUBE":
                bpy.ops.mesh.primitive_cube_add(radius=point_scale)
            elif mesh_type == "SPHERE":
                bpy.ops.mesh.primitive_uv_sphere_add(size=point_scale)
            else:
                bpy.ops.mesh.primitive_uv_sphere_add(size=point_scale)
            viz_mesh = bpy.context.object

            if add_points_as_particle_system:

                material_name = "PointCloudMaterial"
                material = bpy.data.materials.new(name=material_name)
                material.diffuse_color = (
                default_point_color[0] / 255.0, default_point_color[1] / 255.0, default_point_color[2] / 255.0)
                viz_mesh.data.materials.append(material)

                # enable cycles, otherwise the material has no nodes
                bpy.context.scene.render.engine = 'CYCLES'
                material.use_nodes = True
                node_tree = material.node_tree
                # if 'Material Output' in node_tree.nodes:
                #     material_output_node = node_tree.nodes['Material Output']
                # else:
                material_output_node = node_tree.nodes.new('ShaderNodeOutputMaterial')
                if 'Diffuse BSDF' in node_tree.nodes:
                    diffuse_node = node_tree.nodes['Diffuse BSDF']
                else:
                    diffuse_node = node_tree.nodes.new("ShaderNodeBsdfDiffuse")
                node_tree.links.new(diffuse_node.outputs['BSDF'], material_output_node.inputs['Surface'])

                # if 'Image Texture' in node_tree.nodes:
                #     image_texture_node = node_tree.nodes['Image Texture']
                # else:
                image_texture_node = node_tree.nodes.new("ShaderNodeTexImage")
                node_tree.links.new(image_texture_node.outputs['Color'], diffuse_node.inputs['Color'])

                vis_image_height = 1

                # To view the texture we set the height of the texture to vis_image_height
                image = bpy.data.images.new('ParticleColor', len(point_world_coordinates), vis_image_height)

                # working on a copy of the pixels results in a MASSIVE performance speed
                local_pixels = list(image.pixels[:])

                num_points = len(points)

                for j in range(vis_image_height):
                    for point_index, point in enumerate(points):
                        column_offset = point_index * 4  # (R,G,B,A)
                        row_offset = j * 4 * num_points
                        if overwrite_color:
                            color = default_point_color
                        else:
                            color = point.color
                        # Order is R,G,B, opacity
                        local_pixels[row_offset + column_offset] = color[0] / 255.0
                        local_pixels[row_offset + column_offset + 1] = color[1] / 255.0
                        local_pixels[row_offset + column_offset + 2] = color[2] / 255.0
                        # opacity (0 = transparent, 1 = opaque)
                        # local_pixels[row_offset + column_offset + 3] = 1.0    # already set by default

                image.pixels = local_pixels[:]

                image_texture_node.image = image
                particle_info_node = node_tree.nodes.new('ShaderNodeParticleInfo')
                divide_node = node_tree.nodes.new('ShaderNodeMath')
                divide_node.operation = 'DIVIDE'
                node_tree.links.new(particle_info_node.outputs['Index'], divide_node.inputs[0])
                divide_node.inputs[1].default_value = num_points
                shader_node_combine = node_tree.nodes.new('ShaderNodeCombineXYZ')
                node_tree.links.new(divide_node.outputs['Value'], shader_node_combine.inputs['X'])
                node_tree.links.new(shader_node_combine.outputs['Vector'], image_texture_node.inputs['Vector'])

            if len(meshobj.particle_systems) == 0:
                meshobj.modifiers.new("particle sys", type='PARTICLE_SYSTEM')
                particle_sys = meshobj.particle_systems[0]
                settings = particle_sys.settings
                settings.type = 'HAIR'
                settings.use_advanced_hair = True
                settings.emit_from = 'VERT'
                settings.count = len(point_world_coordinates)
                # The final object extent is hair_length * obj.scale
                settings.hair_length = 100  # This must not be 0
                settings.use_emit_random = False
                settings.render_type = 'OBJECT'
                settings.dupli_object = viz_mesh

        else:
            logger.info("Representing Points in the Point Cloud with Meshes: False")

        logger.info('add_point_cloud_using_particle_system: Done')

        return meshobj