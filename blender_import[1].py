# LIVING FACADE AI — Blender import helper
# In Blender: Scripting > Open > this file > Run Script.
import bpy
from pathlib import Path

# Change this path to the downloaded OBJ file if needed.
obj_path = Path.home() / "Downloads" / "LIVING_FACADE_AI_model.obj"
if not obj_path.exists():
    raise FileNotFoundError(
        f"OBJ not found: {obj_path}\n"
        "Download LIVING_FACADE_AI_model.obj from the website and place it in Downloads."
    )

# Clear default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Import OBJ, supporting current and older Blender versions
try:
    bpy.ops.wm.obj_import(filepath=str(obj_path))
except Exception:
    bpy.ops.import_scene.obj(filepath=str(obj_path))

# Set origin/viewport and save native Blender project
for obj in bpy.context.selected_objects:
    if obj.type == 'MESH':
        obj.name = "LIVING_FACADE_AI_" + obj.name
        if obj.data:
            obj.data.name = obj.name + "_Mesh"

blend_path = obj_path.with_suffix(".blend")
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
print("LIVING FACADE AI model imported and saved:", blend_path)
