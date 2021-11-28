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
from analyze_dxf import get_df_fusen, get_df_frame, get_entity_list
from analyze_excel import *

ZEN = "".join(chr(0xff01 + i) for i in range(94))
# ZEN = ZEN.join("　")  # 空白追加
HAN = "".join(chr(0x21 + i) for i in range(94))
# HAN = HAN.join(" ")  # 空白追加
ZEN2HAN = str.maketrans(ZEN, HAN)


def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data


def convert_dxf_to_pdf(dxf, dxf_file_name):
    pdf_file_path = os.path.join('PDF', dxf_file_name + '.pdf')
    matplotlib.qsave(dxf.modelspace(), pdf_file_path)
    return pdf_file_path


def create_table_download_link(df, file_name):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    val = to_excel(df)
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{file_name}.xlsx">Download EXCEL</a>'  # decode b'abc' => abc


def create_download_link(val, filename):
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download PDF</a>'


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8_sig")
    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf">'
    st.markdown(pdf_display, unsafe_allow_html=True)


def show_png(file_path):
    image = Image.open(file_path)
    st.image(image, caption='サンプル', use_column_width=True)


def show_uploaded_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        fp = Path(tmp_file.name)
        fp.write_bytes(uploaded_file.getvalue())
        show_pdf(tmp_file.name)
        # imgs = convert_from_path(tmp_file.name)


def get_dxf_size(zu, df_frame_line, is_offset):
    # 用紙サイズ, 1/〇
    dxf_size = ['', 0]

    xlength = round(df_frame_line['xlength'].max(), 1)
    ylength = round(df_frame_line['ylength'].max(), 1)
    print(xlength, ylength)
    if xlength == 790 and ylength == 560:
        # 組図A3,1/2
        dxf_size = ['A3', 2]
    elif xlength == 790 / 2 and ylength == 560 / 2:
        # 組図A3,1/1
        dxf_size = ['A3', 1]
    elif xlength == 1160 and ylength == 810:
        # 組図A2,1/2
        dxf_size = ['A2', 2]
    elif xlength == 1160 / 2 and ylength == 810 / 2:
        # 組図A2,1/1
        dxf_size = ['A2', 1]
    elif xlength == 569 and ylength == 373:
        # 部品図A4,1/2
        dxf_size = ['A4', 2]
    elif xlength == 569 / 2 and ylength == 373 / 2:
        # 部品図A4,1/1
        dxf_size = ['A4', 1]
    elif xlength == 790 and ylength == 560:
        # 部品図A3,1/2
        dxf_size = ['A3', 2]
    elif xlength == 790 / 2 and ylength == 560 / 2:
        # 部品図A3,1/1
        dxf_size = ['A3', 1]
    print(dxf_size)

    if zu == 'kumizu':
        # 組図
        df_input_pos = pd.read_csv(f'data/frame/kumizu/{dxf_size[0]}.csv', header=0)
    else:
        # 部品図
        df_input_pos = pd.read_csv(f'data/frame/buhinzu/{dxf_size[0]}.csv', header=0)
    if is_offset:
        # Xは最小値は無視する
        xmin = df_frame_line['pos_xl0'].iloc[1]
        # Yは最小値
        ymin = df_frame_line['pos_yl0'].min()
        df_input_pos['x0'] = df_input_pos['x0'] * dxf_size[1] + xmin
        df_input_pos['x1'] = df_input_pos['x1'] * dxf_size[1] + xmin
        df_input_pos['y0'] = df_input_pos['y0'] * dxf_size[1] + ymin
        df_input_pos['y1'] = df_input_pos['y1'] * dxf_size[1] + ymin
    return df_input_pos


