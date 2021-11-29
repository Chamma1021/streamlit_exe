# -*- mode: python ; coding: utf-8 -*-
import os
import sys
sys.setrecursionlimit(sys.getrecursionlimit() * 5000)

block_cipher = None
my_path = os.getcwd()

a = Analysis(['run_main.py'],
             pathex=[my_path],
             binaries=[],
             datas=[
                 (
                     "./venv/Lib/site-packages/altair/vegalite/v4/schema/vega-lite-schema.json",
                     "./altair/vegalite/v4/schema/"
                 ),
                 (
                     "./venv/Lib/site-packages/streamlit/static",
                     "./streamlit/static"
                 )
             ],
             hiddenimports=[
                'pandas',
                'openpyxl',
                'ezdxf',
                'ezdxf.recover',
                'ezdxf.addons.drawing',
                'ezdxf.addons.drawing.matplotlib',
                'ezdxf.addons.drawing.matplotlib.MatplotlibBackend',
                'ezdxf.addons.drawing.Frontend',
                'ezdxf.addons.drawing.RenderContext',
                'matplotlib.pyplot',
                'xlsxwriter',
                'io.BytesIO',
                'base64',
                'PIL',
                'numpy'
             ],
             hookspath=['./hooks'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='run_main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
