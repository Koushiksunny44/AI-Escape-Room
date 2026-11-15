"""Run in Blender's Scripting workspace with archive_room_detailed.blend open.
Exports actual renders; restores scene settings and original objects afterwards.
No API keys, downloads, or new Blender save required.
"""
import bpy
from pathlib import Path
from mathutils import Vector


def run():
    scene = bpy.context.scene
    if not bpy.data.filepath:
        raise RuntimeError('Open and save archive_room_detailed.blend first.')
    source = Path(bpy.data.filepath).parent
    candidates = [p for root in (source, *list(source.parents)[:3]) for p in (root / 'AI_Escape_Room_V1', root)]
    project = next((p for p in candidates if (p/'app.py').is_file() and (p/'game_logic.py').is_file()), None)
    if project is None:
        raise RuntimeError('Cannot locate AI_Escape_Room_V1 next to your Blender project. Set project to your Python folder in this script.')
    assets = project/'assets'; assets.mkdir(exist_ok=True)
    required = ['FA_PlayerCamera','FA_JournalCover','FA5_DeskInspectCamera','FA_Painting','FA_PaintingEmblem']
    missing = [n for n in required if scene.objects.get(n) is None]
    if missing: raise RuntimeError('Open archive_room_detailed.blend. Missing: '+', '.join(missing))
    marks = sorted([o for o in scene.objects if o.name.startswith('FA5_BookMark') and o.type=='FONT'], key=lambda o:o.location.x)
    if len(marks)!=4: raise RuntimeError('Expected four marked books in detailed scene.')
    old_marks = [o.data.body for o in marks]
    emblem = scene.objects['FA_PaintingEmblem']; old_hidden = emblem.hide_render
    r=scene.render
    old=(scene.camera,r.engine,r.resolution_x,r.resolution_y,r.resolution_percentage,r.filepath,r.image_settings.file_format,r.image_settings.color_mode,r.use_file_extension)
    temp=[]; meshes=[]; materials=[]; cameras=[]; lights=[]
    def mat(name, color, metallic=0):
        m=bpy.data.materials.new(name); materials.append(m); m.diffuse_color=(*color,1); m.use_nodes=True
        bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Metallic'].default_value=metallic; bs.inputs['Roughness'].default_value=.55
        return m
    def polygon(name, points, y, material):
        mesh=bpy.data.meshes.new(name); meshes.append(mesh); mesh.from_pydata([(x,y,z) for x,z in points],[],[tuple(range(len(points)))]); mesh.update()
        o=bpy.data.objects.new(name,mesh); scene.collection.objects.link(o); temp.append(o); mesh.materials.append(material); return o
    def aim(obj, target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    def render(name, cam, loc=None, target=None, lens=45, fill=0):
        if loc is not None:
            cam.location=loc; aim(cam,target); cam.data.lens=lens
        scene.camera=cam
        lamp.hide_render=not bool(fill)
        if fill:
            lamp.location=cam.location; aim(lamp,target); lamp.data.energy=fill
        r.filepath=str(assets/name); bpy.ops.render.render(write_still=True); print('EXPORTED:',r.filepath)
    try:
        # Align the visual book clue with the existing LLM rules: 4,1,7,2.
        for o,digit in zip(marks,'4172'): o.data.body=digit
        # Replace the placeholder IV emblem in these exports with original raven artwork.
        emblem.hide_render=True
        dark=mat('Export Raven',(.022,.027,.033)); bronze=mat('Export Brass Eye',(.55,.30,.055),.65)
        feather=mat('Export Raven Feather',(.06,.075,.09))
        # X/Z silhouette on front of the painting, facing the player (-Y).
        polygon('Export Raven Silhouette',[(2.25,1.94),(2.39,2.25),(2.30,2.51),(2.43,2.72),(2.59,2.84),(2.79,2.82),(2.88,2.72),(3.05,2.66),(2.87,2.60),(2.77,2.48),(2.80,2.26),(2.68,2.09),(2.45,1.94)],4.699,dark)
        polygon('Export Raven Wing',[(2.43,2.53),(2.70,2.47),(2.69,2.28),(2.47,2.04),(2.39,2.29)],4.695,feather)
        import math
        polygon('Export Brass Eye',[(2.79+.036*math.cos(i*math.tau/24),2.73+.036*math.sin(i*math.tau/24)) for i in range(24)],4.69,bronze)
        c=bpy.data.cameras.new('Export Closeup Camera'); cameras.append(c); c.clip_start=.025
        cam=bpy.data.objects.new('Export Closeup Camera',c); scene.collection.objects.link(cam); temp.append(cam)
        ld=bpy.data.lights.new('Export Inspection Fill','AREA'); lights.append(ld); ld.shape='DISK'; ld.size=.65; ld.color=(1,.83,.65)
        lamp=bpy.data.objects.new('Export Inspection Fill',ld); scene.collection.objects.link(lamp); temp.append(lamp)
        r.engine='BLENDER_EEVEE'; r.resolution_x=1280; r.resolution_y=720; r.resolution_percentage=100; r.image_settings.file_format='PNG'; r.image_settings.color_mode='RGB'; r.use_file_extension=True
        # Keep original overview if export fails before completing the new one.
        render('room_preview.png',scene.objects['FA_PlayerCamera'])
        render('inspect_desk.png',cam,(-1.85,-2.2,1.85),(-2.25,.1,.85),40,45)
        # Top-down oblique view: text remains legible and the journal fills the frame.
        j=scene.objects['FA_JournalCover'].location
        render('inspect_journal.png',cam,(j.x,j.y-.22,j.z+.95),(j.x,j.y,j.z+.045),45,24)
        render('inspect_bookshelf.png',cam,(-2.58,1.4,1.7),(-2.58,4.3,1.48),33,50)
        center=sum((o.location for o in marks),Vector())/4
        render('inspect_books.png',cam,(center.x,center.y-1.02,center.z+.02),center,42,13)
        render('inspect_painting.png',cam,(2.6,2.32,2.42),(2.6,4.72,2.42),42,45)
        render('inspect_drawer.png',cam,(2.85,-1.35,1.45),(2.85,.4,.66),39,35)
        render('inspect_terminal.png',cam,(2.72,1.65,1.8),(2.72,2.85,1.48),42,22)
        render('inspect_door.png',cam,(0,1.05,1.75),(0,4.85,1.5),35,65)
    finally:
        for o,body in zip(marks,old_marks): o.data.body=body
        emblem.hide_render=old_hidden
        scene.camera,r.engine,r.resolution_x,r.resolution_y,r.resolution_percentage,r.filepath,r.image_settings.file_format,r.image_settings.color_mode,r.use_file_extension=old
        for o in temp: bpy.data.objects.remove(o,do_unlink=True)
        for blocks,collection in [(meshes,bpy.data.meshes),(materials,bpy.data.materials),(cameras,bpy.data.cameras),(lights,bpy.data.lights)]:
            for block in blocks: collection.remove(block)
    print('All nine images exported to:',assets)
    def draw(self,context):
        self.layout.label(text='Nine archive views exported. Refresh Streamlit.')
    bpy.context.window_manager.popup_menu(draw,title='Archive Visual Export Complete',icon='CHECKMARK')

run()
