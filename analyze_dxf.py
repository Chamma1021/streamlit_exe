import re
import pandas as pd


def get_entity_list(block_num, assemble):
    entity_list = []
    for j, dxf_entity in enumerate(assemble):
        entity_list.append(
            {'block_num': block_num,
             'entity_num': j + 1,
             'insert_num': 0,
             'insert_insert_num': 0,
             'layer': dxf_entity.dxf.layer,
             'type': dxf_entity.dxftype(),
             # 'element_dict': dxf_entity.dxf.all_existing_dxf_attribs().items(),
             'entity': dxf_entity,
             }
        )
        if dxf_entity.dxftype() == 'INSERT':
            for k, insert_entity in enumerate(dxf_entity.block().__iter__()):
                entity_list.append(
                    {'block_num': block_num,
                     'entity_num': j + 1,
                     'insert_num': k + 1,
                     'insert_insert_num': 0,
                     'layer': insert_entity.dxf.layer,
                     'type': insert_entity.dxftype(),
                     # 'element_dict': insert_entity.dxf.all_existing_dxf_attribs().items(),
                     'entity': insert_entity,
                     }
                )
                if insert_entity.dxftype() == 'INSERT':
                    for l, insert_insert_entity in enumerate(insert_entity.block().__iter__()):
                        entity_list.append(
                            {'block_num': block_num,
                             'entity_num': j + 1,
                             'insert_num': k + 1,
                             'insert_insert_num': l + 1,
                             'layer': insert_insert_entity.dxf.layer,
                             'type': insert_insert_entity.dxftype(),
                             # 'element_dict': insert_insert_entity.dxf.all_existing_dxf_attribs().items(),
                             'entity': insert_insert_entity,
                             }
                        )
    return entity_list


def count_fusen(x):
    if {'CIRCLE', 'MTEXT', } <= x.keys():
        return (x['CIRCLE'] == 1) & (x['MTEXT'] >= 2)
    else:
        return False


def count_frame(x):
    if {'LINE', 'MTEXT', } <= x.keys():
        return (x['LINE'] >= 50) & (x['MTEXT'] >= 50)
    else:
        return False


def count_input_moji(x):
    if ('MTEXT' in x.keys()) & ('LINE' not in x.keys()) & ('INSERT' not in x.keys()):
        return x['MTEXT'] == 1
    else:
        return False


def count_a_line(x):
    if ('MTEXT' not in x.keys()) & ('LINE' in x.keys()) & ('INSERT' not in x.keys()):
        return x['LINE'] == 1
    else:
        return False


def trimmed_text_entity(text_entity):
    text = text_entity.plain_text()
    # trimmed_text = text[text.rfind(';') + 1:]
    trimmed_text = text.replace(" ", "").replace("\\", "").replace("\u3000", "").replace("\n", "")
    return trimmed_text


def get_diagram_data(text):
    # UT4S525-1A
    m = re.match(r'(\w)T(\d)([^-]+)-(\d)(\w)', text)
    if m is None:
        kigo = ""
        paper_size = "0"
        fukuban = "-"
        hinban = "0"
        diagram_name = text
    else:
        kigo = m.group(1)
        paper_size = m.group(2)
        diagram_name = 'UT' + m.group(2) + m.group(3)
        fukuban = m.group(5)
        hinban = m.group(4)
    return [paper_size, fukuban, hinban, diagram_name]


def get_df_mtext(text_entity):
    text = trimmed_text_entity(text_entity)
    if text:
        return {
            'text': text,
            'text_size': text_entity.dxf.char_height,
            'text_width': text_entity.dxf.width,
            'text_font': text_entity.dxf.style,
            'text_attachment': text_entity.dxf.attachment_point,
            'text_position_x': text_entity.dxf.insert.x,
            'text_position_y': text_entity.dxf.insert.y,
        }
    else:
        return {}


