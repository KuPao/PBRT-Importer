import bpy
from bpy.app.handlers import persistent
import mathutils
from math import pi

class PBRT_Importer(bpy.types.Operator):
    bl_idname = "view3d.cursor_center"
    bl_label = "Simple operator"
    bl_description = "Center 3d cursor"

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    mat_count = 0

    def execute(self, context):

        # Select objects by type
        for o in bpy.context.scene.objects:
            if o.type != 'CAMERA':
                o.select_set(True)
            else:
                o.select_set(False)

        # Call the operator only once
        bpy.ops.object.delete()

        camera = context.scene.camera
        
        print(self.filepath)
        last = 0
        for c in range(len(self.filepath)):
            if self.filepath[c] == '\\':
                last = c
        current = self.filepath[:last] + '\\'

        fp = open(self.filepath, "r")
        line = fp.readline()

        pos = mathutils.Vector((0,0,0))
        rot = mathutils.Vector((0,0,0))
        scl = mathutils.Vector((0,0,0))
        diff= mathutils.Vector((0,0,0,1))
        spec= mathutils.Vector((0,0,0))
        color_map = None
        bump_map = None
        get_pos = False
        get_mat = False
        is_mirror = False
        is_texture = False
        
        while line:
            if "xresolution" in line:
                line=line.replace('[', '')
                line=line.replace(']', '')
                strlist = line.split()
                for idx, s in enumerate(strlist):
                    if "xresolution" in s:
                        context.scene.render.resolution_x = float(strlist[idx+1])

            if "yresolution" in line:
                line=line.replace('[', '')
                line=line.replace(']', '')
                strlist = line.split()
                for idx, s in enumerate(strlist):
                    if "yresolution" in s:
                        context.scene.render.resolution_y = float(strlist[idx+1])

            if "fov" in line:
                line=line.replace('[', '')
                line=line.replace(']', '')
                strlist = line.split()
                for idx, s in enumerate(strlist):
                    if "fov" in s:
                        bpy.data.cameras[camera.name].angle = float(strlist[idx+1])*pi/180


            if "LookAt" in line:
                strlist = line.split()
                pos.x = float(strlist[1])
                pos.y = float(strlist[3])
                pos.z = float(strlist[2])
                foc = mathutils.Vector((float(strlist[4]), float(strlist[6]), float(strlist[5])))
                direction = foc - pos
                rot_quat = direction.to_track_quat('-Z', 'Y')
                #rot_quat = rot_quat.to_matrix().to_4x4()
                #rollMatrix = mathutils.Matrix.Rotation(0, 4, 'Z')
                #camera.matrix_world = rot_quat @ rollMatrix
                camera.rotation_euler = rot_quat.to_euler()
                camera.location = pos

            if "Translate" in line:
                strlist = line.split()
                pos.x = float(strlist[1])
                pos.y = float(strlist[3])
                pos.z = float(strlist[2])
                get_pos = True

            if "Rotate" in line and get_pos:
                strlist = line.split()
                rot.x = float(strlist[2])
                rot.y = float(strlist[4])
                rot.z = float(strlist[3])
                rot = pi * float(strlist[1]) / 180 * rot

            if "Scale" in line and get_pos:
                strlist = line.split()
                scl.x = float(strlist[1])
                scl.y = float(strlist[3])
                scl.z = float(strlist[2])

            if "Material" in line:
                line=line.replace('[', '')
                line=line.replace(']', '')
                line=line.replace('\"', '')
                line=line.replace('/', '\\')
                strlist = line.split()
                get_mat = True
                for idx, s in enumerate(strlist):
                    print(s)
                    if "Kd" in s:
                        diff.x = float(strlist[idx+1])
                        diff.y = float(strlist[idx+2])
                        diff.z = float(strlist[idx+3])
                    if "Ks" in s:
                        spec.x = float(strlist[idx+1])
                        spec.y = float(strlist[idx+2])
                        spec.z = float(strlist[idx+3])
                    if "mirror" in s:
                        is_mirror = True
                    if "map" in s and "color" in strlist[idx-1]:
                        color_map = current+strlist[idx+1]
                        is_texture = True
                    if "map" in s and "bump" in strlist[idx-1]:
                        bump_map = current+strlist[idx+1]
                        is_texture = True


            if "LightSource" in line:
                line=line.replace('[', '')
                line=line.replace(']', '')
                color = mathutils.Vector((1,1,1))
                energy = 0
                strlist = line.split()
                for idx, s in enumerate(strlist):
                    if "point" in s and "from" in strlist[idx+1]:
                        pos.x = float(strlist[idx+2])
                        pos.y = float(strlist[idx+4])
                        pos.z = float(strlist[idx+3])
                    if "color" in s and "L" in strlist[idx+1]:
                        color.x = float(strlist[idx+2])
                        color.y = float(strlist[idx+3])
                        color.z = float(strlist[idx+4])
                        energy = max(color.x, color.y, color.z)
                        color = color / energy
                if "area" in line:
                    bpy.ops.object.light_add(type='AREA', location=pos)
                    light = context.object.data
                    light.energy=energy*9
                    light.color=color
                    for idx, s in enumerate(strlist):
                        if "width" in s:
                            light.shape = 'RECTANGLE'
                            light.size = float(strlist[idx+1])
                        if "height" in s:
                            light.shape = 'RECTANGLE'
                            light.size_y=0.1

                elif "point" in line:
                    bpy.ops.object.light_add(type='POINT', location=pos)
                    light = context.object.data
                    light.energy=energy*9
                    light.color=color

            if "sphere" in line and get_pos:
                line=line.replace('[', '')
                line=line.replace(']', '')
                strlist = line.split()
                r = float(strlist[4])
                bpy.ops.mesh.primitive_uv_sphere_add(radius=r,location=pos,rotation=rot)
                obj = context.object

                if get_mat:
                    mat = bpy.data.materials.new('Material' + str(self.mat_count))
                    self.mat_count = self.mat_count + 1
                    if not is_mirror and not is_texture:
                        mat.diffuse_color = diff
                        mat.specular_color = spec
                    elif is_mirror:
                        mat.metallic = 1.0
                        mat.roughness = 0.0
                        mat.use_nodes = True
                        bsdf = mat.node_tree.nodes["Principled BSDF"]
                        bsdf.inputs['Metallic'].default_value = 1.0
                        bsdf.inputs['Roughness'].default_value = 0.0
                    elif is_texture:
                        mat.use_nodes = True
                        bsdf = mat.node_tree.nodes["Principled BSDF"]
                        if color_map != None:
                            texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
                            texImage.image = bpy.data.images.load(color_map)
                            mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
                    obj.data.materials.append(mat)

                get_pos = False
                get_mat = False
                is_mirror = False
                is_texture = False
                pos = mathutils.Vector((0,0,0))
                rot = mathutils.Vector((0,0,0))
                scl = mathutils.Vector((0,0,0))
                diff= mathutils.Vector((0,0,0,1))
                spec= mathutils.Vector((0,0,0))

            if "cylinder" in line and get_pos:
                line=line.replace('[', '')
                line=line.replace(']', '')
                strlist = line.split()
                r = float(strlist[4])
                h = float(strlist[10]) - float(strlist[7])
                bpy.ops.mesh.primitive_cylinder_add(radius=r,depth=h,location=pos,rotation=rot)
                obj = context.object

                if get_mat:
                    mat = bpy.data.materials.new('Material' + str(self.mat_count))
                    self.mat_count = self.mat_count + 1
                    if not is_mirror and not is_texture:
                        mat.diffuse_color = diff
                        mat.specular_color = spec
                    elif is_mirror:
                        mat.metallic = 1.0
                        mat.roughness = 0.0
                    obj.data.materials.append(mat)

                get_pos = False
                get_mat = False
                is_mirror = False
                is_texture = False
                pos = mathutils.Vector((0,0,0))
                rot = mathutils.Vector((0,0,0))
                scl = mathutils.Vector((0,0,0))
                diff= mathutils.Vector((0,0,0,1))
                spec= mathutils.Vector((0,0,0))

            if "cone" in line and get_pos:
                line=line.replace('[', '')
                line=line.replace(']', '')
                strlist = line.split()
                r = float(strlist[4])
                h = float(strlist[7])
                bpy.ops.mesh.primitive_cone_add(radius1=r,depth=h,location=pos,rotation=rot)
                obj = context.object

                if get_mat:
                    mat = bpy.data.materials.new('Material' + str(self.mat_count))
                    self.mat_count = self.mat_count + 1
                    if not is_mirror and not is_texture:
                        mat.diffuse_color = diff
                        mat.specular_color = spec
                    elif is_mirror:
                        mat.metallic = 1.0
                        mat.roughness = 0.0
                    obj.data.materials.append(mat)
                    
                get_pos = False
                get_mat = False
                is_mirror = False
                is_texture = False
                pos = mathutils.Vector((0,0,0))
                rot = mathutils.Vector((0,0,0))
                scl = mathutils.Vector((0,0,0))
                diff= mathutils.Vector((0,0,0,1))
                spec= mathutils.Vector((0,0,0))

            if "plane" in line and get_pos:
                line=line.replace('[', '')
                line=line.replace(']', '')
                strlist = line.split()
                w = float(strlist[4])
                h = float(strlist[7])
                scl = mathutils.Vector((w,h,1))
                if pos.z - 0.6 < 0.0001:
                    pos.x = 3.5
                bpy.ops.mesh.primitive_plane_add(size=1,location=pos,rotation=rot)
                bpy.ops.transform.rotate(value=-0.5*pi,orient_axis='Y')
                bpy.ops.transform.rotate(value=pi,orient_axis='X')
                bpy.ops.transform.resize(value=scl)

                obj = context.object

                if get_mat:
                    mat = bpy.data.materials.new('Material' + str(self.mat_count))
                    self.mat_count = self.mat_count + 1
                    if not is_mirror and not is_texture:
                        mat.diffuse_color = diff
                        mat.specular_color = spec
                    elif is_mirror:
                        mat.metallic = 1.0
                        mat.roughness = 0.0
                        mat.use_nodes = True
                        bsdf = mat.node_tree.nodes["Principled BSDF"]
                        bsdf.inputs['Metallic'].default_value = 1.0
                        bsdf.inputs['Roughness'].default_value = 0.0
                    elif is_texture:
                        mat.use_nodes = True
                        bsdf = mat.node_tree.nodes["Principled BSDF"]
                        if color_map != None:
                            texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
                            texImage.image = bpy.data.images.load(color_map)
                            mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
                        if bump_map != None:
                            bump = mat.node_tree.nodes.new('ShaderNodeBump')
                            bumpImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
                            bumpImage.image = bpy.data.images.load(bump_map)
                            mat.node_tree.links.new(bump.inputs['Height'], bumpImage.outputs['Color'])
                            mat.node_tree.links.new(bsdf.inputs['Normal'], bump.outputs['Normal'])
                    obj.data.materials.append(mat)

                get_pos = False
                get_mat = False
                is_mirror = False
                is_texture = False
                pos = mathutils.Vector((0,0,0))
                rot = mathutils.Vector((0,0,0))
                scl = mathutils.Vector((0,0,0))
                diff= mathutils.Vector((0,0,0,1))
                spec= mathutils.Vector((0,0,0))

            if "Include" in line and get_pos:
                line=line.replace('\"', '')
                line=line.replace('/', '\\')
                strlist = line.split()
                bpy.ops.import_scene.obj(filepath=current+strlist[1])
                bpy.ops.transform.translate(value=pos)
                bpy.ops.transform.resize(value=scl)
                get_pos = False
                get_mat = False
                is_mirror = False
                is_texture = False
                pos = mathutils.Vector((0,0,0))
                rot = mathutils.Vector((0,0,0))
                scl = mathutils.Vector((0,0,0))
                diff= mathutils.Vector((0,0,0,1))
                spec= mathutils.Vector((0,0,0))
                
            print(line)
            line = fp.readline()

        fp.close()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}