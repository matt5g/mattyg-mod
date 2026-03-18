import py_compile
version = input('Version number: ') 
py_compile.compile('mattyg_mod.py', cfile=f"compiled/MattyGMod_v{version.replace('.','_')}.pyc")