def get_df_circle(circle_entity):
    radius = circle_entity.dxf.radius
    # print(radius)
    if (radius == 10.0) or (radius == 20.0) or (radius == 50.0):
        return {
            'circle_center_x': circle_entity.dxf.center.x,
            'circle_center_y': circle_entity.dxf.center.y,
            'circle_radius': circle_entity.dxf.radius,
        }
    else:
        return {}


def get_df_line(line_entity):
    return {
        'line_start_x': line_entity.dxf.start.x,
        'line_start_y': line_entity.dxf.start.y,
        'line_end_x': line_entity.dxf.end.x,
        'line_end_y': line_entity.dxf.end.y,
    }


def get_df_insert(insert_entity):
    return {
        'insert_place': insert_entity.dxf.insert,
        'insert_xscale': insert_entity.dxf.xscale,
        'insert_yscale': insert_entity.dxf.yscale,
        'insert_zscale': insert_entity.dxf.zscale,
    }


def get_df_fusen(df):
    # CIRCLE,MTEXTのみ取得する
    df_type = df[df['type'].isin(['CIRCLE', 'MTEXT', 'INSERT'])]
    # entity_num毎にtypeをカウントする
    sr_type_count = df_type.groupby(['entity_num', 'type']).size()
    # typeをindexからcolumnに変更する
    df_count = sr_type_count.reset_index(level='type', name='val')
    # print(df_count)
    # columnをdict化する
    s_new = df_count.groupby('entity_num').apply(lambda x: dict(zip(x['type'], x['val'])))
    # dataframeに変更する
    df_new = pd.DataFrame(s_new, columns={'count_per_type'})
    # FUSENかどうか
    df_new['is_fusen'] = df_new['count_per_type'].apply(count_fusen)
    # FUSENのentity_numのみ残す
    df_fusen = df_type[df_type['entity_num'].isin(df_new[df_new['is_fusen']].index)]
    # MTEXTのみ取得し、detailを作成する
    df_fusen_mtext = df_fusen[df_fusen['type'] == 'MTEXT']
    df_fusen_mtext['detail'] = df_fusen_mtext['entity'].apply(get_df_mtext)
    df_fusen_mtext = df_fusen_mtext[df_fusen_mtext['detail'] != {}]
    df_fusen_mtext['pos_y'] = df_fusen_mtext['detail'].apply(lambda x: x['text_position_y'])
    df_fusen_mtext['text'] = df_fusen_mtext['detail'].apply(lambda x: x['text'])
    # df_fusen_mtext.to_csv("a-fusen-text.csv", encoding='utf-8_sig')
    # CIRCLEのみ取得し、detailを作成する
    df_fusen_circle = df_fusen[df_fusen['type'] == 'CIRCLE']
    df_fusen_circle['detail'] = df_fusen_circle['entity'].apply(get_df_circle)
    df_fusen_circle = df_fusen_circle[df_fusen_circle['detail'] != {}]
    df_fusen_circle['pos_y'] = df_fusen_circle['detail'].apply(lambda x: x['circle_center_y'])
    # df_fusen_circle.to_csv("a-fusen-circle.csv", encoding='utf-8_sig')
    # df_fusenに戻す
    # df_fusen = pd.concat([df_fusen_mtext, df_fusen_circle]).sort_values('entity_num')
    df_fusen = df_fusen_mtext.sort_values('entity_num')
    # entity_num毎にpos_y順に並べる
    df_fusen = df_fusen.groupby('entity_num', as_index=False).apply(
        lambda x: x.sort_values(by='pos_y', ascending=False)).reset_index(drop=True)
    # df_fusen.to_csv("df_fusen.csv", encoding='utf-8_sig')
    s_fusen_data = df_fusen.groupby('entity_num').apply(lambda x: list(x['text']))
    df_fusen_data = pd.DataFrame(s_fusen_data, columns=['data'])
    # df_fusen_data.to_csv("df_fusen_data.csv", encoding='utf-8_sig')
    df_fusen_data['品名'] = df_fusen_data['data'].apply(lambda x: x[0])
    df_fusen_data['図面番号'] = df_fusen_data['data'].apply(lambda x: x[1])
    df_fusen_data = df_fusen_data[['品名', '図面番号']]
    print(df_fusen_data)
    df_fusen_data['DIAGRAM'] = df_fusen_data['図面番号'].apply(get_diagram_data)
    df_fusen_data['SIZE(A)'] = df_fusen_data['DIAGRAM'].apply(lambda x: x[0]).astype(int)
    df_fusen_data['副番'] = df_fusen_data['DIAGRAM'].apply(lambda x: x[1])
    df_fusen_data['品番'] = df_fusen_data['DIAGRAM'].apply(lambda x: x[2]).astype(int)
    df_fusen_data['図面番号'] = df_fusen_data['DIAGRAM'].apply(lambda x: x[3])
    df_fusen_data.sort_values(['副番', '図面番号'], ascending=[False, True], inplace=True)
    # df_fusen_data.to_csv('df_fusen_data.csv')
    df_fusen_data.drop('DIAGRAM', axis=1, inplace=True)
    df_fusen_data.reset_index(inplace=True)
    df_fusen_data.index += 1
    return df_fusen_data


