# -*- mode: python -*-

onefile = False


block_cipher = None

import pathlib
icons = [(os.path.join(base,file),base) for base,dirs,files in os.walk('icons') for file in files] + \
        [(str(f), '.') for f in pathlib.Path('.').glob('*.png')]

import platform
binaries = {
    'Linux': [
        # libmp3splt
        ('/usr/lib/libmp3splt.so', '.'),
        #('/usr/lib/libmp3splt0/libsplt_flac.so.0', 'libmp3splt'),
        #('/usr/lib/libmp3splt0/libsplt_mp3.so.0', 'libmp3splt'),
        #('/usr/lib/libmp3splt0/libsplt_ogg.so.0', 'libmp3splt'),
        ('/usr/lib/libmp3splt0/libsplt_flac.so.0', ''),
        ('/usr/lib/libmp3splt0/libsplt_mp3.so.0', ''),
        ('/usr/lib/libmp3splt0/libsplt_ogg.so.0', ''),
    ],
    'Windows': [
        # libmp3splt: only 32bit!
        ('C:/Program Files/mp3splt/libmp3splt.dll', ''), # copy libmp3splt-0.dll to this file
        ('C:/Program Files/mp3splt/libmp3splt-0.dll', ''),
        #('C:/Program Files/mp3splt/libsplt_flac-0.dll', 'libmp3splt'),
        #('C:/Program Files/mp3splt/libsplt_mp3-0.dll', 'libmp3splt'),
        #('C:/Program Files/mp3splt/libsplt_ogg-0.dll', 'libmp3splt'),
        ('C:/Program Files/mp3splt/libsplt_flac-0.dll', ''),
        ('C:/Program Files/mp3splt/libsplt_mp3-0.dll', ''),
        ('C:/Program Files/mp3splt/libsplt_ogg-0.dll', ''),
        # other
        ('C:/Program Files/mp3splt/iconv.dll', ''),
        ('C:/Program Files/mp3splt/libFLAC.dll', ''),
        ('C:/Program Files/mp3splt/libid3tag.dll', ''),
        ('C:/Program Files/mp3splt/libintl-8.dll', ''),
        ('C:/Program Files/mp3splt/libltdl-7.dll', ''),
        ('C:/Program Files/mp3splt/libmad-0.dll', ''),
        ('C:/Program Files/mp3splt/libogg-0.dll', ''),
        ('C:/Program Files/mp3splt/libvorbis-0.dll', ''),
        ('C:/Program Files/mp3splt/libvorbisenc-2.dll', ''),
        ('C:/Program Files/mp3splt/libvorbisfile-3.dll', ''),
        ('C:/Program Files/mp3splt/pcre3.dll', ''),
        ('C:/Program Files/mp3splt/zlib1.dll', ''),
    ]
}

import unidecode
unidecode_modules = [t[1] for t in pkgutil.iter_modules(unidecode.__path__) if t[1].startswith('x')]

a = Analysis(['tandamaster.py'],
             pathex=['/home/saso/tango.org/tm'],
             binaries=binaries[platform.system()],
             datas=icons + [
                 ('initial_config/config.py', 'initial_config'),
                 ('initial_config/playtree.xml', 'initial_config'),
                 ('initial_config/ui.xml', 'initial_config'),
             ] +
             ( [('tandamaster.bat', ''),
                ('gi.pth', ''),
             ] if platform.system() == 'Windows' else [] )
             ,
             hiddenimports=[
                 'six','packaging', 'packaging.version', 'packaging.specifiers', 'packaging.requirements',
                 'mp3splt_h',
             ] + unidecode_modules,
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
