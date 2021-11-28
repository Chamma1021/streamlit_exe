import streamlit as st
import sys
import ezdxf
import tempfile
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image
import base64
from io import BytesIO
from ezdxf import recover
from ezdxf.addons.drawing import matplotlib
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing import Frontend, RenderContext
import pandas as pd

if __name__ == '__main__':
    st.header("Hello world")

    st.title('Counter Example')
    count = 0
    st.write(ezdxf.__version__)
    increment = st.button('Increment')
    if increment:
        count += 1

    st.write('Count = ', count)

    spectra = st.file_uploader("upload file", type={"csv", "txt"})
    if spectra is not None:
        spectra_df = pd.read_csv(spectra)
        st.write(spectra_df)
