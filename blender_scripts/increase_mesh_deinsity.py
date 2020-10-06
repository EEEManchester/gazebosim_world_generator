import bpy
context = bpy.context

for ob in context.scene.objects:
     if ob.type == 'MESH':
         # get old one or add one
         m = ob.modifiers.get("My SubDiv") or ob.modifiers.new('My SubDiv', 'SUBSURF')
         
         m.levels = 1
         m.render_levels = 1
         m.quality = 1
         m.subdivision_type = 'SIMPLE'
         bpy.ops.object.modifier_apply(apply_as='DATA',modifier="My SubDiv")