def get_df_frame(df):
    # CIRCLE,MTEXTのみ取得する
    df_type = df[df['type'].isin(['MTEXT', 'LINE', 'INSERT'])]
    # entity_num毎にtypeをカウントする
    sr_type_count = df_type.groupby(['entity_num', 'type']).size()
    # typeをindexからcolumnに変更する
    df_count = sr_type_count.reset_index(level='type', name='val')
    # columnをdict化する
    s_count = df_count.groupby('entity_num').apply(lambda x: dict(zip(x['type'], x['val'])))
    # dataframeに変更する
    df_count = pd.DataFrame(s_count, columns={'count_per_type'})
    # FRAMEかどうか
    df_count['is_frame'] = df_count['count_per_type'].apply(count_frame)
    # 入力文字かどうか
    df_count['is_input'] = df_count['count_per_type'].apply(count_input_moji)
    # 1本線かどうか
    df_count['is_aline'] = df_count['count_per_type'].apply(count_a_line)
    # df_count.to_csv('df_count.csv')
    # frameのentity_numのみ残す
    df_frame = df_type[df_type['entity_num'].isin(df_count[df_count['is_frame']].index)]
    df_frame['frame_input'] = 'frame'
    df_input = df_type[df_type['entity_num'].isin(df_count[df_count['is_input']].index)]
    df_input['frame_input'] = 'input'
    df_aline = df_type[df_type['entity_num'].isin(df_count[df_count['is_aline']].index)]
    df_aline['frame_input'] = 'aline'
    df_frame = pd.concat([df_frame, df_input, df_aline]).sort_values(
        ['entity_num', 'insert_num', 'insert_insert_num'])
    # INSERTのみ取得し、detailを作成する
    df_frame_insert = df_frame[df_frame['type'] == 'INSERT']
    drop_index = df_frame.index[df_frame['type'] == 'INSERT']
    df_frame.drop(drop_index, inplace=True)
    df_frame_insert['detail'] = df_frame_insert['entity'].apply(get_df_insert)
    df_frame_insert = df_frame_insert[df_frame_insert['detail'] != {}]
    # INSERTのX座標を取得する
    df_frame_insert['pos_x'] = df_frame_insert.apply(
        lambda x: x['detail']['insert_place'][0] if x['insert_num'] == 0 else None, axis=1)
    df_frame_insert['pos_x'].fillna(method='ffill', inplace=True)
    df_frame_insert['pos_x'] = df_frame_insert.apply(
        lambda x: x['pos_x'] + x['detail']['insert_place'][0] if (x['insert_num'] > 0) & (
                x['insert_insert_num'] == 0) else x['pos_x'], axis=1)
    df_frame_insert['pos_x'] = df_frame_insert.apply(
        lambda x: x['pos_x'] + x['detail']['insert_place'][0] if (x['insert_num'] > 0) & (
                x['insert_insert_num'] > 0) else x['pos_x'], axis=1)
    # df_frame_insert.to_csv("df_frame_insert.csv", encoding='utf-8_sig')
    # INSERTのY座標を取得する
    df_frame_insert['pos_y'] = df_frame_insert.apply(
        lambda x: x['detail']['insert_place'][1] if x['insert_num'] == 0 else None, axis=1)
    df_frame_insert['pos_y'].fillna(method='ffill', inplace=True)
    df_frame_insert['pos_y'] = df_frame_insert.apply(
        lambda x: x['pos_y'] + x['detail']['insert_place'][1] if (x['insert_num'] > 0) & (
                x['insert_insert_num'] == 0) else x['pos_y'], axis=1)
    df_frame_insert['pos_y'] = df_frame_insert.apply(
        lambda x: x['pos_y'] + x['detail']['insert_place'][1] if (x['insert_num'] > 0) & (
                x['insert_insert_num'] > 0) else x['pos_y'], axis=1)
    # INSERTのscaleを取得する
    df_frame_insert['xscale'] = df_frame_insert['detail'].apply(lambda x: x['insert_xscale'])
    df_frame_insert['yscale'] = df_frame_insert['detail'].apply(lambda x: x['insert_yscale'])
    df_frame_insert['zscale'] = df_frame_insert['detail'].apply(lambda x: x['insert_zscale'])
    # df_frame_insert.to_csv("df_frame_insert.csv", encoding='utf-8_sig')
    # INSERTを結合する（INSERTのPOSITIONを返す）
    df_frame = pd.concat([df_frame_insert, df_frame]).sort_values(
        ['entity_num', 'insert_num', 'insert_insert_num'])
    # pos_x,pos_yの空白を上から順に埋める
    df_frame["pos_x"] = df_frame.groupby('entity_num')['pos_x'].transform(lambda x: x.ffill())
    df_frame["pos_x"].fillna(0, inplace=True)
    df_frame["pos_y"] = df_frame.groupby('entity_num')['pos_y'].transform(lambda x: x.ffill())
    df_frame["pos_y"].fillna(0, inplace=True)
    # xscale,yscale,zscaleの空白を上から順に埋める
    df_frame_zero = df_frame[df_frame['insert_insert_num'] == 0]
    drop_index = df_frame.index[df_frame['insert_insert_num'] == 0]
    df_frame.drop(drop_index, inplace=True)
    # df_frame.to_csv('df_frame_non_zero.csv', encoding='utf-8_sig')
    # 空白を埋める
    df_frame_zero["xscale"] = df_frame_zero.groupby('entity_num')['xscale'].transform(
        lambda x: x.ffill())
    df_frame_zero["yscale"] = df_frame_zero.groupby('entity_num')['yscale'].transform(
        lambda x: x.ffill())
    df_frame_zero["zscale"] = df_frame_zero.groupby('entity_num')['zscale'].transform(
        lambda x: x.ffill())
    df_frame_zero["xscale"].fillna(1, inplace=True)
    df_frame_zero["yscale"].fillna(1, inplace=True)
    df_frame_zero["zscale"].fillna(1, inplace=True)
    # INSERTを結合する（INSERTのSCALEを返す）
    df_frame = pd.concat([df_frame, df_frame_zero]).sort_values(
        ['entity_num', 'insert_num', 'insert_insert_num'])
    df_frame["xscale"].fillna(1, inplace=True)
    df_frame["yscale"].fillna(1, inplace=True)
    df_frame["zscale"].fillna(1, inplace=True)
    # df_frame.to_csv('df_frame.csv', encoding='utf-8_sig')
    # MTEXTのみ取得し、detailを作成する
    df_frame_mtext = df_frame[df_frame['type'] == 'MTEXT']
    df_frame_mtext['detail'] = df_frame_mtext['entity'].apply(get_df_mtext)
    df_frame_mtext = df_frame_mtext[df_frame_mtext['detail'] != {}]
    df_frame_mtext['text'] = df_frame_mtext['detail'].apply(lambda x: x['text'])
    # df_frame_mtext.to_csv("df_frame_mtext.csv", encoding='utf-8_sig')
    # textのpositionを取得する
    df_frame_mtext['pos_xt'] = df_frame_mtext['detail'].apply(lambda x: x['text_position_x'])
    df_frame_mtext['pos_xt'] = df_frame_mtext['pos_xt'] * df_frame_mtext['xscale'] + df_frame_mtext[
        'pos_x']
    df_frame_mtext['pos_yt'] = df_frame_mtext['detail'].apply(lambda x: x['text_position_y'])
    df_frame_mtext['pos_yt'] = df_frame_mtext['pos_yt'] * df_frame_mtext['yscale'] + df_frame_mtext[
        'pos_y']
    # LINEのみ取得し、detailを作成する
    df_frame_line = df_frame[df_frame['type'] == 'LINE']
    df_frame_line['detail'] = df_frame_line['entity'].apply(get_df_line)
    df_frame_line = df_frame_line[df_frame_line['detail'] != {}]
    # LINEのpositionを取得する
    df_frame_line['pos_xl0'] = df_frame_line['detail'].apply(lambda x: x['line_start_x'])
    df_frame_line['pos_xl0'] = df_frame_line['pos_xl0'] * df_frame_line['xscale'] + df_frame_line[
        'pos_x']
    df_frame_line['pos_yl0'] = df_frame_line['detail'].apply(lambda x: x['line_start_y'])
    df_frame_line['pos_yl0'] = df_frame_line['pos_yl0'] * df_frame_line['yscale'] + df_frame_line[
        'pos_y']
    df_frame_line['pos_xl1'] = df_frame_line['detail'].apply(lambda x: x['line_end_x'])
    df_frame_line['pos_xl1'] = df_frame_line['pos_xl1'] * df_frame_line['xscale'] + df_frame_line[
        'pos_x']
    df_frame_line['pos_yl1'] = df_frame_line['detail'].apply(lambda x: x['line_end_y'])
    df_frame_line['pos_yl1'] = df_frame_line['pos_yl1'] * df_frame_line['yscale'] + df_frame_line[
        'pos_y']
    df_frame_line['xlength'] = abs(df_frame_line['pos_xl1'] - df_frame_line['pos_xl0'])
    df_frame_line['ylength'] = abs(df_frame_line['pos_yl1'] - df_frame_line['pos_yl0'])
    df_frame_line.sort_values('pos_xl0', inplace=True)
    # df_frame_line.reset_index(inplace=True)
    df_a_line = df_frame_line[df_frame_line['frame_input'] == 'aline']
    df_frame_line = df_frame_line[df_frame_line['frame_input'] == 'frame']
    # df_frame_line.to_csv("df_frame_line.csv", encoding='utf-8_sig')
    # 結合
    df_frame = pd.concat([df_frame_insert, df_frame_mtext, df_frame_line]).sort_values(
        ['entity_num', 'insert_num', 'insert_insert_num', 'pos_xl0'])
    # df_frame.to_csv('df_frame.csv', encoding='utf-8_sig')
    # df_frame_insert.sort_values('pos', inplace=True)
    # df_frame_insert.to_csv("df_frame_insert.csv", encoding='utf-8_sig')
    df_all_text = df_frame[df_frame['type'] == 'MTEXT']
    df_all_text = df_all_text[['frame_input', 'type', 'text', 'pos_xt', 'pos_yt']]
    df_all_text.reset_index(inplace=True)
    df_all_text.index += 1
    df_frame_text = df_all_text[df_all_text['frame_input'] == 'frame']
    df_input_text = df_all_text[df_all_text['frame_input'] == 'input']
    # print(df_input_text)
    return df_a_line, df_frame_line, df_frame_text, df_input_text