if __name__ == '__main__':
    # SIDE BAR
    st.sidebar.markdown(' # Select Apps')
    app = ['照合結果', '詳細データ']
    data = ['摘要表', '組図', '部品図']
    selected_app = st.sidebar.selectbox('表示', app)
    st.sidebar.markdown('***')
    selected_data = ""
    if selected_app == app[1]:
        st.sidebar.markdown(' ## Select Data')
        selected_data = st.sidebar.radio('詳細データを確認する', data)
        st.sidebar.markdown('***')
    st.sidebar.markdown(' ## File Upload')
    uploaded_excel = st.sidebar.file_uploader("摘要表（EXCEL）", type=['xlsx', 'xlsm'])
    uploaded_kumizu_dxf = st.sidebar.file_uploader("組図（DXF）", "dxf")
    uploaded_buhinzu_dxfs = st.sidebar.file_uploader("部品図（DXF）", "dxf", accept_multiple_files=True)
    #
    if uploaded_excel is not None:
        # 読み込み・摘要表
        # st.markdown('### **{}**'.format(uploaded_excel.name))
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            file_path = Path(tmp_file.name)
            file_path.write_bytes(uploaded_excel.getvalue())
            print(uploaded_excel.name)
        df_hyoshi = get_values_hyoshi(file_path)
        df_tekiyohyo = get_values_tekiyosho(file_path)
        df_tekiyohyo['品名'] = df_tekiyohyo['品名'].apply(lambda x: x.replace(' ', '').replace('　', ''))
        os.unlink(file_path)
    else:
        df_hyoshi = pd.DataFrame()
        df_tekiyohyo = pd.DataFrame()
    kumizu_list = []
    if uploaded_kumizu_dxf is not None:
        # 読み込み・組図
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            file_path = Path(tmp_file.name)
            file_path.write_bytes(uploaded_kumizu_dxf.getvalue())
        try:
            doc_kumizu, auditor = recover.readfile(file_path)
        except IOError:
            print(f'Not a DXF file or a generic I/O error.')
            sys.exit(1)
        except ezdxf.DXFStructureError:
            print(f'Invalid or corrupted DXF file.')
            sys.exit(2)
        # pdf_file_path = os.path.join('outputs', uploaded_dxf.name + '.pdf')
        # matplotlib.qsave(doc.modelspace(), pdf_file_path)
        # PDF作成に変更する #
        msp = doc_kumizu.modelspace()
        # block No.0（doc.entities） を分解する
        entity_list = get_entity_list(0, doc_kumizu.entities)
        if not entity_list:
            pass
        df = pd.DataFrame(entity_list)
        df_fusen_text = get_df_fusen(df)
        df_a_line, df_frame_line, df_frame_text, df_input_text = get_df_frame(df)
        # df_frame_line.to_csv("df_frame_line2.csv")
        df_assy = get_dxf_size('kumizu', df_frame_line, True)
        # df_assy.to_csv('df_assy.csv', encoding='utf-8_sig')
        # 入力文字の整理
        input_list = []
        for i, row in df_assy.iterrows():
            s_isinframe = (row['x0'] < df_input_text['pos_xt']) & (
                    df_input_text['pos_xt'] < row['x1']) & (
                                  row['y0'] < df_input_text['pos_yt']) & (
                                  df_input_text['pos_yt'] < row['y1'])
            input_list.append(df_input_text[s_isinframe]['text'].values)
        df_assy['input'] = pd.DataFrame(input_list)
        df_assy = df_assy[['name-j', 'name-e', 'target', 'input']]
        df_assy.index += 1
        kumizu_list = [doc_kumizu, auditor, df_fusen_text, df_frame_text, df_input_text, df_assy]
        df_assy["input"].fillna('-', inplace=True)
        os.unlink(file_path)
    else:
        df_assy = pd.DataFrame()
    buhinzu_lists = []
    if uploaded_buhinzu_dxfs is not None:
        # 読み込み・部品図
        for i, uploaded_buhinzu_dxf in enumerate(uploaded_buhinzu_dxfs):
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                file_path = Path(tmp_file.name)
                file_path.write_bytes(uploaded_buhinzu_dxf.getvalue())
            try:
                doc, auditor = recover.readfile(file_path)
            except IOError:
                print(f'Not a DXF file or a generic I/O error.')
                sys.exit(1)
            except ezdxf.DXFStructureError:
                print(f'Invalid or corrupted DXF file.')
                sys.exit(2)
            # pdf_file_path = os.path.join('outputs', uploaded_dxf.name + '.pdf')
            # matplotlib.qsave(doc.modelspace(), pdf_file_path)
            # PDF作成に変更する #
            msp = doc.modelspace()
            # block No.0（doc.entities） を分解する
            buhinzu_entity_list = get_entity_list(0, doc.entities)
            if not buhinzu_entity_list:
                pass
            df_buhinzu = pd.DataFrame(buhinzu_entity_list)
            df_buhinzu_a_line, df_buhinzu_frame_line, df_buhinzu_frame_text, df_buhinzu_input_text = get_df_frame(
                df_buhinzu)
            df_buhinzu_text_data = get_dxf_size('buhinzu', df_buhinzu_frame_line, True)
            df_buhinzu_line_data = get_dxf_size('buhinzu', df_buhinzu_frame_line, False)

            # 入力文字の整理
            input_list = []
            for i, row in df_buhinzu_text_data.iterrows():
                if row['type'] == 't':
                    s_isinframe = (row['x0'] < df_buhinzu_input_text['pos_xt']) & (
                            df_buhinzu_input_text['pos_xt'] < row['x1']) & (
                                          row['y0'] < df_buhinzu_input_text['pos_yt']) & (
                                          df_buhinzu_input_text['pos_yt'] < row['y1'])
                    input_list.append(df_buhinzu_input_text[s_isinframe]['text'].values)
            # LineはTextの後ろにかく
            for i, row in df_buhinzu_line_data.iterrows():
                if row['type'] == 'l':
                    s_isinframe = (round(row['x0'], 3) == round(df_buhinzu_a_line['pos_xl0'],
                                                                3)) & (
                                      (round(row['y1'], 3) == round(df_buhinzu_a_line['pos_yl1'],
                                                                    3)))
                    # input_list.append(df_buhinzu_a_line[s_isinframe])
                    # df_buhinzu_a_line.to_csv('df_buhinzu_a_line_s_isinframe.csv')
                    if len(df_buhinzu_a_line[s_isinframe]):
                        input_list.append(str(1))
                    else:
                        input_list.append(str(0))
            df_buhinzu_text_data['input'] = pd.DataFrame(input_list)
            df_buhinzu_text_data = df_buhinzu_text_data[['name-j', 'name-e', 'target', 'input']]
            df_buhinzu_text_data.index += 1
            df_buhinzu_text_data["input"].fillna('-', inplace=True)
            buhinzu_lists.append(
                [doc, auditor, df_buhinzu_frame_text, df_buhinzu_input_text, df_buhinzu_text_data])
            os.unlink(file_path)
        else:
            df_buhinzu_text_data = pd.DataFrame()
    ####################################################################################
    # APPs表示
    if selected_app == app[0]:
        # 照合結果
        st.markdown('## 照合結果')
        cover_columns = ['種類', '図種', '設備名', '使用機種', '作成', '照査', '設計', '検認', '作成日付', ]
        contents_columns = ['照合', '種類', '品名', '図面番号', '副番', '品番', '材料', '熱処理', '表面処理', '数/SET',
                            '必要数', ]
        df_cover = pd.DataFrame(columns=cover_columns)
        df_shogo_dxfs = pd.DataFrame(columns=contents_columns)
        df_shogo_fusen = pd.DataFrame(columns=contents_columns)
        df_shogo_tekiyohyo = pd.DataFrame(columns=contents_columns)
        # 表紙の適用表
        if len(df_hyoshi):
            st.write(df_hyoshi.iloc[1]['item'])
            # 適用表の表紙
            df_cover = df_cover.append({'種類': '摘要表',
                                        '図種': '-',
                                        '設備名': df_hyoshi.iloc[0]['item'],
                                        '使用機種': df_hyoshi.iloc[2]['item'],
                                        '作成': df_hyoshi.iloc[3]['item'],
                                        '照査': df_hyoshi.iloc[4]['item'],
                                        '設計': df_hyoshi.iloc[5]['item'],
                                        '検認': df_hyoshi.iloc[6]['item'],
                                        '作成日付': None
                                        }, ignore_index=True, )
        # 表紙の組図
        if len(df_assy):
            # 組図の文字列（df_assy）から摘要表と照合するところを取得し、半角にする
            assay_tekiyohyo_list = df_assy[df_assy['target'] == '摘要表']['input'].to_list()
            assay_hyoshi_list = df_assy[df_assy['target'] == '表紙']['input'].to_list()
            s_assay_tekiyohyo = pd.Series(assay_tekiyohyo_list)
            s_assay_hyoshi = pd.Series(assay_hyoshi_list)
            s_assay_tekiyohyo_han = s_assay_tekiyohyo.apply(lambda x: x.translate(ZEN2HAN))
            s_assay_hyoshi_han = s_assay_hyoshi.apply(lambda x: x.translate(ZEN2HAN))
            assay_tekiyohyo_han_list = s_assay_tekiyohyo_han.to_list()
            assay_hyoshi_han_list = s_assay_hyoshi_han.to_list()
            # 組図の表紙
            df_cover = df_cover.append({'種類': '組図',
                                        '図種': assay_tekiyohyo_han_list[0],
                                        '設備名': assay_hyoshi_han_list[0],
                                        '使用機種': assay_hyoshi_han_list[1],
                                        '作成': assay_hyoshi_han_list[2],
                                        '照査': assay_hyoshi_han_list[3],
                                        '設計': assay_hyoshi_han_list[4],
                                        '検認': assay_hyoshi_han_list[5],
                                        '作成日付': assay_hyoshi_han_list[6],
                                        }, ignore_index=True, )
            # 摘要表編
            # df_shogo_dxfs…摘要表の中身と照合する組図
            # 組図の半角にした文字列をまとめる
            kumizu_zumenbango = assay_tekiyohyo_han_list[
                1].lstrip("NA") if assay_tekiyohyo_han_list[1][:2] == "NA" else \
                assay_tekiyohyo_han_list[1]
            # 適用表内容と照合する組図の枠情報
            df_shogo_dxfs = df_shogo_dxfs.append({'種類': '組図',
                                                  '品名': assay_tekiyohyo_han_list[0],
                                                  '図面番号': kumizu_zumenbango,
                                                  '副番': '-',
                                                  '品番': int(assay_tekiyohyo_han_list[2]),
                                                  '材料': assay_tekiyohyo_han_list[3],
                                                  '熱処理': assay_tekiyohyo_han_list[4],
                                                  '表面処理': '-',
                                                  '数/SET': int(assay_tekiyohyo_han_list[5]),
                                                  '必要数': int(assay_tekiyohyo_han_list[6]),
                                                  }, ignore_index=True, )

        # 表示・部品図
        if len(uploaded_buhinzu_dxfs):
            for i, uploaded_buhinzu_dxf in enumerate(uploaded_buhinzu_dxfs):
                _, _, df_frame_text_buhinzu, df_input_text_buhinzu, df_buhinzu = buhinzu_lists[i]
                buhinzu_hyoshi_list = df_buhinzu[df_buhinzu['target'] == '表紙']['input'].to_list()
                s_buhinzu_hyoshi = pd.Series(buhinzu_hyoshi_list)
                s_buhinzu_hyoshi_han = s_buhinzu_hyoshi.apply(lambda x: x.translate(ZEN2HAN))
                buhinzu_hyoshi_han_list = s_buhinzu_hyoshi_han.to_list()
                # df_cover…摘要表の表紙を照合する組図・部品図
                # 適用表表紙と照合する部品図の枠情報
                df_cover = df_cover.append({'種類': '部品図',
                                            '図種': df_buhinzu[df_buhinzu['target'] == '摘要表'].iloc[0][
                                                'input'],
                                            '設備名': buhinzu_hyoshi_han_list[0],
                                            '使用機種': buhinzu_hyoshi_han_list[1],
                                            '作成': buhinzu_hyoshi_han_list[2],
                                            '照査': buhinzu_hyoshi_han_list[3],
                                            '設計': buhinzu_hyoshi_han_list[4],
                                            '検認': buhinzu_hyoshi_han_list[5],
                                            '作成日付': buhinzu_hyoshi_han_list[6],
                                            }, ignore_index=True, )
                # 摘要表編
                # 部品図の文字列（df_buhinzu）から摘要表と照合するところを取得し、半角にする
                buhinzu_tekiyohyo_list = df_buhinzu[df_buhinzu['target'] == '摘要表'][
                    'input'].to_list()
                s_buhinzu_tekiyohyo = pd.Series(buhinzu_tekiyohyo_list)
                s_buhinzu_tekiyohyo_han = s_buhinzu_tekiyohyo.apply(lambda x: x.translate(ZEN2HAN))
                assay_buhinzu_han_list = s_buhinzu_tekiyohyo_han.to_list()
                # df_shogo_dxfs…摘要表の中身と照合する組図・部品図
                buhinzu_hinmei = assay_buhinzu_han_list[0].replace(' ', '').replace('　', '')
                buhinzu_zumenbango = assay_buhinzu_han_list[
                    1].lstrip('NA') if assay_buhinzu_han_list[1][:2] == 'NA' else \
                    assay_buhinzu_han_list[1]
                buhinzu_fukuban = assay_buhinzu_han_list[7] if assay_buhinzu_han_list[
                                                                   7] != "" else "-"
                # 適用表内容と照合する部品図の枠情報
                df_shogo_dxfs = df_shogo_dxfs.append({'種類': '部品図',
                                                      '品名': buhinzu_hinmei,
                                                      '図面番号': buhinzu_zumenbango,
                                                      '副番': buhinzu_fukuban,
                                                      '品番': int(assay_buhinzu_han_list[2]),
                                                      '材料': assay_buhinzu_han_list[3],
                                                      '熱処理': assay_buhinzu_han_list[4],
                                                      '表面処理': '-',
                                                      '数/SET': int(assay_buhinzu_han_list[5]),
                                                      '必要数': int(assay_buhinzu_han_list[6]),
                                                      }, ignore_index=True, )
        if len(df_assy):
            # 適用表内容と照合する組図の風船情報
            df_fusen = kumizu_list[2]
            df_shogo_fusen['品名'] = df_fusen['品名'].apply(lambda x: x.replace(' ', ''))
            df_shogo_fusen['図面番号'] = df_fusen['図面番号']
            df_shogo_fusen['副番'] = df_fusen['副番']
            df_shogo_fusen['品番'] = df_fusen['品番']
            df_shogo_fusen['種類'] = df_shogo_fusen['種類'].map({np.nan: '組図風船'})
            df_shogo_dxfs = df_shogo_dxfs.append(df_shogo_fusen)
        # 表示・一致/不一致検証
        st.markdown('#### 表紙編')
        st.table(df_cover)
        st.markdown('#### 摘要表編')
        match_list = ['品名', '図面番号']
        selected_row = st.multiselect('照合する列を選択する', match_list, default=['品名', '図面番号'])
        st.markdown(f'摘要表と各図面において、__{selected_row}__が一致している行を取得します。')
        count_dict = {
            'ok': 0,
            'ng': 0,
            'nothing': 0,
        }
        for id, row in df_tekiyohyo.iterrows():
            shogo_ok = False
            # 摘要表１行ずつ
            df_shogo_tekiyohyo = df_shogo_tekiyohyo.append({'照合': '-',
                                                            '種類': '摘要表',
                                                            '品名': row['品名'],
                                                            '図面番号': row['図面番号'],
                                                            '副番': row['副番'],
                                                            '品番': row['品番'],
                                                            '材料': row['材料'],
                                                            '熱処理': row['熱処理'],
                                                            '表面処理': row['表面処理'],
                                                            '数/SET': row['数/SET'],
                                                            '必要数': row['必要数'],
                                                            }, ignore_index=True, )
            # df_shogo_dxfs「適用表内容と照合するデータ」の中から摘要表の品名と一致する行を検索する
            if selected_row == ['品名']:
                # 品名:一致 図面番号:不一致 行のみ取得する
                df_match_dxfs = df_shogo_dxfs[
                    (df_shogo_dxfs['品名'] == row['品名']) & (df_shogo_dxfs['図面番号'] != row['図面番号'])]
            elif selected_row == ['図面番号']:
                # 品名:不一致 図面番号:一致 行のみ取得する
                df_match_dxfs = df_shogo_dxfs[
                    (df_shogo_dxfs['品名'] != row['品名']) & (df_shogo_dxfs['図面番号'] == row['図面番号'])]
            else:
                # 品名:一致 図面番号:一致 行のみ取得する
                df_match_dxfs = df_shogo_dxfs[
                    (df_shogo_dxfs['品名'] == row['品名']) & (df_shogo_dxfs['図面番号'] == row['図面番号'])]
            if len(df_match_dxfs):
                # 一致する行があれば・・・
                for i, match_row in df_match_dxfs.iterrows():
                    # 一致行を1行ずつ確認する
                    zumenbango = match_row['図面番号'] == row['図面番号']
                    hinban = match_row['品番'] == row['品番']
                    fukuban = match_row['副番'] == row['副番']
                    zairyo = match_row['材料'] == row['材料']
                    netsushori = match_row['熱処理'] == row['熱処理']
                    hyomenshori = match_row['表面処理'] == row['表面処理']
                    kazuset = match_row['数/SET'] == row['数/SET']
                    hitsuyosu = match_row['必要数'] == row['必要数']
                    if match_row['種類'] == "組図":
                        # 適用表と組図の枠 => 「図面番号」と「品番」の照合一致
                        match_condition = zumenbango and hinban
                    elif match_row['種類'] == "部品図":
                        # 適用表と部品図の枠 => 「図面番号」と「品番」と「副番」と「材料」の照合一致
                        match_condition = zumenbango and hinban and fukuban and zairyo
                    else:
                        # 適用表と組図風船の枠 => 「図面番号」と「品番」と「副番」の照合一致
                        match_condition = zumenbango and hinban and fukuban
                    if match_condition:
                        # 照合結果 OK
                        shogo = '◎'
                        shogo_ok = True
                    elif not zumenbango:
                        # 図面番号 不一致
                        shogo = '×図面番号'
                    elif not fukuban:
                        # 副番 不一致
                        shogo = '×副番'
                    elif not hinban:
                        # 品番 不一致
                        shogo = '×品番'
                    else:
                        # その他
                        shogo = '×その他'
                    # 適用表の下の行に、照合一致の行を追加する
                    df_shogo_tekiyohyo = df_shogo_tekiyohyo.append({'照合': shogo,
                                                                    '種類': match_row['種類'],
                                                                    '品名': match_row['品名'],
                                                                    '図面番号': match_row['図面番号'],
                                                                    '副番': match_row['副番'],
                                                                    '品番': match_row['品番'],
                                                                    '材料': match_row['材料'],
                                                                    '熱処理': match_row['熱処理'],
                                                                    '表面処理': match_row['表面処理'],
                                                                    '数/SET': match_row['数/SET'],
                                                                    '必要数': match_row['必要数'],
                                                                    }, ignore_index=True, )
                if shogo_ok:
                    # OK数を+1する
                    count_dict['ok'] += 1
                else:
                    # NG数を+1する
                    count_dict['ng'] += 1
            else:
                # NOTHINGを+1する
                count_dict['nothing'] += 1
            # 空白行
            df_shogo_tekiyohyo = df_shogo_tekiyohyo.append({'照合': " ",
                                                            '種類': " ",
                                                            '品名': " ",
                                                            '図面番号': " ",
                                                            '副番': " ",
                                                            '品番': 0,
                                                            '材料': " ",
                                                            '熱処理': " ",
                                                            '表面処理': " ",
                                                            '数/SET': 0,
                                                            '必要数': 0,
                                                            }, ignore_index=True, )
        # 一致・不一致表示
        # st.markdown('#### 照合対象編')
        # st.dataframe(df_shogo_dxfs)
        shogo_list = ['ALL', '◎', '×図面番号', '×品番', '×副番', '×その他', 'Ｘ']
        selected_shogo = st.multiselect('表示する照合結果を選択する', shogo_list, default=['ALL'])
        if 'ALL' in selected_shogo:
            selected_shogo = shogo_list[1:]
        elif 'Ｘ' in selected_shogo:
            selected_shogo.extend(['×図面番号', '×品番', '×副番', '×その他'])
        selected_shogo.append('-')
        selected_shogo.append(' ')
        df_shogo_tekiyohyo_selected = df_shogo_tekiyohyo[
            (df_shogo_tekiyohyo['照合'].isin(selected_shogo))]
        st.write("摘要表と各図面の照合結果")
        # col1, col2, col3 = st.columns(3)
        # with col1:
        st.markdown("##### 照合一致数")
        st.markdown(f"# {count_dict['ok']}")
        # with col2:
        st.markdown("##### 照合不一致数")
        st.markdown(f"# {count_dict['ng']}")
        # with col3:
        st.markdown("##### 照合なし数")
        st.markdown(f"# {count_dict['nothing']}")
        # df_count = pd.DataFrame.from_dict(count_dict, orient='index')
        # st.table(df_count)
        st.table(df_shogo_tekiyohyo_selected)

    if selected_app == app[1]:
        # 詳細データ
        if selected_data == data[0]:
            # 摘要表
            if uploaded_excel is not None:
                st.markdown('### **{}**'.format(uploaded_excel.name))
                st.markdown('#### 表紙')
                st.table(df_hyoshi)
                st.markdown(create_table_download_link(df_hyoshi, '表紙'), unsafe_allow_html=True)
                st.markdown('#### 摘要表')
                st.dataframe(df_tekiyohyo)
                st.markdown(create_table_download_link(df_tekiyohyo, '摘要表'), unsafe_allow_html=True)
            else:
                st.markdown(' ### ** Please upload new Excel ! **')
        elif selected_data == data[1]:
            # 組図
            if uploaded_kumizu_dxf:
                pic_check = st.checkbox('図面表示', key=0)
                doc, auditor, df_fusen_text, df_frame_text, df_input_text, df_assy = kumizu_list
                # show PDF
                if pic_check:
                    pass
                    # fig = plt.figure()
                    # if not auditor.has_errors:
                    #     ax = fig.add_axes([0, 0, 1, 1])
                    #     ctx = RenderContext(doc)
                    #     out = MatplotlibBackend(ax)
                    #     Frontend(ctx, out).draw_layout(doc.modelspace(), finalize=True)
                    #     with st.expander('DXF 図面'):
                    #         st.pyplot(fig)
                    #     if st.button(label='PDF 作成', key=0):
                    #         pdf_path = Path(uploaded_kumizu_dxf.name).stem + ".pdf"
                    #         fig.savefig(pdf_path)
                st.markdown('### **{}**'.format(uploaded_kumizu_dxf.name))
                st.markdown('#### 風船文字')
                st.dataframe(df_fusen_text)
                st.markdown(create_table_download_link(df_fusen_text, '風船文字'),
                            unsafe_allow_html=True)
                st.markdown('***')
                st.markdown('#### 枠内入力文字')
                # st.dataframe(df_a3)
                st.table(df_assy)
                st.markdown(create_table_download_link(df_assy, '枠内入力文字'), unsafe_allow_html=True)
                st.markdown('***')
                st.markdown('#### 枠文字')
                st.dataframe(df_frame_text)
                st.markdown(create_table_download_link(df_frame_text, '枠文字'),
                            unsafe_allow_html=True)
                st.markdown('***')
                st.markdown('#### 全入力文字')
                st.dataframe(df_input_text)
                st.markdown(create_table_download_link(df_input_text, '他入力文字'),
                            unsafe_allow_html=True)
                st.markdown('***')
            else:
                st.markdown(' ### ** Please upload new Kumizu ! **')
        elif selected_data == data[2]:
            # 部品図
            if uploaded_buhinzu_dxfs:
                for i, uploaded_buhinzu_dxf in enumerate(uploaded_buhinzu_dxfs):
                    pic_check = st.checkbox('図面表示', key=i)
                    doc, auditor, df_frame_text, df_input_text, df_assy = buhinzu_lists[i]
                    # show PDF
                    if pic_check:
                        pass
                        # fig = plt.figure()
                        # if not auditor.has_errors:
                        #     ax = fig.add_axes([0, 0, 1, 1])
                        #     ctx = RenderContext(doc)
                        #     out = MatplotlibBackend(ax)
                        #     Frontend(ctx, out).draw_layout(doc.modelspace(), finalize=True)
                        #     with st.expander('DXF 図面'):
                        #         st.pyplot(fig)
                        #     if st.button(label='PDF 作成', key=i):
                        #         pdf_path = Path(uploaded_buhinzu_dxf.name).stem + ".pdf"
                        #         fig.savefig(pdf_path)
                    st.markdown('### **{}**'.format(uploaded_buhinzu_dxf.name))
                    st.markdown('***')
                    st.markdown('#### 枠内入力文字')
                    st.table(df_assy)
                    st.markdown(create_table_download_link(df_assy, '枠内入力文字'),
                                unsafe_allow_html=True)
                    st.markdown('***')
                    st.markdown('#### 枠文字')
                    st.dataframe(df_frame_text)
                    st.markdown(create_table_download_link(df_frame_text, '枠文字'),
                                unsafe_allow_html=True)
                    st.markdown('***')
                    st.markdown('#### 全入力文字')
                    st.dataframe(df_input_text)
                    st.markdown(create_table_download_link(df_input_text, '他入力文字'),
                                unsafe_allow_html=True)
                    st.markdown('***')
            else:
                st.markdown(' ### ** Please upload new Buhinzu ! **')
