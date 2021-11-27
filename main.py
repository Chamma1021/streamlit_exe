import streamlit as st
import pandas as pd

if __name__ == '__main__':
    st.header("Hello world")

    st.title('Counter Example')
    count = 0

    increment = st.button('Increment')
    if increment:
        count += 1

    st.write('Count = ', count)

    spectra = st.file_uploader("upload file", type={"csv", "txt"})
    if spectra is not None:
        spectra_df = pd.read_csv(spectra)
        st.write(spectra_df)
