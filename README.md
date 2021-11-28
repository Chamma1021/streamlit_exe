# streamlit_exe

environment

- python = 3.7.9
- streamlit = 0.61.0
- pyinstaller = 4.1

main.py
```
import streamlit as st

if __name__ == '__main__':
    st.header("Hello world")
```
run_main.py
```
import streamlit.cli

if __name__ == '__main__':
    streamlit.cli._main_run_clExplicit('main.py', 'streamlit run')
```
cli.py
```
def _main_run_clExplicit(file, command_line, args=[ ]):
    streamlit._is_running_with_streamlit = True
    bootstrap.run(file, command_line, args)
```
./hooks/hook-streamlit.py
```
from PyInstaller.utils.hooks import copy_metadata
datas = copy_metadata('streamlit')
```
./.streamlit/config.toml
```
[global]
developmentMode = false

[server]
port = 8501
```
[Terminal]
```
pyinstaller --onefile --additional-hooks-dir=./hooks run_main.py --clean
```
[run_main.spec]
```
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['run_main.py'],
             pathex=['.'],
             binaries=[],
             datas=[
                 (
                     "{$YOURPYTHONENV}/Lib/site-packages/altair/vegalite/v4/schema/vega-lite-schema.json",
                     "./altair/vegalite/v4/schema/"
                 ),
                 (
                     "${YOURPYTHONENV}/Lib/site-packages/streamlit/static",
                     "./streamlit/static"
                 )
            ],
            hiddenimports=['matplotlib'],
            ...,
            noarchive=False)
pyz = PYZ(...)
exe = EXE(...)
```
[terminal]
```
pyinstaller --onefile --additional-hooks-dir=./hooks run_main.spec --clean
```
copy .streamlit and main.py into dist direcoty
