# -*- mode: python -*-

onefile = False


block_cipher = None

import pathlib
icons = [(os.path.join(base,file),base) for base,dirs,files in os.walk('icons') for file in files] + \
        [(str(f), '.') for f in pathlib.Path('.').glob('*.png')]

import platform
libmp3splt_binaries = {
    'Linux': [
        ('/usr/lib/libmp3splt.so', '.'),
        ('/usr/lib/libmp3splt0/libsplt_flac.so.0', 'libmp3splt'),
        ('/usr/lib/libmp3splt0/libsplt_mp3.so.0', 'libmp3splt'),
        ('/usr/lib/libmp3splt0/libsplt_ogg.so.0', 'libmp3splt'),
    ],
    'Windows': [ # 32bit!
        ('libmp3splt-0.9.2-win32/libmp3splt.dll', ''),
        ('libmp3splt-0.9.2-win32/libsplt_flac-0.dll', 'libmp3splt'),
        ('libmp3splt-0.9.2-win32/libsplt_mp3-0.dll', 'libmp3splt'),
        ('libmp3splt-0.9.2-win32/libsplt_ogg-0.dll', 'libmp3splt'),
    ]
}
    
a = Analysis(['tandamaster.py'],
             pathex=['/home/saso/tango.org/tm'],
             binaries=libmp3splt_binaries[platform.system()],
             datas=icons + [
                 ('initial_config/config.py', 'initial_config'),
                 ('initial_config/playtree.xml', 'initial_config'),
                 ('initial_config/ui.xml', 'initial_config'),
             ] +
             ( [('windows-dist/tandamaster.bat', ''),
                ('windows-dist/gi.pth', ''),
             ] if platform.system() == 'Windows' else [] )
             ,
             hiddenimports=[
                 'six','packaging', 'packaging.version', 'packaging.specifiers', 'packaging.requirements',
                 'mp3splt_h',
             ],
             hookspath=[],
             runtime_hooks=['copyconfig.py'] if onefile else [],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

#a.pure.remove( ('config', '/home/saso/tango.org/tm/config.py', 'PYMODULE') )



pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

if onefile:
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              name='tandamaster',
              debug=False,
              strip=False,
              upx=True,
              console=True )
else:    
    exe = EXE(pyz,
              a.scripts,
              # [('v',None,'OPTION')],  # debug info
              exclude_binaries=True,
              name='tandamaster',
              debug=False,
              strip=False,
              upx=True,
              console=True )
    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   name='tandamaster')
