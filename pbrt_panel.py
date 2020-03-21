import bpy

class PBRT_Panel(bpy.types.Panel):
    bl_idname = "Test_PT_Panel"
    bl_label = "PBRT Loader"
    bl_category = "Ray Tracing Addon"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator('view3d.cursor_center', text="Load File")
