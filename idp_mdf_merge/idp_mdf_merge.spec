# -*- mode: python -*-

block_cipher = None


a = Analysis(['idp_mdf_merge.py'],
             pathex=['C:\\Users\\geoffbp\\workspace\\idp_mdf_merge\\idp_mdf_merge'],
             binaries=[],
             datas=[('C:\\Python27\\tcl\\tcl8.5', 'tcl\\tcl8.5'), ('C:\\Python27\\tcl\\tk8.5', 'tk\\tk8.5')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='idp_mdf_merge',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
