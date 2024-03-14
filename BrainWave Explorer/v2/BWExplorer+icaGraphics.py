import PySimpleGUI as sg
import time
import os
import mne
from mne.preprocessing import ICA
import copy

from GUIgraphics import *
from Analyse import *
from parse import *

'''
BrainWave Explorer - программа, предназначенная для анализа данных
'''


if __name__ == '__main__':
    '''Запуск основной программы'''
    order_cola = ['cola',
                  'funky',
                  'd_cola',
                  'cola_zero',
                  'chernogolovka',
                  'd_zero']

    order_honey =['Dedushkin_uley',
                  'Bashkirsky',
                  'Medovoye_razdolie',
                  'Permskiye_pcholy',
                  'Permskaya_fabrika',
                  'Dalnevostochniy',
                  'Lubomedovo'
                  ] #пока не придумала общего решения, плодим сущности. Это порядок мёда в открытом тестировании

    sg.theme('LightBlue2')  # это раскраска темы
    RATE = 500 #частота считываний в 1 с
    volunteers_combo = sg.Combo([], font=('Arial Bold', 12), expand_x=True, enable_events=True,
                               readonly=True, key='-VOL-', disabled=True)
    exp_combo = sg.Combo(['закрытый', 'открытый'], font=('Arial Bold', 12), expand_x=True, enable_events=True,
                               readonly=True, key='-EXP-', disabled=True)
    electrode_combo = sg.Combo([], font=('Arial Bold', 12), expand_x=True, enable_events=True, readonly=True,
                                key='-ELEC-', disabled=True)
    timestamps_combo = sg.Combo([], font=('Arial Bold', 12), expand_x=True, enable_events=True, readonly=True,
                                key='-TIME-', disabled=True)
    fig_agg = None
    files = []
    t = []
    final_data = {} #словарь, со словарями в котором будут храниться результаты
    m = 0
    '''так как в PySimpleGUI нет функции проверки состояния объектов(WTF!!!),
    то я завожу отдельную переменную как флажок, чтобы проверять, были ли уже подкгружены временные метки или нет'''
    flag_timestamps = False

    '''отрисовка формы'''
    layout = [
        [sg.Text('Тип продукта'), sg.Radio('Cola', group_id="PRODUCT", key='P1', default=True),
         sg.Radio('Мёд', group_id="PRODUCT")],
        [sg.Text('Выберите папку, в которой содержатся данные с эксперимента'),
         sg.In(size=(25, 1), enable_events=True, key='-FOLDER-'), sg.FolderBrowse()],

        [sg.Text('Испытуемый'), volunteers_combo, sg.Text('Выберите тип эксперимента'), exp_combo],
        [sg.Text('Электрод'), electrode_combo],
        [sg.Text('Выберите временную метку'), timestamps_combo],
        [sg.Text('Начало временного отрезка'), sg.InputText(key='-START-', size=(10, 10), disabled=True),
         sg.Text('Продолжительность (сек)'), sg.InputText(key='-LEN-', disabled=True)],
        [sg.Submit('Построить график', key='-PLOT-', disabled=True)],
        [sg.Canvas(key='-CANVAS-')],

        [sg.Submit('Отчёт(закр, 5 сек в конце, закр)', key='-REPF-', disabled=True),
        sg.Submit('Отчёт (откр, 5 сек в конце)', key='-OPEN-', disabled=True),
        sg.Submit('Закр, 5ск, нефильтр', key='-NOFILTCLOSE-', disabled=True), sg.Submit('Откр, 5сек, нефильтр', key='-NOFILTOPEN-', disabled=True)]

    ]
    # sg.Submit('Отчёт (закр, 5 сек в начале)', key='-REPS-', disabled=True),
    # [sg.Button('Добавить отрезок', key='-SEG-', disabled=False),
    #      sg.Button('Сохранить данные по волонтёру', key='-ADD-', disabled=False),
    #      sg.Button('Выгрузить отчёт', key='-FFT-', disabled=False)],
    # sg.Button('Выгрузить таблицу', key='-FFT-', disabled=True),
    # sg.Button('Выгрузить WTP etc', key='-ETC-', disabled=True)

    window = sg.Window('FFT for EEG', layout, finalize=True, size=(815, 650), font=('Arial', 12), resizable=True)
    # window['-TIME-'].update(disabled=True)
    window.Refresh()

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if values['P1'] == True:
            print('cola')
            type = 'cola'
            if event == '-FOLDER-':
                folder = values['-FOLDER-']
                path_vol = f'{folder}/DATA/'
                window['-VOL-'].update(disabled=False, values=os.listdir(path_vol))

                #сразу подгружаем данные обо всех испытуемых в специальный словарик
                #должны быть подготовлены данные об этом
                try:
                    with open(f'{folder}/data_about_volunteers.csv', encoding='windows-1251') as f:
                        f.readline()
                        for row in f:
                            row = row.strip().split(';')
                            final_data[row[0]] = row[1:]
                    #ещё сразу спарсим информацию о WTP, оценке вкуса и цены. Если нужно, их можно выгрузить отдельно

                    # window['-ETC-'].update(disabled=False)

                    # window['-REPS-'].update(disabled=False)
                    # window['-REPF-'].update(disabled=False)
                    # window['-OPEN-'].update(disabled=False)
                except:
                    sg.popup("В папку с данными поместите файл с информацией о волонтёрах")
            if event == '-VOL-':
                window['-EXP-'].update(disabled=False)
                path_time = f'{folder}/DATA/{values["-VOL-"]}/times.txt'
                path_type = f'{folder}/DATA/{values["-VOL-"]}/order.txt'
                path_answers = f'{folder}/DATA/{values["-VOL-"]}/first.txt'
                path_edf = f'{folder}/DATA/{values["-VOL-"]}/{values["-VOL-"]}.edf'
                raw = mne.io.read_raw_edf(path_edf, preload=True)
                raw.apply_function(lambda x: x * 1e-6)  # переводим в милливольты
                dict_times_closed, dict_times_open = parse_files(path_time,
                                                                 path_type, order=order_cola)  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                ch_names = ['EEG Fp1',
                            'EEG Fp2',
                            'EEG F3',
                            'EEG F4',
                            'EEG P3',
                            'EEG P4',
                            'EEG O1',
                            'EEG O2',
                            ]
                raw.pick(ch_names)
                eeg_signals = ['EEG Fp1: лобный полюс, слева',
                               'EEG Fp2: лобный полюс, справа',
                               'EEG F3: фронтальная часть, слева',
                               'EEG F4:фронтальная часть, справа',
                               'EEG P3: задняя теменная (париетальная) часть, слева',
                               'EEG P4: задняя теменная (париетальная) часть, справа',
                               'EEG O1: затылочная (окципитальная) часть, слева',
                               'EEG O2: затылочная (окципитальная) часть, справа',
                               'все каналы'
                               ]
                data_raw = raw.get_data()
                data = {
                    'EEG Fp1': [''],
                    'EEG Fp2': [''],
                    'EEG F3': [''],
                    'EEG F4': [''],
                    'EEG P3': [''],
                    'EEG P4': [''],
                    'EEG O1': [''],
                    'EEG O2': ['']
                }
                for ch_name, channel in zip(ch_names, data_raw):
                    data[ch_name].append(channel)

                window['-ELEC-'].update(disabled=False, values=eeg_signals)

            if event == '-EXP-':
                # print(values["-EXP-"])
                if values["-EXP-"] == 'закрытый':
                        # window['-REPS-'].update(disabled=False)
                        window['-REPF-'].update(disabled=False)
                        window['-NOFILTCLOSE-'].update(disabled=False)
                        window['-OPEN-'].update(disabled=True)
                        window['-NOFILTOPEN-'].update(disabled=True)
                        timestamps = [f'{str(k)} : {v[0]}' for k, v in dict_times_closed.items()]
                        window['-TIME-'].update(disabled=False, values=timestamps)
                        parsed_wtp_etc = WTP_price_taste(folder, type='close')

                        pre_data = {
                            "cola1": [],
                            "cola2": [],
                            "cola_zero1": [],
                            "cola_zero2": [],
                            "d_cola1": [],
                            "d_cola2": [],
                            "d_zero1": [],
                            "d_zero2": [],
                            "funky1": [],
                            "funky2": [],
                            "chernogolovka1": [],
                            "chernogolovka2": []
                        }
                        dict_times = dict_times_closed

                else:
                    # window['-REPS-'].update(disabled=True)
                    window['-REPF-'].update(disabled=True)
                    window['-OPEN-'].update(disabled=False)
                    window['-NOFILTOPEN-'].update(disabled=False)
                    window['-PLOT-'].update(disabled=True)
                    timestamps = [f'{str(k)} : {v[0]}' for k, v in dict_times_open.items()]
                    window['-TIME-'].update(disabled=False, values=timestamps)
                    parsed_wtp_etc = WTP_price_taste(folder, type='open', order=order_cola)

                    # pre_data = {
                    #     'cola':[],
                    #     'chernogolovka':[],
                    #     'cola_zero':[],
                    #     'd_cola':[],
                    #     'd_zero':[],
                    #     'funky':[]
                    # }
                    pre_data = dict.fromkeys(order_cola, [])
                    dict_times = dict_times_open

            if event == '-ELEC-':

                chosen_electrode = values['-ELEC-']
                if not flag_timestamps:
                    # dict_times = parse_files(path_time,path_type,path_answers)
                    # timestamps = [f'{str(k)} : {"; ".join(v)}' for k, v in dict_times.items()]
                    # window['-TIME-'].update(disabled=False, values=timestamps)
                    flag_timestamps = True

            if event == '-TIME-':

                stamp = float(values['-TIME-'].split(':')[0])
                window['-START-'].update(disabled=False, value=stamp)
                length = int(dict_times[stamp][1])
                window['-LEN-'].update(disabled=False, value=length)
                window['-PLOT-'].update(disabled=False)
            if event == '-PLOT-':
                #здесь мы рассматриваем случай, когда строим 8 графиков по нужным электродам
                # или один, если хочется посмотреть конкретнее
                if values["-ELEC-"] == '' or values["-ELEC-"] == 'все каналы':

                    #временные метки
                    if values['-START-'] == '':
                        a = 0
                    else:
                        a = int(float(values['-START-']) * RATE)
                    b = a + int(float(values['-LEN-']) * RATE)

                    if fig_agg is not None:
                        delete_fig_agg(fig_agg)
                    #теперь нам нужно достать данные по каждому электроду
                    # print(data)
                    #когда известны отрезки, сделаем ICA и добавим эти данные в data
                    filt_raw = raw.copy().filter(l_freq=1.0, h_freq=None)
                    filt_raw.crop(tmin=a//RATE, tmax=b//RATE)
                    ica = ICA(n_components=5, max_iter="auto", random_state=97)
                    ica.fit(filt_raw)
                    ica.apply(filt_raw, exclude=[0]) #!!!!!!!!!!!
                    ica_data = filt_raw.get_data()
                    data_for_multi_plot = copy.deepcopy(data)
                    # data_for_multi_plot['EEG Fp1'].append('GOTYA!')

                    for k, channel in zip(data_for_multi_plot.keys(), ica_data):
                        data_for_multi_plot[k].append(channel)

                    # print(2222, data_for_multi_plot)
                    fig = fig_maker_multi_ica(window, RATE, data_for_multi_plot, a, b)
                    fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                    window.Refresh()

                    #после отрисовки нужно удалить данные по ica из словаря
                    # for k, v in data.items():
                    #     data[k] = v[:-1]
                    # window['-SEG-'].update(disabled=False)
                    # window['-ADD-'].update(disabled=False)
                    # window['-FFT-'].update(disabled=False)

                else:
                    elct = values["-ELEC-"].split(': ')[0]

                    # временные метки
                    if values['-START-'] == '':
                        a = 0
                    else:
                        a = int(float(values['-START-']) * RATE)
                    b = a + int(float(values['-LEN-']) * RATE)

                    if fig_agg is not None:
                        delete_fig_agg(fig_agg)

                    # когда известны отрезки, сделаем ICA и добавим эти данные в data
                    filt_raw = raw.copy().filter(l_freq=1.0, h_freq=None)
                    filt_raw.crop(tmin=a // RATE, tmax=b // RATE)
                    ica = ICA(n_components=5, max_iter="auto", random_state=97)
                    ica.fit(filt_raw)
                    ica.apply(filt_raw, exclude=[0])  # !!!!!!!!!!!
                    ica_data = filt_raw.get_data()
                    data_for_one_plot = data[elct]
                    # print(1111111, data[elct])
                    i = ch_names.index(elct)
                    data_for_one_plot.append(ica_data[i])
                    # print(1111, data_for_one_plot)
                    fig = fig_maker_ica(window, RATE, data_for_one_plot, a, b)
                    fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                    window.Refresh()

                    # fig = fig_maker(window, d, a, b)
                    # fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                    # window.Refresh()
                    # window['-SEG-'].update(disabled=False)
                    # window['-ADD-'].update(disabled=False)
                    # window['-FFT-'].update(disabled=False)
                # нужен ли функционал, чтобы можно было потом выбрать, по какому промежутку строим?

            if event == '-SEG-':
                '''
                нажали кнопку "Добавить отрезок"
                Сразу расчитывается FFT
                '''
                if values['-TIME-'] == '':
                    sg.popup('Выберите временную метку')
                else:
                    type = values['-TIME-'].split(': ')[1].strip()
                    start = float(values['-START-'].replace(',', '.'))
                    finish = start + float(values['-LEN-'].replace(',', '.'))
                    line_eeg = []
                    for v in data.values():
                        freqs = [str(i).replace('.', ',') for i in calc_fft(v[-1], RATE, start, finish)] #v[-1] - это данные сигнала
                        line_eeg.extend(freqs[:2])
                    pre_data[type].extend(line_eeg)

            if event == '-ADD-':
                volunteer = values['-VOL-']
                for k in final_data.keys():
                    if final_data[k][0] == volunteer:
                        final_data[k].append(pre_data)
                        break
                sg.popup("Данные сохранены")

            if event == '-FFT-':
                unused = []
                for k, v in final_data.items():
                    if not isinstance(v[-1], dict):
                        unused.append(k)
                if len(unused) > 0:
                    unused = [final_data[k][0] for k in unused]
                    sg.popup("Невозможно выгрузить данные, нет информации по волонтёру/ам):\n", '\n'.join(unused))
                else:

                    path_result=f'{folder}/results/'
                    if not os.path.exists(path_result):
                        os.mkdir(path_result)
                    with open(
                            f'{path_result}/result {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv',
                            'w') as csv_result:

                        print(';'.join(['ID', 'Age', 'Sex', 'Brand',
                             'taste', 'similarity', 'WTP', 'price',
                             'Fp1-alpha', 'Fp1-beta',
                             'Fp2-alpha', 'Fp2-beta',
                             'F3-alpha', 'F3 -beta',
                             'F4-alpha', 'F4 -beta',
                             'P3-alpha', 'P3 -beta',
                             'P4-alpha', 'P4 -beta',
                             'O3-alpha', 'O3 - beta',
                             'O4-alpha', 'O4 -beta',
                                ]), file=csv_result)
                        for id, values in final_data.items():
                            name = values[0]
                            for brand, fft_results in values[-1].items():
                                print(';'.join([id, values[1], values[2], brand, parsed_wtp_etc[name]['taste'][brand],
                                                parsed_wtp_etc[name]['similarity'][brand], parsed_wtp_etc[name]['WTP'][brand],
                                                parsed_wtp_etc[name]['price'][brand]] + fft_results), file=csv_result)

                    sg.popup("Файл сохранён в папку")
            if event == '-ETC-':
                f =True
                while f:
                    if export_wtp_etc(folder, parsed_wtp_etc) != -1:
                        f = False
                        sg.popup("Файл сохранён в папку results")

            if event == '-REPS-':
                '''выгрузка общего отчёта закрытые 5 секунд в начале + применение ICA'''
                data_ica = ica_preproc_first_5_sec(folder, RATE)
                for k in final_data.keys():
                    # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', final_data[k][0])
                    final_data[k].append(data_ica[final_data[k][0]])

                path_result = f'{folder}/results/'
                if not os.path.exists(path_result):
                    os.mkdir(path_result)
                with open(
                        f'{path_result}/clear_result_{folder.split("/")[-1]} {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv',
                        'w') as csv_result:
                    print(';'.join(['ID', 'name', 'Age', 'Sex', 'Brand',
                                    'taste', 'similarity', 'WTP', 'price',
                                    'F3-alpha_1', 'F3-alpha_2', 'F3-alpha_3', 'F3-alpha_4', 'F3-alpha_5',
                                    'F3-beta_1', 'F3-beta_2', 'F3-beta_3', 'F3-beta_4', 'F3-beta_5',
                                    'F3-gamma_1', 'F3-gamma_2', 'F3-gamma_3', 'F3-gamma_4', 'F3-gamma_5',
                                    'F4-alpha_1', 'F4-alpha_2', 'F4-alpha_3', 'F4-alpha_4', 'F4-alpha_5',
                                    'F4-beta_1', 'F4-beta_2', 'F4-beta_3', 'F4-beta_4', 'F4-beta_5',
                                    'F4-gamma_1', 'F4-gamma_2', 'F4-gamma_3', 'F4-gamma_4', 'F4-gamma_5',
                                    'Fp1-alpha_1', 'Fp1-alpha_2', 'Fp1-alpha_3', 'Fp1-alpha_4', 'Fp1-alpha_5',
                                    'Fp1-beta_1', 'Fp1-beta_2', 'Fp1-beta_3', 'Fp1-beta_4', 'Fp1-beta_5',
                                    'Fp1-gamma_1', 'Fp1-gamma_2', 'Fp1-gamma_3', 'Fp1-gamma_4', 'Fp1-gamma_5',
                                    'Fp2-alpha_1', 'Fp2-alpha_2', 'Fp2-alpha_3', 'Fp2-alpha_4', 'Fp2-alpha_5',
                                    'Fp2-beta_1', 'Fp2-beta_2', 'Fp2-beta_3', 'Fp2-beta_4', 'Fp2-beta_5',
                                    'Fp2-gamma_1', 'Fp2-gamma_2', 'Fp2-gamma_3', 'Fp2-gamma_4', 'Fp2-gamma_5',
                                    'O3-alpha_1', 'O3-alpha_2', 'O3-alpha_3', 'O3-alpha_4', 'O3-alpha_5',
                                    'O3-beta_1', 'O3-beta_2', 'O3-beta_3', 'O3-beta_4', 'O3-beta_5',
                                    '03-gamma_1', 'O3-gamma_2', 'O3-gamma_3', 'O3-gamma_4', 'O3-gamma_5',
                                    'O4-alpha_1', 'O4-alpha_2', 'O4-alpha_3', 'O4-alpha_4', 'O4-alpha_5',
                                    'O4-beta_1', 'O4-beta_2', 'O4-beta_3', 'O4-beta_4', 'O4-beta_5',
                                    'O4-gamma_1', 'O4-gamma_2', 'O4-gamma_3', 'O4-gamma_4', 'O4-gamma_5',
                                    'P3-alpha_1', 'P3-alpha_2', 'P3-alpha_3', 'P3-alpha_4', 'P3-alpha_5',
                                    'P3-beta_1', 'P3-beta_2', 'P3-beta_3', 'P3-beta_4', 'P3-beta_5',
                                    'P3-gamma_1', 'P3-gamma_2', 'P3-gamma_3', 'P3-gamma_4', 'P3-gamma_5',
                                    'P4-alpha_1', 'P4-alpha_2', 'P4-alpha_3', 'P4-alpha_4', 'P4-alpha_5',
                                    'P4-beta_1', 'P4-beta_2', 'P4-beta_3', 'P4-beta_4', 'P4-beta_5',
                                    'P4-gamma_1', 'P4-gamma_2', 'P4-gamma_3', 'P4-gamma_4', 'P4-gamma_5',
                                    ]), file=csv_result)
                    for id, values in final_data.items():
                        name = values[0]
                        for brand, fft_results in values[-1].items():
                            print(';'.join([id, values[0], values[1], values[2], brand, parsed_wtp_etc[name]['taste'][brand],
                                            parsed_wtp_etc[name]['similarity'][brand], parsed_wtp_etc[name]['WTP'][brand],
                                            parsed_wtp_etc[name]['price'][brand], fft_results]), file=csv_result)

                sg.popup("Файл сохранён в папку")

            if event == '-REPF-':
                '''выгрузка общего отчёта закрытые с -10 по -5 секу + применение ICA'''
                data_ica = ica_preproc_last_5_sec(folder, RATE, type=type)
                for k in final_data.keys():
                    # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', final_data[k][0])
                    final_data[k].append(data_ica[final_data[k][0]])

                path_result = f'{folder}/results/'
                with open(
                        f'{path_result}/clear_close_result_{folder.split("/")[-1]} {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv',
                        'w') as csv_result:
                    print(';'.join(['ID', 'name', 'Age', 'Sex', 'Brand',
                                    'taste', 'similarity', 'WTP', 'price',
                                    'F3-alpha_1', 'F3-alpha_2', 'F3-alpha_3', 'F3-alpha_4', 'F3-alpha_5',
                                    'F3-beta_1', 'F3-beta_2', 'F3-beta_3', 'F3-beta_4', 'F3-beta_5',
                                    'F3-gamma_1', 'F3-gamma_2', 'F3-gamma_3', 'F3-gamma_4', 'F3-gamma_5',
                                    'F4-alpha_1', 'F4-alpha_2', 'F4-alpha_3', 'F4-alpha_4', 'F4-alpha_5',
                                    'F4-beta_1', 'F4-beta_2', 'F4-beta_3', 'F4-beta_4', 'F4-beta_5',
                                    'F4-gamma_1', 'F4-gamma_2', 'F4-gamma_3', 'F4-gamma_4', 'F4-gamma_5',
                                    'Fp1-alpha_1', 'Fp1-alpha_2', 'Fp1-alpha_3', 'Fp1-alpha_4', 'Fp1-alpha_5',
                                    'Fp1-beta_1', 'Fp1-beta_2', 'Fp1-beta_3', 'Fp1-beta_4', 'Fp1-beta_5',
                                    'Fp1-gamma_1', 'Fp1-gamma_2', 'Fp1-gamma_3', 'Fp1-gamma_4', 'Fp1-gamma_5',
                                    'Fp2-alpha_1', 'Fp2-alpha_2', 'Fp2-alpha_3', 'Fp2-alpha_4', 'Fp2-alpha_5',
                                    'Fp2-beta_1', 'Fp2-beta_2', 'Fp2-beta_3', 'Fp2-beta_4', 'Fp2-beta_5',
                                    'Fp2-gamma_1', 'Fp2-gamma_2', 'Fp2-gamma_3', 'Fp2-gamma_4', 'Fp2-gamma_5',
                                    'O3-alpha_1', 'O3-alpha_2', 'O3-alpha_3', 'O3-alpha_4', 'O3-alpha_5',
                                    'O3-beta_1', 'O3-beta_2', 'O3-beta_3', 'O3-beta_4', 'O3-beta_5',
                                    '03-gamma_1', 'O3-gamma_2', 'O3-gamma_3', 'O3-gamma_4', 'O3-gamma_5',
                                    'O4-alpha_1', 'O4-alpha_2', 'O4-alpha_3', 'O4-alpha_4', 'O4-alpha_5',
                                    'O4-beta_1', 'O4-beta_2', 'O4-beta_3', 'O4-beta_4', 'O4-beta_5',
                                    'O4-gamma_1', 'O4-gamma_2', 'O4-gamma_3', 'O4-gamma_4', 'O4-gamma_5',
                                    'P3-alpha_1', 'P3-alpha_2', 'P3-alpha_3', 'P3-alpha_4', 'P3-alpha_5',
                                    'P3-beta_1', 'P3-beta_2', 'P3-beta_3', 'P3-beta_4', 'P3-beta_5',
                                    'P3-gamma_1', 'P3-gamma_2', 'P3-gamma_3', 'P3-gamma_4', 'P3-gamma_5',
                                    'P4-alpha_1', 'P4-alpha_2', 'P4-alpha_3', 'P4-alpha_4', 'P4-alpha_5',
                                    'P4-beta_1', 'P4-beta_2', 'P4-beta_3', 'P4-beta_4', 'P4-beta_5',
                                    'P4-gamma_1', 'P4-gamma_2', 'P4-gamma_3', 'P4-gamma_4', 'P4-gamma_5'
                                    ]), file=csv_result)
                    for id, values in final_data.items():
                        name = values[0]
                        for brand, fft_results in values[-1].items():
                            print(';'.join([id, values[0], values[1], values[2], brand, parsed_wtp_etc[name]['taste'][brand],
                                            parsed_wtp_etc[name]['similarity'][brand], parsed_wtp_etc[name]['WTP'][brand],
                                            parsed_wtp_etc[name]['price'][brand], fft_results]), file=csv_result)

                sg.popup("Файл сохранён в папку")

            if event == '-OPEN-':
                '''выгрузка общего отчёта по ОТКРЫТОМУ эксперименту секунды в конце + применение ICA'''
                data_ica = ica_preproc_open_5_sec(folder, RATE, type=type, order=order_cola)
                print(data_ica.values())
                for k in final_data.keys():
                    # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', final_data[k][0])
                    final_data[k].append(data_ica[final_data[k][0]])
                # print(parsed_wtp_etc)
                path_result = f'{folder}/results/'
                with open(
                        f'{path_result}/clear_open_result_{folder.split("/")[-1]} {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv',
                        'w') as csv_result:
                    print(';'.join(['ID', 'name', 'Age', 'Sex', 'Brand',
                                    'taste_stated', 'taste_revealed', 'price', 'WTP',
                                    'F3-alpha_1', 'F3-alpha_2', 'F3-alpha_3', 'F3-alpha_4', 'F3-alpha_5',
                                    'F3-beta_1', 'F3-beta_2', 'F3-beta_3', 'F3-beta_4', 'F3-beta_5',
                                    'F3-gamma_1', 'F3-gamma_2', 'F3-gamma_3', 'F3-gamma_4', 'F3-gamma_5',
                                    'F4-alpha_1', 'F4-alpha_2', 'F4-alpha_3', 'F4-alpha_4', 'F4-alpha_5',
                                    'F4-beta_1', 'F4-beta_2', 'F4-beta_3', 'F4-beta_4', 'F4-beta_5',
                                    'F4-gamma_1', 'F4-gamma_2', 'F4-gamma_3', 'F4-gamma_4', 'F4-gamma_5',
                                    'Fp1-alpha_1', 'Fp1-alpha_2', 'Fp1-alpha_3', 'Fp1-alpha_4', 'Fp1-alpha_5',
                                    'Fp1-beta_1', 'Fp1-beta_2', 'Fp1-beta_3', 'Fp1-beta_4', 'Fp1-beta_5',
                                    'Fp1-gamma_1', 'Fp1-gamma_2', 'Fp1-gamma_3', 'Fp1-gamma_4', 'Fp1-gamma_5',
                                    'Fp2-alpha_1', 'Fp2-alpha_2', 'Fp2-alpha_3', 'Fp2-alpha_4', 'Fp2-alpha_5',
                                    'Fp2-beta_1', 'Fp2-beta_2', 'Fp2-beta_3', 'Fp2-beta_4', 'Fp2-beta_5',
                                    'Fp2-gamma_1', 'Fp2-gamma_2', 'Fp2-gamma_3', 'Fp2-gamma_4', 'Fp2-gamma_5',
                                    'O3-alpha_1', 'O3-alpha_2', 'O3-alpha_3', 'O3-alpha_4', 'O3-alpha_5',
                                    'O3-beta_1', 'O3-beta_2', 'O3-beta_3', 'O3-beta_4', 'O3-beta_5',
                                    '03-gamma_1', 'O3-gamma_2', 'O3-gamma_3', 'O3-gamma_4', 'O3-gamma_5',
                                    'O4-alpha_1', 'O4-alpha_2', 'O4-alpha_3', 'O4-alpha_4', 'O4-alpha_5',
                                    'O4-beta_1', 'O4-beta_2', 'O4-beta_3', 'O4-beta_4', 'O4-beta_5',
                                    'O4-gamma_1', 'O4-gamma_2', 'O4-gamma_3', 'O4-gamma_4', 'O4-gamma_5',
                                    'P3-alpha_1', 'P3-alpha_2', 'P3-alpha_3', 'P3-alpha_4', 'P3-alpha_5',
                                    'P3-beta_1', 'P3-beta_2', 'P3-beta_3', 'P3-beta_4', 'P3-beta_5',
                                    'P3-gamma_1', 'P3-gamma_2', 'P3-gamma_3', 'P3-gamma_4', 'P3-gamma_5',
                                    'P4-alpha_1', 'P4-alpha_2', 'P4-alpha_3', 'P4-alpha_4', 'P4-alpha_5',
                                    'P4-beta_1', 'P4-beta_2', 'P4-beta_3', 'P4-beta_4', 'P4-beta_5',
                                    'P4-gamma_1', 'P4-gamma_2', 'P4-gamma_3', 'P4-gamma_4', 'P4-gamma_5'
                                    ]), file=csv_result)
                    for id, values in final_data.items():
                        name = values[0]
                        # print(values[-1].items())
                        for brand, fft_results in values[-1].items():
                            # print(parsed_wtp_etc)
                            print(';'.join([id, values[0], values[1], values[2], brand, parsed_wtp_etc[name]['taste_stated'][brand],
                                            parsed_wtp_etc[name]['taste_revealed'][brand], parsed_wtp_etc[name]['price'][brand],
                                            parsed_wtp_etc[name]['WTP'][brand], fft_results]), file=csv_result)

                sg.popup("Файл сохранён в папку")

            if event == '-NOFILTCLOSE-':
                '''выгрузка общего отчёта закрытые с -10 по -5 сек БЕЗ ICA'''
                data_ica = no_ica_last_5_sec(folder, RATE, order=order_cola)
                for k in final_data.keys():
                    # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', final_data[k][0])
                    final_data[k].append(data_ica[final_data[k][0]])

                path_result = f'{folder}/results/'
                with open(
                        f'{path_result}/nofilter_close_result_{folder.split("/")[-1]} {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv',
                        'w') as csv_result:
                    print(';'.join(['ID', 'name', 'Age', 'Sex', 'Brand',
                                    'taste', 'similarity', 'WTP', 'price',
                                    'F3-alpha_1', 'F3-alpha_2', 'F3-alpha_3', 'F3-alpha_4', 'F3-alpha_5',
                                    'F3-beta_1', 'F3-beta_2', 'F3-beta_3', 'F3-beta_4', 'F3-beta_5',
                                    'F3-gamma_1', 'F3-gamma_2', 'F3-gamma_3', 'F3-gamma_4', 'F3-gamma_5',
                                    'F4-alpha_1', 'F4-alpha_2', 'F4-alpha_3', 'F4-alpha_4', 'F4-alpha_5',
                                    'F4-beta_1', 'F4-beta_2', 'F4-beta_3', 'F4-beta_4', 'F4-beta_5',
                                    'F4-gamma_1', 'F4-gamma_2', 'F4-gamma_3', 'F4-gamma_4', 'F4-gamma_5',
                                    'Fp1-alpha_1', 'Fp1-alpha_2', 'Fp1-alpha_3', 'Fp1-alpha_4', 'Fp1-alpha_5',
                                    'Fp1-beta_1', 'Fp1-beta_2', 'Fp1-beta_3', 'Fp1-beta_4', 'Fp1-beta_5',
                                    'Fp1-gamma_1', 'Fp1-gamma_2', 'Fp1-gamma_3', 'Fp1-gamma_4', 'Fp1-gamma_5',
                                    'Fp2-alpha_1', 'Fp2-alpha_2', 'Fp2-alpha_3', 'Fp2-alpha_4', 'Fp2-alpha_5',
                                    'Fp2-beta_1', 'Fp2-beta_2', 'Fp2-beta_3', 'Fp2-beta_4', 'Fp2-beta_5',
                                    'Fp2-gamma_1', 'Fp2-gamma_2', 'Fp2-gamma_3', 'Fp2-gamma_4', 'Fp2-gamma_5',
                                    'O3-alpha_1', 'O3-alpha_2', 'O3-alpha_3', 'O3-alpha_4', 'O3-alpha_5',
                                    'O3-beta_1', 'O3-beta_2', 'O3-beta_3', 'O3-beta_4', 'O3-beta_5',
                                    '03-gamma_1', 'O3-gamma_2', 'O3-gamma_3', 'O3-gamma_4', 'O3-gamma_5',
                                    'O4-alpha_1', 'O4-alpha_2', 'O4-alpha_3', 'O4-alpha_4', 'O4-alpha_5',
                                    'O4-beta_1', 'O4-beta_2', 'O4-beta_3', 'O4-beta_4', 'O4-beta_5',
                                    'O4-gamma_1', 'O4-gamma_2', 'O4-gamma_3', 'O4-gamma_4', 'O4-gamma_5',
                                    'P3-alpha_1', 'P3-alpha_2', 'P3-alpha_3', 'P3-alpha_4', 'P3-alpha_5',
                                    'P3-beta_1', 'P3-beta_2', 'P3-beta_3', 'P3-beta_4', 'P3-beta_5',
                                    'P3-gamma_1', 'P3-gamma_2', 'P3-gamma_3', 'P3-gamma_4', 'P3-gamma_5',
                                    'P4-alpha_1', 'P4-alpha_2', 'P4-alpha_3', 'P4-alpha_4', 'P4-alpha_5',
                                    'P4-beta_1', 'P4-beta_2', 'P4-beta_3', 'P4-beta_4', 'P4-beta_5',
                                    'P4-gamma_1', 'P4-gamma_2', 'P4-gamma_3', 'P4-gamma_4', 'P4-gamma_5'
                                    ]), file=csv_result)
                    for id, values in final_data.items():
                        name = values[0]
                        for brand, fft_results in values[-1].items():
                            print(';'.join(
                                [id, values[0], values[1], values[2], brand, parsed_wtp_etc[name]['taste'][brand],
                                 parsed_wtp_etc[name]['similarity'][brand], parsed_wtp_etc[name]['WTP'][brand],
                                 parsed_wtp_etc[name]['price'][brand], fft_results]), file=csv_result)

                sg.popup("Файл сохранён в папку")

            if event == '-NOFILTOPEN-':
                '''выгрузка общего отчёта по ОТКРЫТОМУ эксперименту -6 по -1 сек + БЕЗ ICA'''
                data_ica = no_ica_open_5_sec(folder, RATE, order=order_cola)
                print(data_ica)
                for k in final_data.keys():
                    final_data[k].append(data_ica[final_data[k][0]])
                path_result = f'{folder}/results/'
                with open(
                        f'{path_result}/nofilter_open_result_{folder.split("/")[-1]} {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv',
                        'w') as csv_result:
                    print(';'.join(['ID', 'name', 'Age', 'Sex', 'Brand',
                                     'taste_stated', 'taste_revealed', 'price', 'WTP',
                                    'F3-alpha_1', 'F3-alpha_2', 'F3-alpha_3', 'F3-alpha_4', 'F3-alpha_5',
                                    'F3-beta_1', 'F3-beta_2', 'F3-beta_3', 'F3-beta_4', 'F3-beta_5',
                                    'F3-gamma_1', 'F3-gamma_2', 'F3-gamma_3', 'F3-gamma_4', 'F3-gamma_5',
                                    'F4-alpha_1', 'F4-alpha_2', 'F4-alpha_3', 'F4-alpha_4', 'F4-alpha_5',
                                    'F4-beta_1', 'F4-beta_2', 'F4-beta_3', 'F4-beta_4', 'F4-beta_5',
                                    'F4-gamma_1', 'F4-gamma_2', 'F4-gamma_3', 'F4-gamma_4', 'F4-gamma_5',
                                    'Fp1-alpha_1', 'Fp1-alpha_2', 'Fp1-alpha_3', 'Fp1-alpha_4', 'Fp1-alpha_5',
                                    'Fp1-beta_1', 'Fp1-beta_2', 'Fp1-beta_3', 'Fp1-beta_4', 'Fp1-beta_5',
                                    'Fp1-gamma_1', 'Fp1-gamma_2', 'Fp1-gamma_3', 'Fp1-gamma_4', 'Fp1-gamma_5',
                                    'Fp2-alpha_1', 'Fp2-alpha_2', 'Fp2-alpha_3', 'Fp2-alpha_4', 'Fp2-alpha_5',
                                    'Fp2-beta_1', 'Fp2-beta_2', 'Fp2-beta_3', 'Fp2-beta_4', 'Fp2-beta_5',
                                    'Fp2-gamma_1', 'Fp2-gamma_2', 'Fp2-gamma_3', 'Fp2-gamma_4', 'Fp2-gamma_5',
                                    'O3-alpha_1', 'O3-alpha_2', 'O3-alpha_3', 'O3-alpha_4', 'O3-alpha_5',
                                    'O3-beta_1', 'O3-beta_2', 'O3-beta_3', 'O3-beta_4', 'O3-beta_5',
                                    '03-gamma_1', 'O3-gamma_2', 'O3-gamma_3', 'O3-gamma_4', 'O3-gamma_5',
                                    'O4-alpha_1', 'O4-alpha_2', 'O4-alpha_3', 'O4-alpha_4', 'O4-alpha_5',
                                    'O4-beta_1', 'O4-beta_2', 'O4-beta_3', 'O4-beta_4', 'O4-beta_5',
                                    'O4-gamma_1', 'O4-gamma_2', 'O4-gamma_3', 'O4-gamma_4', 'O4-gamma_5',
                                    'P3-alpha_1', 'P3-alpha_2', 'P3-alpha_3', 'P3-alpha_4', 'P3-alpha_5',
                                    'P3-beta_1', 'P3-beta_2', 'P3-beta_3', 'P3-beta_4', 'P3-beta_5',
                                    'P3-gamma_1', 'P3-gamma_2', 'P3-gamma_3', 'P3-gamma_4', 'P3-gamma_5',
                                    'P4-alpha_1', 'P4-alpha_2', 'P4-alpha_3', 'P4-alpha_4', 'P4-alpha_5',
                                    'P4-beta_1', 'P4-beta_2', 'P4-beta_3', 'P4-beta_4', 'P4-beta_5',
                                    'P4-gamma_1', 'P4-gamma_2', 'P4-gamma_3', 'P4-gamma_4', 'P4-gamma_5'
                                    ]), file=csv_result)

                    for id, values in final_data.items():
                        name = values[0]

                        for brand, fft_results in values[-1].items():
                            # print(brand)
                            print(';'.join([id, values[0], values[1], values[2], brand, parsed_wtp_etc[name]['taste_stated'][brand],
                                            parsed_wtp_etc[name]['taste_revealed'][brand], parsed_wtp_etc[name]['price'][brand],
                                            parsed_wtp_etc[name]['WTP'][brand], fft_results]), file=csv_result)

                sg.popup("Файл сохранён в папку")

        else:
            print('honey')
            type = 'honey'
            if event == '-FOLDER-':
                folder = values['-FOLDER-']
                path_vol = f'{folder}/DATA/'
                window['-VOL-'].update(disabled=False, values=os.listdir(path_vol))

                # сразу подгружаем данные обо всех испытуемых в специальный словарик
                # должны быть подготовлены данные об этом
                try:
                    with open(f'{folder}/data_about_volunteers.csv', encoding='windows-1251') as f:
                        f.readline()
                        for row in f:
                            row = row.strip().split(';')
                            final_data[row[0]] = row[1:]
                    # ещё сразу спарсим информацию о WTP, оценке вкуса и цены. Если нужно, их можно выгрузить отдельно

                    # window['-ETC-'].update(disabled=False)

                    # window['-REPS-'].update(disabled=False)
                    # window['-REPF-'].update(disabled=False)
                    # window['-OPEN-'].update(disabled=False)
                except:
                    sg.popup("В папку с данными поместите файл с информацией о волонтёрах")
            if event == '-VOL-':
                window['-EXP-'].update(disabled=False)
                path_time = f'{folder}/DATA/{values["-VOL-"]}/times.txt'
                path_type = f'{folder}/DATA/{values["-VOL-"]}/order.txt'
                path_answers = f'{folder}/DATA/{values["-VOL-"]}/first.txt'
                path_edf = f'{folder}/DATA/{values["-VOL-"]}/{values["-VOL-"]}.edf'
                raw = mne.io.read_raw_edf(path_edf, preload=True)
                raw.apply_function(lambda x: x * 1e-6)  # переводим в милливольты
                dict_times_closed, dict_times_open = parse_files_honey(path_time,
                                                                 path_type,
                                                                 order=order_honey)  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                ch_names = ['EEG Fp1',
                            'EEG Fp2',
                            'EEG F3',
                            'EEG F4',
                            'EEG P3',
                            'EEG P4',
                            'EEG O1',
                            'EEG O2',
                            ]
                raw.pick(ch_names)
                eeg_signals = ['EEG Fp1: лобный полюс, слева',
                               'EEG Fp2: лобный полюс, справа',
                               'EEG F3: фронтальная часть, слева',
                               'EEG F4:фронтальная часть, справа',
                               'EEG P3: задняя теменная (париетальная) часть, слева',
                               'EEG P4: задняя теменная (париетальная) часть, справа',
                               'EEG O1: затылочная (окципитальная) часть, слева',
                               'EEG O2: затылочная (окципитальная) часть, справа',
                               'все каналы'
                               ]
                data_raw = raw.get_data()
                data = {
                    'EEG Fp1': [''],
                    'EEG Fp2': [''],
                    'EEG F3': [''],
                    'EEG F4': [''],
                    'EEG P3': [''],
                    'EEG P4': [''],
                    'EEG O1': [''],
                    'EEG O2': ['']
                }
                for ch_name, channel in zip(ch_names, data_raw):
                    data[ch_name].append(channel)

                window['-ELEC-'].update(disabled=False, values=eeg_signals)

            if event == '-EXP-':
                # print(values["-EXP-"])
                if values["-EXP-"] == 'закрытый':
                    # window['-REPS-'].update(disabled=False)
                    window['-REPF-'].update(disabled=False)
                    window['-NOFILTCLOSE-'].update(disabled=False)
                    window['-OPEN-'].update(disabled=True)
                    window['-NOFILTOPEN-'].update(disabled=True)
                    timestamps = [f'{str(k)} : {v[0]}' for k, v in dict_times_closed.items()]
                    window['-TIME-'].update(disabled=False, values=timestamps)
                    parsed_wtp_etc = parse_features_honey(folder, type='close')

                    pre_data = {
                        "Bashkirsky": [],
                        "Dalnevostochniy": [],
                        "Dedushkin_uley": [],
                        "Lubomedovo": [],
                        "Medovoye_razdolie": [],
                        "Permskaya_fabrika": [],
                        "Permskiye_pcholy": [],
                    }
                    dict_times = dict_times_closed

                else:
                    # window['-REPS-'].update(disabled=True)
                    window['-REPF-'].update(disabled=True)
                    window['-OPEN-'].update(disabled=False)
                    window['-NOFILTOPEN-'].update(disabled=False)
                    window['-PLOT-'].update(disabled=True)
                    timestamps = [f'{str(k)} : {v[0]}' for k, v in dict_times_open.items()]
                    window['-TIME-'].update(disabled=False, values=timestamps)
                    parsed_wtp_etc = parse_features_honey(folder, type='open', order=order_honey)

                    # pre_data = {
                    #     'cola':[],
                    #     'chernogolovka':[],
                    #     'cola_zero':[],
                    #     'd_cola':[],
                    #     'd_zero':[],
                    #     'funky':[]
                    # }
                    pre_data = dict.fromkeys(order_cola, [])
                    dict_times = dict_times_open

            if event == '-ELEC-':

                chosen_electrode = values['-ELEC-']
                if not flag_timestamps:
                    # dict_times = parse_files(path_time,path_type,path_answers)
                    # timestamps = [f'{str(k)} : {"; ".join(v)}' for k, v in dict_times.items()]
                    # window['-TIME-'].update(disabled=False, values=timestamps)
                    flag_timestamps = True

            if event == '-TIME-':
                stamp = float(values['-TIME-'].split(':')[0])
                window['-START-'].update(disabled=False, value=stamp)
                length = int(dict_times[stamp][1])
                window['-LEN-'].update(disabled=False, value=length)
                window['-PLOT-'].update(disabled=False)
            if event == '-PLOT-':
                # здесь мы рассматриваем случай, когда строим 8 графиков по нужным электродам
                # или один, если хочется посмотреть конкретнее
                if values["-ELEC-"] == '' or values["-ELEC-"] == 'все каналы':

                    # временные метки
                    if values['-START-'] == '':
                        a = 0
                    else:
                        a = int(float(values['-START-']) * RATE)
                    b = a + int(float(values['-LEN-']) * RATE)

                    if fig_agg is not None:
                        delete_fig_agg(fig_agg)
                    # теперь нам нужно достать данные по каждому электроду
                    # print(data)
                    # когда известны отрезки, сделаем ICA и добавим эти данные в data
                    filt_raw = raw.copy().filter(l_freq=1.0, h_freq=None)
                    filt_raw.crop(tmin=a // RATE, tmax=b // RATE)
                    ica = ICA(n_components=5, max_iter="auto", random_state=97)
                    ica.fit(filt_raw)
                    ica.apply(filt_raw, exclude=[0])  # !!!!!!!!!!!
                    ica_data = filt_raw.get_data()
                    data_for_multi_plot = copy.deepcopy(data)
                    # data_for_multi_plot['EEG Fp1'].append('GOTYA!')

                    for k, channel in zip(data_for_multi_plot.keys(), ica_data):
                        data_for_multi_plot[k].append(channel)

                    # print(2222, data_for_multi_plot)
                    fig = fig_maker_multi_ica(window, RATE, data_for_multi_plot, a, b)
                    fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                    window.Refresh()

                    # после отрисовки нужно удалить данные по ica из словаря
                    # for k, v in data.items():
                    #     data[k] = v[:-1]
                    # window['-SEG-'].update(disabled=False)
                    # window['-ADD-'].update(disabled=False)
                    # window['-FFT-'].update(disabled=False)

                else:
                    elct = values["-ELEC-"].split(': ')[0]

                    # временные метки
                    if values['-START-'] == '':
                        a = 0
                    else:
                        a = int(float(values['-START-']) * RATE)
                    b = a + int(float(values['-LEN-']) * RATE)

                    if fig_agg is not None:
                        delete_fig_agg(fig_agg)

                    # когда известны отрезки, сделаем ICA и добавим эти данные в data
                    filt_raw = raw.copy().filter(l_freq=1.0, h_freq=None)
                    filt_raw.crop(tmin=a // RATE, tmax=b // RATE)
                    ica = ICA(n_components=5, max_iter="auto", random_state=97)
                    ica.fit(filt_raw)
                    ica.apply(filt_raw, exclude=[0])  # !!!!!!!!!!!
                    ica_data = filt_raw.get_data()
                    data_for_one_plot = data[elct]
                    print(1111111, data[elct])
                    i = ch_names.index(elct)
                    data_for_one_plot.append(ica_data[i])
                    print(1111, data_for_one_plot)
                    fig = fig_maker_ica(window, RATE, data_for_one_plot, a, b)
                    fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                    window.Refresh()

                    # fig = fig_maker(window, d, a, b)
                    # fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                    # window.Refresh()
                    # window['-SEG-'].update(disabled=False)
                    # window['-ADD-'].update(disabled=False)
                    # window['-FFT-'].update(disabled=False)
                # нужен ли функционал, чтобы можно было потом выбрать, по какому промежутку строим?

            if event == '-SEG-':
                '''
                нажали кнопку "Добавить отрезок"
                Сразу расчитывается FFT
                '''
                if values['-TIME-'] == '':
                    sg.popup('Выберите временную метку')
                else:
                    type = values['-TIME-'].split(': ')[1].strip()
                    start = float(values['-START-'].replace(',', '.'))
                    finish = start + float(values['-LEN-'].replace(',', '.'))
                    line_eeg = []
                    for v in data.values():
                        freqs = [str(i).replace('.', ',') for i in
                                 calc_fft(v[-1], RATE, start, finish)]  # v[-1] - это данные сигнала
                        line_eeg.extend(freqs[:2])
                    pre_data[type].extend(line_eeg)

            if event == '-ADD-':
                volunteer = values['-VOL-']
                for k in final_data.keys():
                    if final_data[k][0] == volunteer:
                        final_data[k].append(pre_data)
                        break
                sg.popup("Данные сохранены")

            if event == '-FFT-':
                unused = []
                for k, v in final_data.items():
                    if not isinstance(v[-1], dict):
                        unused.append(k)
                if len(unused) > 0:
                    unused = [final_data[k][0] for k in unused]
                    sg.popup("Невозможно выгрузить данные, нет информации по волонтёру/ам):\n", '\n'.join(unused))
                else:

                    path_result = f'{folder}/results/'
                    if not os.path.exists(path_result):
                        os.mkdir(path_result)
                    with open(
                            f'{path_result}/result {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv',
                            'w') as csv_result:

                        print(';'.join(['ID', 'Age', 'Sex', 'Brand',
                                        'taste', 'similarity', 'WTP', 'price',
                                        'Fp1-alpha', 'Fp1-beta',
                                        'Fp2-alpha', 'Fp2-beta',
                                        'F3-alpha', 'F3 -beta',
                                        'F4-alpha', 'F4 -beta',
                                        'P3-alpha', 'P3 -beta',
                                        'P4-alpha', 'P4 -beta',
                                        'O3-alpha', 'O3 - beta',
                                        'O4-alpha', 'O4 -beta',
                                        ]), file=csv_result)
                        for id, values in final_data.items():
                            name = values[0]
                            for brand, fft_results in values[-1].items():
                                print(';'.join([id, values[1], values[2], brand, parsed_wtp_etc[name]['taste'][brand],
                                                parsed_wtp_etc[name]['similarity'][brand],
                                                parsed_wtp_etc[name]['WTP'][brand],
                                                parsed_wtp_etc[name]['price'][brand]] + fft_results), file=csv_result)

                    sg.popup("Файл сохранён в папку")
            if event == '-ETC-':
                f = True
                while f:
                    if export_wtp_etc(folder, parsed_wtp_etc) != -1:
                        f = False
                        sg.popup("Файл сохранён в папку results")

            if event == '-REPS-':
                '''выгрузка общего отчёта закрытые 5 секунд в начале + применение ICA'''
                data_ica = ica_preproc_first_5_sec(folder, RATE,order=order_honey, type_honey='taste')
                for k in final_data.keys():
                    # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', final_data[k][0])
                    final_data[k].append(data_ica[final_data[k][0]])

                # path_result = f'{folder}/results/'
                # if not os.path.exists(path_result):
                #     os.mkdir(path_result)
                # with open(
                #         f'{path_result}/clear_result_{folder.split("/")[-1]} {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv',
                #         'w') as csv_result:
                #     print(';'.join(['ID', 'name', 'Age', 'Sex', 'Brand',
                #                     'taste', 'similarity', 'WTP', 'price',
                #                     'F3-alpha_1', 'F3-alpha_2', 'F3-alpha_3', 'F3-alpha_4', 'F3-alpha_5',
                #                     'F3-beta_1', 'F3-beta_2', 'F3-beta_3', 'F3-beta_4', 'F3-beta_5',
                #                     'F3-gamma_1', 'F3-gamma_2', 'F3-gamma_3', 'F3-gamma_4', 'F3-gamma_5',
                #                     'F4-alpha_1', 'F4-alpha_2', 'F4-alpha_3', 'F4-alpha_4', 'F4-alpha_5',
                #                     'F4-beta_1', 'F4-beta_2', 'F4-beta_3', 'F4-beta_4', 'F4-beta_5',
                #                     'F4-gamma_1', 'F4-gamma_2', 'F4-gamma_3', 'F4-gamma_4', 'F4-gamma_5',
                #                     'Fp1-alpha_1', 'Fp1-alpha_2', 'Fp1-alpha_3', 'Fp1-alpha_4', 'Fp1-alpha_5',
                #                     'Fp1-beta_1', 'Fp1-beta_2', 'Fp1-beta_3', 'Fp1-beta_4', 'Fp1-beta_5',
                #                     'Fp1-gamma_1', 'Fp1-gamma_2', 'Fp1-gamma_3', 'Fp1-gamma_4', 'Fp1-gamma_5',
                #                     'Fp2-alpha_1', 'Fp2-alpha_2', 'Fp2-alpha_3', 'Fp2-alpha_4', 'Fp2-alpha_5',
                #                     'Fp2-beta_1', 'Fp2-beta_2', 'Fp2-beta_3', 'Fp2-beta_4', 'Fp2-beta_5',
                #                     'Fp2-gamma_1', 'Fp2-gamma_2', 'Fp2-gamma_3', 'Fp2-gamma_4', 'Fp2-gamma_5',
                #                     'O3-alpha_1', 'O3-alpha_2', 'O3-alpha_3', 'O3-alpha_4', 'O3-alpha_5',
                #                     'O3-beta_1', 'O3-beta_2', 'O3-beta_3', 'O3-beta_4', 'O3-beta_5',
                #                     '03-gamma_1', 'O3-gamma_2', 'O3-gamma_3', 'O3-gamma_4', 'O3-gamma_5',
                #                     'O4-alpha_1', 'O4-alpha_2', 'O4-alpha_3', 'O4-alpha_4', 'O4-alpha_5',
                #                     'O4-beta_1', 'O4-beta_2', 'O4-beta_3', 'O4-beta_4', 'O4-beta_5',
                #                     'O4-gamma_1', 'O4-gamma_2', 'O4-gamma_3', 'O4-gamma_4', 'O4-gamma_5',
                #                     'P3-alpha_1', 'P3-alpha_2', 'P3-alpha_3', 'P3-alpha_4', 'P3-alpha_5',
                #                     'P3-beta_1', 'P3-beta_2', 'P3-beta_3', 'P3-beta_4', 'P3-beta_5',
                #                     'P3-gamma_1', 'P3-gamma_2', 'P3-gamma_3', 'P3-gamma_4', 'P3-gamma_5',
                #                     'P4-alpha_1', 'P4-alpha_2', 'P4-alpha_3', 'P4-alpha_4', 'P4-alpha_5',
                #                     'P4-beta_1', 'P4-beta_2', 'P4-beta_3', 'P4-beta_4', 'P4-beta_5',
                #                     'P4-gamma_1', 'P4-gamma_2', 'P4-gamma_3', 'P4-gamma_4', 'P4-gamma_5',
                #                     ]), file=csv_result)
                #     for id, values in final_data.items():
                #         name = values[0]
                #         for brand, fft_results in values[-1].items():
                #             print(';'.join(
                #                 [id, values[0], values[1], values[2], brand, parsed_wtp_etc[name]['taste'][brand],
                #                  parsed_wtp_etc[name]['similarity'][brand], parsed_wtp_etc[name]['WTP'][brand],
                #                  parsed_wtp_etc[name]['price'][brand], fft_results]), file=csv_result)
                #
                # sg.popup("Файл сохранён в папку")

            if event == '-REPF-':
                '''выгрузка общего отчёта закрытые в конце + применение ICA'''
                data_ica = ica_preproc_last_5_sec(folder, RATE, type=type, type_honey='taste', order=order_honey)

                for k in final_data.keys():

                    # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', final_data[k][0])
                    final_data[k].append(data_ica[final_data[k][0]]) # в final_data ключи - ID, а в data_ica - фамилии, они в final_data[k][0]

                path_result = f'{folder}/results/'
                if not os.path.exists(path_result):
                    os.mkdir(path_result)
                with open(f'{path_result}/clear_close_result_{folder.split("/")[-1]} {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv', mode='w') as csv_result:
                    print(';'.join(['ID', 'name', 'Age', 'Sex', 'Brand',
                                    'taste', 'quality', 'WTP', 'price',
                                    'f1','f2','f3','f4','f5','f6','f7','f8',
                                    'F3-alpha_1', 'F3-alpha_2', 'F3-alpha_3', 'F3-alpha_4', 'F3-alpha_5',
                                    'F3-beta_1', 'F3-beta_2', 'F3-beta_3', 'F3-beta_4', 'F3-beta_5',
                                    'F3-gamma_1', 'F3-gamma_2', 'F3-gamma_3', 'F3-gamma_4', 'F3-gamma_5',
                                    'F4-alpha_1', 'F4-alpha_2', 'F4-alpha_3', 'F4-alpha_4', 'F4-alpha_5',
                                    'F4-beta_1', 'F4-beta_2', 'F4-beta_3', 'F4-beta_4', 'F4-beta_5',
                                    'F4-gamma_1', 'F4-gamma_2', 'F4-gamma_3', 'F4-gamma_4', 'F4-gamma_5',
                                    'Fp1-alpha_1', 'Fp1-alpha_2', 'Fp1-alpha_3', 'Fp1-alpha_4', 'Fp1-alpha_5',
                                    'Fp1-beta_1', 'Fp1-beta_2', 'Fp1-beta_3', 'Fp1-beta_4', 'Fp1-beta_5',
                                    'Fp1-gamma_1', 'Fp1-gamma_2', 'Fp1-gamma_3', 'Fp1-gamma_4', 'Fp1-gamma_5',
                                    'Fp2-alpha_1', 'Fp2-alpha_2', 'Fp2-alpha_3', 'Fp2-alpha_4', 'Fp2-alpha_5',
                                    'Fp2-beta_1', 'Fp2-beta_2', 'Fp2-beta_3', 'Fp2-beta_4', 'Fp2-beta_5',
                                    'Fp2-gamma_1', 'Fp2-gamma_2', 'Fp2-gamma_3', 'Fp2-gamma_4', 'Fp2-gamma_5',
                                    'O3-alpha_1', 'O3-alpha_2', 'O3-alpha_3', 'O3-alpha_4', 'O3-alpha_5',
                                    'O3-beta_1', 'O3-beta_2', 'O3-beta_3', 'O3-beta_4', 'O3-beta_5',
                                    '03-gamma_1', 'O3-gamma_2', 'O3-gamma_3', 'O3-gamma_4', 'O3-gamma_5',
                                    'O4-alpha_1', 'O4-alpha_2', 'O4-alpha_3', 'O4-alpha_4', 'O4-alpha_5',
                                    'O4-beta_1', 'O4-beta_2', 'O4-beta_3', 'O4-beta_4', 'O4-beta_5',
                                    'O4-gamma_1', 'O4-gamma_2', 'O4-gamma_3', 'O4-gamma_4', 'O4-gamma_5',
                                    'P3-alpha_1', 'P3-alpha_2', 'P3-alpha_3', 'P3-alpha_4', 'P3-alpha_5',
                                    'P3-beta_1', 'P3-beta_2', 'P3-beta_3', 'P3-beta_4', 'P3-beta_5',
                                    'P3-gamma_1', 'P3-gamma_2', 'P3-gamma_3', 'P3-gamma_4', 'P3-gamma_5',
                                    'P4-alpha_1', 'P4-alpha_2', 'P4-alpha_3', 'P4-alpha_4', 'P4-alpha_5',
                                    'P4-beta_1', 'P4-beta_2', 'P4-beta_3', 'P4-beta_4', 'P4-beta_5',
                                    'P4-gamma_1', 'P4-gamma_2', 'P4-gamma_3', 'P4-gamma_4', 'P4-gamma_5'
                                    ]), file=csv_result)
                    for id, values in final_data.items():
                        name = values[0]
                        print(parsed_wtp_etc[name]['taste'])
                        for brand, fft_results in values[-1].items():
                            print(';'.join(
                                [id, values[0], values[1], values[2], brand,
                                 parsed_wtp_etc[name]['taste'][brand],
                                 parsed_wtp_etc[name]['quality'][brand],
                                 parsed_wtp_etc[name]['WTP'][brand],
                                 parsed_wtp_etc[name]['price'][brand],
                                 parsed_wtp_etc[name]['f1'][brand],
                                 parsed_wtp_etc[name]['f2'][brand],
                                 parsed_wtp_etc[name]['f3'][brand],
                                 parsed_wtp_etc[name]['f4'][brand],
                                 parsed_wtp_etc[name]['f5'][brand],
                                 parsed_wtp_etc[name]['f6'][brand],
                                 parsed_wtp_etc[name]['f7'][brand],
                                 parsed_wtp_etc[name]['f8'][brand],
                                 fft_results]), file=csv_result)

                sg.popup("Файл сохранён в папку")

            if event == '-OPEN-':
                '''выгрузка общего отчёта по ОТКРЫТОМУ эксперименту -10 по -5 сек + применение ICA'''
                data_ica = ica_preproc_open_5_sec(folder, RATE, order=order_honey, type=type, type_honey='taste')
                for k in final_data.keys():
                    # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', final_data[k][0])
                    final_data[k].append(data_ica[final_data[k][0]])
                # print(parsed_wtp_etc)
                path_result = f'{folder}/results/'
                if not os.path.exists(path_result):
                    os.mkdir(path_result)
                with open(
                        f'{path_result}/clear_open_result_{folder.split("/")[-1]} {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv',
                        'w') as csv_result:
                    print(';'.join(['ID', 'name', 'Age', 'Sex', 'Brand',
                                    'taste_stated', 'taste_revealed', 'WTP', 'price', 'quality',
                                    'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8',
                                    'F3-alpha_1', 'F3-alpha_2', 'F3-alpha_3', 'F3-alpha_4', 'F3-alpha_5',
                                    'F3-beta_1', 'F3-beta_2', 'F3-beta_3', 'F3-beta_4', 'F3-beta_5',
                                    'F3-gamma_1', 'F3-gamma_2', 'F3-gamma_3', 'F3-gamma_4', 'F3-gamma_5',
                                    'F4-alpha_1', 'F4-alpha_2', 'F4-alpha_3', 'F4-alpha_4', 'F4-alpha_5',
                                    'F4-beta_1', 'F4-beta_2', 'F4-beta_3', 'F4-beta_4', 'F4-beta_5',
                                    'F4-gamma_1', 'F4-gamma_2', 'F4-gamma_3', 'F4-gamma_4', 'F4-gamma_5',
                                    'Fp1-alpha_1', 'Fp1-alpha_2', 'Fp1-alpha_3', 'Fp1-alpha_4', 'Fp1-alpha_5',
                                    'Fp1-beta_1', 'Fp1-beta_2', 'Fp1-beta_3', 'Fp1-beta_4', 'Fp1-beta_5',
                                    'Fp1-gamma_1', 'Fp1-gamma_2', 'Fp1-gamma_3', 'Fp1-gamma_4', 'Fp1-gamma_5',
                                    'Fp2-alpha_1', 'Fp2-alpha_2', 'Fp2-alpha_3', 'Fp2-alpha_4', 'Fp2-alpha_5',
                                    'Fp2-beta_1', 'Fp2-beta_2', 'Fp2-beta_3', 'Fp2-beta_4', 'Fp2-beta_5',
                                    'Fp2-gamma_1', 'Fp2-gamma_2', 'Fp2-gamma_3', 'Fp2-gamma_4', 'Fp2-gamma_5',
                                    'O3-alpha_1', 'O3-alpha_2', 'O3-alpha_3', 'O3-alpha_4', 'O3-alpha_5',
                                    'O3-beta_1', 'O3-beta_2', 'O3-beta_3', 'O3-beta_4', 'O3-beta_5',
                                    '03-gamma_1', 'O3-gamma_2', 'O3-gamma_3', 'O3-gamma_4', 'O3-gamma_5',
                                    'O4-alpha_1', 'O4-alpha_2', 'O4-alpha_3', 'O4-alpha_4', 'O4-alpha_5',
                                    'O4-beta_1', 'O4-beta_2', 'O4-beta_3', 'O4-beta_4', 'O4-beta_5',
                                    'O4-gamma_1', 'O4-gamma_2', 'O4-gamma_3', 'O4-gamma_4', 'O4-gamma_5',
                                    'P3-alpha_1', 'P3-alpha_2', 'P3-alpha_3', 'P3-alpha_4', 'P3-alpha_5',
                                    'P3-beta_1', 'P3-beta_2', 'P3-beta_3', 'P3-beta_4', 'P3-beta_5',
                                    'P3-gamma_1', 'P3-gamma_2', 'P3-gamma_3', 'P3-gamma_4', 'P3-gamma_5',
                                    'P4-alpha_1', 'P4-alpha_2', 'P4-alpha_3', 'P4-alpha_4', 'P4-alpha_5',
                                    'P4-beta_1', 'P4-beta_2', 'P4-beta_3', 'P4-beta_4', 'P4-beta_5',
                                    'P4-gamma_1', 'P4-gamma_2', 'P4-gamma_3', 'P4-gamma_4', 'P4-gamma_5'
                                    ]), file=csv_result)
                    for id, values in final_data.items():
                        name = values[0]

                        for brand, fft_results in values[-1].items():
                            # print(brand)
                            print(';'.join([id, values[0], values[1], values[2], brand,
                                            parsed_wtp_etc[name]['taste_stated'][brand],
                                            parsed_wtp_etc[name]['taste_revealed'][brand],
                                            parsed_wtp_etc[name]['WTP'][brand],
                                            parsed_wtp_etc[name]['price'][brand],
                                            parsed_wtp_etc[name]['quality'][brand],
                                            parsed_wtp_etc[name]['f1'][brand],
                                            parsed_wtp_etc[name]['f2'][brand],
                                            parsed_wtp_etc[name]['f3'][brand],
                                            parsed_wtp_etc[name]['f4'][brand],
                                            parsed_wtp_etc[name]['f5'][brand],
                                            parsed_wtp_etc[name]['f6'][brand],
                                            parsed_wtp_etc[name]['f7'][brand],
                                            parsed_wtp_etc[name]['f8'][brand],
                                            fft_results]), file=csv_result)

                sg.popup("Файл сохранён в папку")

            if event == '-NOFILTCLOSE-':
                '''выгрузка общего отчёта закрытые БЕЗ ICA'''
                data_ica = no_ica_last_5_sec(folder, RATE, order= order_honey, type=type, type_honey='taste')
                for k in final_data.keys():
                    # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', final_data[k][0])
                    final_data[k].append(data_ica[final_data[k][0]])

                path_result = f'{folder}/results/'
                if not os.path.exists(path_result):
                    os.mkdir(path_result)
                with open(
                        f'{path_result}/nofilter_close_result_{folder.split("/")[-1]} {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv',
                        'w') as csv_result:
                    print(';'.join(['ID', 'name', 'Age', 'Sex', 'Brand',
                                    'taste', 'quality', 'WTP', 'price',
                                    'f1','f2','f3','f4','f5','f6','f7','f8',
                                    'F3-alpha_1', 'F3-alpha_2', 'F3-alpha_3', 'F3-alpha_4', 'F3-alpha_5',
                                    'F3-beta_1', 'F3-beta_2', 'F3-beta_3', 'F3-beta_4', 'F3-beta_5',
                                    'F3-gamma_1', 'F3-gamma_2', 'F3-gamma_3', 'F3-gamma_4', 'F3-gamma_5',
                                    'F4-alpha_1', 'F4-alpha_2', 'F4-alpha_3', 'F4-alpha_4', 'F4-alpha_5',
                                    'F4-beta_1', 'F4-beta_2', 'F4-beta_3', 'F4-beta_4', 'F4-beta_5',
                                    'F4-gamma_1', 'F4-gamma_2', 'F4-gamma_3', 'F4-gamma_4', 'F4-gamma_5',
                                    'Fp1-alpha_1', 'Fp1-alpha_2', 'Fp1-alpha_3', 'Fp1-alpha_4', 'Fp1-alpha_5',
                                    'Fp1-beta_1', 'Fp1-beta_2', 'Fp1-beta_3', 'Fp1-beta_4', 'Fp1-beta_5',
                                    'Fp1-gamma_1', 'Fp1-gamma_2', 'Fp1-gamma_3', 'Fp1-gamma_4', 'Fp1-gamma_5',
                                    'Fp2-alpha_1', 'Fp2-alpha_2', 'Fp2-alpha_3', 'Fp2-alpha_4', 'Fp2-alpha_5',
                                    'Fp2-beta_1', 'Fp2-beta_2', 'Fp2-beta_3', 'Fp2-beta_4', 'Fp2-beta_5',
                                    'Fp2-gamma_1', 'Fp2-gamma_2', 'Fp2-gamma_3', 'Fp2-gamma_4', 'Fp2-gamma_5',
                                    'O3-alpha_1', 'O3-alpha_2', 'O3-alpha_3', 'O3-alpha_4', 'O3-alpha_5',
                                    'O3-beta_1', 'O3-beta_2', 'O3-beta_3', 'O3-beta_4', 'O3-beta_5',
                                    '03-gamma_1', 'O3-gamma_2', 'O3-gamma_3', 'O3-gamma_4', 'O3-gamma_5',
                                    'O4-alpha_1', 'O4-alpha_2', 'O4-alpha_3', 'O4-alpha_4', 'O4-alpha_5',
                                    'O4-beta_1', 'O4-beta_2', 'O4-beta_3', 'O4-beta_4', 'O4-beta_5',
                                    'O4-gamma_1', 'O4-gamma_2', 'O4-gamma_3', 'O4-gamma_4', 'O4-gamma_5',
                                    'P3-alpha_1', 'P3-alpha_2', 'P3-alpha_3', 'P3-alpha_4', 'P3-alpha_5',
                                    'P3-beta_1', 'P3-beta_2', 'P3-beta_3', 'P3-beta_4', 'P3-beta_5',
                                    'P3-gamma_1', 'P3-gamma_2', 'P3-gamma_3', 'P3-gamma_4', 'P3-gamma_5',
                                    'P4-alpha_1', 'P4-alpha_2', 'P4-alpha_3', 'P4-alpha_4', 'P4-alpha_5',
                                    'P4-beta_1', 'P4-beta_2', 'P4-beta_3', 'P4-beta_4', 'P4-beta_5',
                                    'P4-gamma_1', 'P4-gamma_2', 'P4-gamma_3', 'P4-gamma_4', 'P4-gamma_5'
                                    ]), file=csv_result)
                    for id, values in final_data.items():
                        name = values[0]
                        for brand, fft_results in values[-1].items():
                            print(';'.join(
                                [id, values[0], values[1], values[2], brand,
                                 parsed_wtp_etc[name]['taste'][brand],
                                 parsed_wtp_etc[name]['quality'][brand],
                                 parsed_wtp_etc[name]['WTP'][brand],
                                 parsed_wtp_etc[name]['price'][brand],
                                 parsed_wtp_etc[name]['f1'][brand],
                                 parsed_wtp_etc[name]['f2'][brand],
                                 parsed_wtp_etc[name]['f3'][brand],
                                 parsed_wtp_etc[name]['f4'][brand],
                                 parsed_wtp_etc[name]['f5'][brand],
                                 parsed_wtp_etc[name]['f6'][brand],
                                 parsed_wtp_etc[name]['f7'][brand],
                                 parsed_wtp_etc[name]['f8'][brand],
                                 fft_results]), file=csv_result)

                sg.popup("Файл сохранён в папку")

            if event == '-NOFILTOPEN-':
                '''выгрузка общего отчёта по ОТКРЫТОМУ эксперименту -6 по -1 сек + БЕЗ ICA'''
                data_ica = no_ica_open_5_sec(folder, RATE, order=order_honey, type=type, type_honey='taste')
                for k in final_data.keys():
                    # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', final_data[k][0])
                    final_data[k].append(data_ica[final_data[k][0]])
                # print(parsed_wtp_etc)
                path_result = f'{folder}/results/'
                if not os.path.exists(path_result):
                    os.mkdir(path_result)
                with open(
                        f'{path_result}/nofilter_open_result_{folder.split("/")[-1]} {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv',
                        'w') as csv_result:
                    print(';'.join(['ID', 'name', 'Age', 'Sex', 'Brand',
                                    'taste_stated', 'taste_revealed', 'WTP', 'price', 'quality',
                                    'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8',
                                    'F3-alpha_1', 'F3-alpha_2', 'F3-alpha_3', 'F3-alpha_4', 'F3-alpha_5',
                                    'F3-beta_1', 'F3-beta_2', 'F3-beta_3', 'F3-beta_4', 'F3-beta_5',
                                    'F3-gamma_1', 'F3-gamma_2', 'F3-gamma_3', 'F3-gamma_4', 'F3-gamma_5',
                                    'F4-alpha_1', 'F4-alpha_2', 'F4-alpha_3', 'F4-alpha_4', 'F4-alpha_5',
                                    'F4-beta_1', 'F4-beta_2', 'F4-beta_3', 'F4-beta_4', 'F4-beta_5',
                                    'F4-gamma_1', 'F4-gamma_2', 'F4-gamma_3', 'F4-gamma_4', 'F4-gamma_5',
                                    'Fp1-alpha_1', 'Fp1-alpha_2', 'Fp1-alpha_3', 'Fp1-alpha_4', 'Fp1-alpha_5',
                                    'Fp1-beta_1', 'Fp1-beta_2', 'Fp1-beta_3', 'Fp1-beta_4', 'Fp1-beta_5',
                                    'Fp1-gamma_1', 'Fp1-gamma_2', 'Fp1-gamma_3', 'Fp1-gamma_4', 'Fp1-gamma_5',
                                    'Fp2-alpha_1', 'Fp2-alpha_2', 'Fp2-alpha_3', 'Fp2-alpha_4', 'Fp2-alpha_5',
                                    'Fp2-beta_1', 'Fp2-beta_2', 'Fp2-beta_3', 'Fp2-beta_4', 'Fp2-beta_5',
                                    'Fp2-gamma_1', 'Fp2-gamma_2', 'Fp2-gamma_3', 'Fp2-gamma_4', 'Fp2-gamma_5',
                                    'O3-alpha_1', 'O3-alpha_2', 'O3-alpha_3', 'O3-alpha_4', 'O3-alpha_5',
                                    'O3-beta_1', 'O3-beta_2', 'O3-beta_3', 'O3-beta_4', 'O3-beta_5',
                                    '03-gamma_1', 'O3-gamma_2', 'O3-gamma_3', 'O3-gamma_4', 'O3-gamma_5',
                                    'O4-alpha_1', 'O4-alpha_2', 'O4-alpha_3', 'O4-alpha_4', 'O4-alpha_5',
                                    'O4-beta_1', 'O4-beta_2', 'O4-beta_3', 'O4-beta_4', 'O4-beta_5',
                                    'O4-gamma_1', 'O4-gamma_2', 'O4-gamma_3', 'O4-gamma_4', 'O4-gamma_5',
                                    'P3-alpha_1', 'P3-alpha_2', 'P3-alpha_3', 'P3-alpha_4', 'P3-alpha_5',
                                    'P3-beta_1', 'P3-beta_2', 'P3-beta_3', 'P3-beta_4', 'P3-beta_5',
                                    'P3-gamma_1', 'P3-gamma_2', 'P3-gamma_3', 'P3-gamma_4', 'P3-gamma_5',
                                    'P4-alpha_1', 'P4-alpha_2', 'P4-alpha_3', 'P4-alpha_4', 'P4-alpha_5',
                                    'P4-beta_1', 'P4-beta_2', 'P4-beta_3', 'P4-beta_4', 'P4-beta_5',
                                    'P4-gamma_1', 'P4-gamma_2', 'P4-gamma_3', 'P4-gamma_4', 'P4-gamma_5'
                                    ]), file=csv_result)
                    for id, values in final_data.items():
                        name = values[0]

                        for brand, fft_results in values[-1].items():
                            # print(brand)
                            print(';'.join([id, values[0], values[1], values[2], brand,
                                            parsed_wtp_etc[name]['taste_stated'][brand],
                                            parsed_wtp_etc[name]['taste_revealed'][brand],
                                            parsed_wtp_etc[name]['price'][brand],
                                            parsed_wtp_etc[name]['WTP'][brand],
                                            parsed_wtp_etc[name]['quality'][brand],
                                            parsed_wtp_etc[name]['f1'][brand],
                                            parsed_wtp_etc[name]['f2'][brand],
                                            parsed_wtp_etc[name]['f3'][brand],
                                            parsed_wtp_etc[name]['f4'][brand],
                                            parsed_wtp_etc[name]['f5'][brand],
                                            parsed_wtp_etc[name]['f6'][brand],
                                            parsed_wtp_etc[name]['f7'][brand],
                                            parsed_wtp_etc[name]['f8'][brand],
                                            fft_results]),
                                              file=csv_result)

                sg.popup("Файл сохранён в папку")

    window.close()
