import PySimpleGUI as sg
import csv
import numpy as np
# import matplotlib as mplt
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from scipy.fft import rfft, rfftfreq
import time
import os, fnmatch

from GUIgraphics import fig_maker, fig_maker_multi, draw_figure, delete_fig_agg
from Analyse import calc_fft, ica_preproc
from parse import parse_files, WTP_price_taste, export_wtp_etc

'''
BrainWave Explorer - программа, предназначенная для анализа данных
'''


if __name__ == '__main__':
    sg.theme('LightBlue2')  # это раскраска темы
    RATE = 500 #частота считываний в 1 с
    volunteers_combo = sg.Combo([], font=('Arial Bold', 12), expand_x=True, enable_events=True,
                               readonly=True, key='-VOL-', disabled=True)
    electrode_combo = sg.Combo([], font=('Arial Bold', 12), expand_x=True, enable_events=True, readonly=True,
                                key='-ELEC-', disabled=True)
    timestamps_combo = sg.Combo([], font=('Arial Bold', 12), expand_x=True, enable_events=True, readonly=True,
                                key='-TIME-', disabled=True)
    fig_agg = None
    files = []
    t = []
    final_data = {} #словарь, со словарями?? в котором будут храниться результаты
    m = 0
    '''так как в PySimpleGUI нет функции проверки состояния объектов(WTF!!!),
    то я завожу отдельную переменную как флажок, чтобы проверять, были ли уже подкгружены временные метки или нет'''
    flag_timestamps = False

    '''отрисовка формы'''
    layout = [
        [sg.Text('Выберите папку, в которой содержатся данные с эксперимента'),
         sg.In(size=(25, 1), enable_events=True, key='-FOLDER-'), sg.FolderBrowse()],
        [sg.Text('Испытуемый'), volunteers_combo],
        [sg.Text('Электрод'), electrode_combo],
        [sg.Text('Выберите временную метку'), timestamps_combo],
        [sg.Text('Начало временного отрезка'), sg.InputText(key='-START-', size=(10, 10), disabled=True),
         sg.Text('Продолжительность (сек)'), sg.InputText(key='-LEN-', disabled=True)],
        [sg.Submit('Построить график', key='-PLOT-', disabled=True), sg.Submit('Выгрузить общий отчёт', key='-REP-', disabled=True)],
        [sg.Canvas(key='-CANVAS-')],
        [sg.Button('Добавить отрезок', key='-SEG-', disabled=True),
         sg.Button('Сохранить данные по волонтёру', key='-ADD-', disabled=True),
         sg.Button('Выгрузить таблицу', key='-FFT-', disabled=True),
         sg.Button('Выгрузить WTP etc', key='-ETC-', disabled=True)]
    ]
    # кнопка "Выгрузить общий отчёт" - временная

    window = sg.Window('FFT for EEG', layout, finalize=True, size=(815, 650), font=('Arial', 12), resizable=True)
    # window['-TIME-'].update(disabled=True)
    window.Refresh()

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
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
                parsed_wtp_etc = WTP_price_taste(folder)
                window['-ETC-'].update(disabled=False)
                window['-REP-'].update(disabled=False)
            except:
                sg.popup("В папку с данными поместите файл с информацией о волонтёрах")
        if event == '-VOL-':
            flag_timestamps = False
            path_time = f'{folder}/DATA/{values["-VOL-"]}/times.txt'
            path_type = f'{folder}/DATA/{values["-VOL-"]}/order.txt'
            path_answers = f'{folder}/DATA/{values["-VOL-"]}/first.txt'
            path_eeg = f'{folder}/DATA/{values["-VOL-"]}/CSV_Export'
            pattern = "EEG*"
            listOfFiles = os.listdir(path_eeg)
            #здесь можно ещё добавить пояснение, что это за сигнал, откуда
            #так работает быстрее - мы не загружаем сразу все данные,
            # нужные нам электроды Fp1, Fp2, F3,  F4, P3, P4, O1, O2
            # если мы работаем с CSV, то они соответствуют номерам:
            # EEG0, EEG1, EEG3, EEG4, EEG13, EEG14, EEG18, EEG19
            electrods = [0, 1, 3, 4, 13, 14, 18, 19]

            eeg_signals = [file for file in listOfFiles if (fnmatch.fnmatch(file, pattern) and (int(file[4:-4]) in electrods))]
            data = {'EEG_0.csv': ['Fp1', 'лобный полюс, слева'],
                    'EEG_1.csv': ['Fp2', 'лобный полюс, справа'],
                    'EEG_3.csv': ['F3', 'фронтальная часть, слева (принятие решений?)'],
                    'EEG_4.csv': ['F4', 'фронтальная часть, справа (принятие решений?)'],
                    'EEG_13.csv': ['P3', 'задняя теменная (париетальная) часть, слева (запланированное движение)'],
                    'EEG_14.csv': ['P4', 'задняя теменная (париетальная) часть, справа (запланированное движение)'],
                    'EEG_18.csv': ['O1', 'затылочная (окципитальная) часть, слева (зрение)'],
                    'EEG_19.csv': ['O2', 'затылочная (окципитальная) часть, справа (зрение)']}

            #поэтому сразу подгружаем данные об электродах при выборе волонтёра, чтобы потом не обновлять их
            # путь к файлу, где лежат данные по электродам path_eeg
            try:
                for i in range(len(eeg_signals)):
                    with open(f'{path_eeg}/{eeg_signals[i]}') as f: # какой файл выбран
                        data[eeg_signals[i]].append( list([float(i.replace(',', '.')) * 1e-6 for i in list(csv.reader(f, delimiter=';'))[0]]))
                        eeg_signals[i] = f'{data[eeg_signals[i]][0]}, {data[eeg_signals[i]][1]}, {eeg_signals[i]}'
                print(type(data), len(data))
                eeg_signals.append('все каналы')
                window['-ELEC-'].update(disabled=False, values=eeg_signals)
                dict_times = parse_files(path_time, path_type)
                timestamps = [f'{str(k)} : {v[0]}' for k, v in dict_times.items()]
                window['-TIME-'].update(disabled=False, values=timestamps)

                #словарик, в который будут сохранены все данные по этому волотёру для рассчёта FFT
                #можно использовать, чтобы сбросить данные о респонденте
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
            except:
                sg.popup('Проверьте расположение файлов ЭЭГ')

        if event == '-ELEC-':
            chosen_electrode = values['-ELEC-']
            if not flag_timestamps:
                # dict_times = parse_files(path_time,path_type,path_answers)
                # timestamps = [f'{str(k)} : {"; ".join(v)}' for k, v in dict_times.items()]
                # window['-TIME-'].update(disabled=False, values=timestamps)
                flag_timestamps = True

        if event == '-TIME-':
            stamp = float(values['-TIME-'].split(':')[0])
            #print(stamp)
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
                print(type(data), len(data))
                fig = fig_maker_multi(window, RATE, data, a, b)
                fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                window.Refresh()
                window['-SEG-'].update(disabled=False)
                window['-ADD-'].update(disabled=False)
                window['-FFT-'].update(disabled=False)

            else:
                file_csv = values["-ELEC-"].split(', ')[-1]
                data_for_one_plot = data[file_csv][-1]

                m = values['-TIME-']
                if values['-START-'] == '':
                    a = 0
                else:
                    a = int(float(values['-START-']) * RATE)
                if values['-LEN-'] == '':
                    b = len(data[a:])
                else:
                    b = a + int(float(values['-LEN-']) * RATE)

                if fig_agg is not None:
                    delete_fig_agg(RATE, fig_agg)
                d = data_for_one_plot[a:b]

                fig = fig_maker(window, d, a, b)
                fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                window.Refresh()
                window['-SEG-'].update(disabled=False)
                window['-ADD-'].update(disabled=False)
                window['-FFT-'].update(disabled=False)
            # нужен ли функционал, чтобы можно было потом выбрать, по какому промежутку строим?

        if event == '-SEG-':
            '''
            нажали кнопку "Добавить отрезок"
            Сразу расчитывается FFT
            '''
            print(values['-TIME-'])
            if values['-TIME-'] == '':
                print(1)
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
            #print(volunteer)
            for k in final_data.keys():
                if final_data[k][0] == volunteer:
                    final_data[k].append(pre_data)
                    break
            sg.popup("Данные сохранены")
            '''for k, v in final_data.items():
                print(k, v)'''

        if event == '-FFT-':
            unused = []
            for k, v in final_data.items():
                print(k, v)
                if not isinstance(v[-1], dict):
                    unused.append(k)
            # print(unused)
            # print(final_data)
            if len(unused) > 0:
                unused = [final_data[k][0] for k in unused]
                sg.popup("Невозможно выгрузить данные, нет информации по волонтёру/ам):\n", '\n'.join(unused))
            else:
                path_result=f'{folder}/results/'
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
                         'O4-alpha', 'O4 -beta'
                            ]), file=csv_result)
                    for id, values in final_data.items():
                        name = values[0]
                        #print(values)
                        for brand, fft_results in values[-1].items():

                            '''print(';'.join([id, values[1], values[2], brand, parsed_wtp_etc[name]['taste'][brand],
                                            parsed_wtp_etc[name]['similarity'][brand], parsed_wtp_etc[name]['WTP'][brand],
                                            parsed_wtp_etc[name]['price'][brand]] + fft_results))'''
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

        if event == '-REP-':
            '''выгрузка общего отчёт + применение ICA'''
            data_ica = ica_preproc(folder, RATE)
            print(data_ica.keys())
            for k in final_data.keys():
                    final_data[k].append(data_ica[final_data[k][0]])

            path_result = f'{folder}/results/'
            with open(
                    f'{path_result}/clear_result {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv',
                    'w') as csv_result:
                print(';'.join(['ID', 'name', 'Age', 'Sex', 'Brand',
                                'taste', 'similarity', 'WTP', 'price',
                                'F3-alpha_1', 'F3-alpha_2', 'F3-alpha_3', 'F3-alpha_4', 'F3-alpha_5',
                                'F3-beta_1', 'F3-beta_2', 'F3-beta_3', 'F3-beta_4', 'F3-beta_5',
                                'F4-alpha_1', 'F4-alpha_2', 'F4-alpha_3', 'F4-alpha_4', 'F4-alpha_5',
                                'F4-beta_1', 'F4-beta_2', 'F4-beta_3', 'F4-beta_4', 'F4-beta_5',
                                'Fp1-alpha_1', 'Fp1-alpha_2', 'Fp1-alpha_3', 'Fp1-alpha_4', 'Fp1-alpha_5',
                                'Fp1-beta_1', 'Fp1-beta_2', 'Fp1-beta_3', 'Fp1-beta_4', 'Fp1-beta_5',
                                'Fp2-alpha_1', 'Fp2-alpha_2', 'Fp2-alpha_3', 'Fp2-alpha_4', 'Fp2-alpha_5',
                                'Fp2-beta_1', 'Fp2-beta_2', 'Fp2-beta_3', 'Fp2-beta_4', 'Fp2-beta_5',
                                'O3-alpha_1', 'O3-alpha_2', 'O3-alpha_3', 'O3-alpha_4', 'O3-alpha_5',
                                'O3-beta_1', 'O3-beta_2', 'O3-beta_3', 'O3-beta_4', 'O3-beta_5',
                                'O4-alpha_1', 'O4-alpha_2', 'O4-alpha_3', 'O4-alpha_4', 'O4-alpha_5',
                                'P3-alpha_1', 'P3-alpha_2', 'P3-alpha_3', 'P3-alpha_4', 'P3-alpha_5',
                                'P3-beta_1', 'P3-beta_2', 'P3-beta_3', 'P3-beta_4', 'P3-beta_5',
                                'P4-alpha_1', 'P4-alpha_2', 'P4-alpha_3', 'P4-alpha_4', 'P4-alpha_5',
                                'P4-beta_1', 'P4-beta_2', 'P4-beta_3', 'P4-beta_4', 'P4-beta_5'
                                ]), file=csv_result)
                for id, values in final_data.items():
                    name = values[0]
                    # print(values)
                    for brand, fft_results in values[-1].items():
                        # print(';'.join([id, values[1], values[2], brand, parsed_wtp_etc[name]['taste'][brand],
                        #                 parsed_wtp_etc[name]['similarity'][brand], parsed_wtp_etc[name]['WTP'][brand],
                        #                 parsed_wtp_etc[name]['price'][brand]] + fft_results))
                        print(';'.join([id, values[0], values[1], values[2], brand, parsed_wtp_etc[name]['taste'][brand],
                                        parsed_wtp_etc[name]['similarity'][brand], parsed_wtp_etc[name]['WTP'][brand],
                                        parsed_wtp_etc[name]['price'][brand], fft_results]), file=csv_result)

            sg.popup("Файл сохранён в папку")


    window.close()
