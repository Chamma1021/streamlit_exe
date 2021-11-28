import os
import pandas as pd
import numpy as np
import streamlit as st

ZEN = "".join(chr(0xff01 + i) for i in range(94))
ZEN = ZEN.join("　")  # 空白追加
HAN = "".join(chr(0x21 + i) for i in range(94))
HAN = HAN.join(" ")  # 空白追加
ZEN2HAN = str.maketrans(ZEN, HAN)


#
# 表紙
def get_values_hyoshi(excel_file):
    sheet_name_1 = '表紙'
    df_hyoshi = pd.read_excel(excel_file, sheet_name=sheet_name_1, header=None)
    hyoshi_dict = {}
    hyoshi_dict['設備名'] = df_hyoshi.iat[1, 2]
    hyoshi_dict['ライン名'] = df_hyoshi.iat[2, 2]
    hyoshi_dict['使用機種'] = df_hyoshi.iat[4, 2]
    hyoshi_dict['作成'] = df_hyoshi.iat[3, 5]
    hyoshi_dict['照査'] = df_hyoshi.iat[3, 6]
    hyoshi_dict['設計'] = df_hyoshi.iat[3, 7]
    hyoshi_dict['検認'] = df_hyoshi.iat[3, 8]
    hyoshi_dict['摘要表No.'] = df_hyoshi.iat[3, 10]
    hyoshi_dict['製作番号'] = df_hyoshi.iat[3, 11]
    df_hyoshi = pd.DataFrame(list(hyoshi_dict.items()), columns=["name-j", "item"])
    df_hyoshi['item'] = df_hyoshi['item'].astype(str).apply(
        lambda x: x.translate(ZEN2HAN)).str.replace(" ", "")
    df_hyoshi.reset_index(inplace=True, drop=True)
    df_hyoshi.index += 1
    df_hyoshi['target'] = ['表紙', 'その他', '表紙', '表紙', '表紙', '表紙', '表紙', 'その他', 'その他', ]
    df_hyoshi = df_hyoshi[['name-j', 'target', 'item']]
    return df_hyoshi


#
def get_values_tekiyosho(excel_file):
    # 摘要表
    skiprows = [0, 1, 2, 3, 4, 5]
    usecols = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    names = ['改定', '行番', '品名', '図面番号', '副番', '品番', '材料', '熱処理', '表面処理', '数/SET', '必要数', '所要数',
             '特記事項', '手配先']
    sheet_name_2 = ['摘要表 ', '摘要表']
    try:
        df_tekiyohyo = pd.read_excel(excel_file, sheet_name=sheet_name_2[0],
                                     header=None, skiprows=skiprows, usecols=usecols, names=names)
    except ValueError:
        df_tekiyohyo = pd.read_excel(excel_file, sheet_name=sheet_name_2[1],
                                     header=None, skiprows=skiprows, usecols=usecols, names=names)

    df_tekiyohyo.replace({'-': 0, '': np.nan, '<NA>': np.nan}, inplace=True)
    df_tekiyohyo.dropna(subset=['品名'], inplace=True)
    df_tekiyohyo['改定'].replace({np.nan: "-"}, inplace=True)
    df_tekiyohyo['図面番号'].replace({np.nan: "-"}, inplace=True)
    df_tekiyohyo['副番'].replace({np.nan: "-"}, inplace=True)
    df_tekiyohyo['熱処理'].replace({np.nan: "-"}, inplace=True)
    df_tekiyohyo['材料'].replace({np.nan: "-"}, inplace=True)
    df_tekiyohyo['表面処理'].replace({np.nan: "-"}, inplace=True)
    df_tekiyohyo['特記事項'].replace({np.nan: "-"}, inplace=True)
    df_tekiyohyo['手配先'].replace({np.nan: "-"}, inplace=True)
    df_tekiyohyo['品番'].replace({np.nan: 0}, inplace=True)
    df_tekiyohyo['数/SET'].replace({np.nan: 0}, inplace=True)
    df_tekiyohyo['必要数'].replace({np.nan: 0}, inplace=True)
    df_tekiyohyo['所要数'].replace({np.nan: 0}, inplace=True)
    df_tekiyohyo = df_tekiyohyo.astype({'品番': int, '数/SET': int, '必要数': int, '所要数': int})
    df_tekiyohyo.reset_index(inplace=True, drop=True)
    df_tekiyohyo.index += 1
    return df_tekiyohyo


if __name__ == '__main__':
    excel_file = 'data/excel/US52_A ピン圧入治具.xlsm'
    excel_name = os.path.splitext(os.path.basename(excel_file))[0]
    df_hyoshi = get_values_hyoshi(excel_file)
    df_tekiyohyo = get_values_tekiyosho(excel_file)
    # streamlit
    pdf_uploads = st.sidebar.file_uploader(label="図面PDFファイルアップロード", type='pdf',
                                           accept_multiple_files=True)
    excel_uploads = st.sidebar.file_uploader(label="摘要表EXCELファイルアップロード", type='xlsm')

    st.title(excel_name)
    st.write('## {}'.format("表紙"))
    st.table(df_hyoshi)
    st.write('## {}'.format("摘要表"))
    st.dataframe(df_tekiyohyo, width=2000, height=3000)
