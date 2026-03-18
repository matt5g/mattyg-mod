import py_compile
import zipfile
import os
version = input('Version number: ') 
py_compile.compile('mattyg_mod.py', cfile=f"compiled/MattyGMod_v{version.replace('.','_')}.pyc")
with zipfile.ZipFile(f'compiled/MattyGMod_v{version.replace(".","_")}.zip', 'w') as zipf:
    zipf.write(f'compiled/MattyGMod_v{version.replace(".","_")}.pyc', os.path.basename(f'compiled/MattyGMod_v{version.replace(".","_")}.pyc'))
os.rename(f'compiled/MattyGMod_v{version.replace(".","_")}.zip', f'compiled/MattyGMod_v{version.replace(".","_")}.ts4script')
copyToMods = True # optionally copy the file to the mods folder
if copyToMods:
    import shutil
    mods_folder = os.path.expanduser('~\\Documents\\Electronic Arts\\The Sims 4\\Mods')
    shutil.copy(f'compiled/MattyGMod_v{version.replace(".","_")}.ts4script', mods_folder + f'\\mattygmod\\MattyGMod_v{version.replace(".","_")}.ts4script')
    for file in os.listdir(mods_folder + '\\mattygmod'):
        if file.startswith('MattyGMod_v') and file.endswith('.ts4script') and file != f'MattyGMod_v{version.replace(".","_")}.ts4script':
            os.remove(os.path.join(mods_folder + '\\mattygmod', file))
    