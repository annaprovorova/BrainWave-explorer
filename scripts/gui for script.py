import PySimpleGUI as sg
import csv
import numpy as np
import matplotlib as mplt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.fft import rfft, rfftfreq
import time
import os, fnmatch

'''функция для обновления графика'''
def fig_maker(window, data_one_channel, time_start=8.6, time_finish=9.6):  # this should be called as a thread, then time.sleep() here would not freeze the GUI
   global RATE
   t = np.arange(time_start/RATE, time_finish/RATE, 1 / RATE)
   fig = mplt.figure.Figure(figsize=(8, 4), dpi=100)
   ax = fig.add_subplot(1, 1, 1)
   ax.plot(t, data_one_channel)
   ax.set_xlabel("Время, сек")
   ax.set_ylabel("Амплитуда, миллиВольты")
   window.write_event_value('-THREAD-', 'done.')
   time.sleep(1)
   return fig

def fig_maker_multi(window, data, time_start=8.6, time_finish=9.6):  # this should be called as a thread, then time.sleep() here would not freeze the GUI
   global RATE
   t = np.arange(time_start / RATE, time_finish / RATE, 1 / RATE)

   fig = mplt.figure.Figure(figsize=(8, 4), dpi=100)
   gs = fig.add_gridspec(8, hspace=0)
   axs = gs.subplots(sharex=True, sharey=True)
   i = 0
   for v in data.values():
       axs[i].plot(t, v[-1][time_start:time_finish])
       axs[i].set_ylabel(v[0],  rotation=0, fontweight='bold', color='orange')
       axs[i].label_outer()    # Hide x labels and tick labels for all but bottom plot
       i += 1


   window.write_event_value('-THREAD-', 'done.')
   time.sleep(1)
   return fig

'''функция для отрисовки графика, создание виджета'''
def draw_figure(canvas, figure):
   tkcanvas = FigureCanvasTkAgg(figure, canvas)
   tkcanvas.draw()
   tkcanvas.get_tk_widget().pack(side='top', fill='both', expand=1)
   return tkcanvas


'''функция для удаления старого графика'''
def delete_fig_agg(fig_agg):
   fig_agg.get_tk_widget().forget()
   plt.close('all')


'''функция для расчёта FFT и разделения его по диапазонам частот'''
def calc_fft(data, time_start, time_finish):
    global RATE
    yf = np.abs(rfft(data))**2
    #print(time_start, time_finish)
    time_for_axes = np.arange(time_start, time_finish, 1/RATE)
    xf = rfftfreq(len(time_for_axes), 1/RATE)
    # debug print(len(xf), time_finish, time_start)
    yf.sort()
    i = 0
    agr_alpha = 0
    agr_beta = 0
    agr_gamma = 0
    agr_delta = 0
    agr_teta = 0
    while i < (len(yf)) and xf[i] <= 4.0:
        agr_delta += yf[i]
        i += 1
    while i < (len(yf)) and xf[i] <= 8.0:
        agr_teta += yf[i]
        i += 1
    while i < (len(yf)) and xf[i] <= 13.0:
        agr_alpha += yf[i]
        i += 1
    while i < (len(yf)) and xf[i] <= 30.0:
        agr_beta += yf[i]
        i += 1
    while i < (len(yf)) and xf[i] <= 60.0:
        agr_gamma += yf[i]
        i += 1
    return [agr_alpha, agr_beta, agr_gamma, agr_delta, agr_teta]


'''функция для парсинга меток времени, вида шоколада и ответов'''
def parse_files(path_time, path_type):
    parsed_time = dict() #словарь, в котором ключами будут метки времени, а значениями то, что происходит
    time_file = open(path_time, encoding="utf-8")
    type_file = open(path_type, encoding="utf-8")
    # в изначальном файлике все данные повторяются по 2 раза.
    # нам удобнее ввести уникальные значения, например, cola1 и cola2
    # поэтому мы заводим множество, с помощью которого будем проверять, встречался ли нам уже такой бренд
    brand_check = set()

    time_file.readline() #пропускаем строку в файле с началом эксперимента

    for i in range(12):
        label = float(time_file.readline().split()[1])
        next_label = float(time_file.readline().split()[1])
        cola_type = type_file.readline().strip()
        if cola_type in brand_check:
            parsed_time[label] = [cola_type + '2', next_label-label]
        else:
            parsed_time[label] = [cola_type + '1', next_label - label]
            brand_check.add(cola_type)

    #если для анализа нужны данные в открытую, то нужно разкомментировать этот кусочек
    # for i in range(6):
    #     parsed_time[float(time_file.readline().split()[1])] = ['просмотр изображения']
    #     parsed_time[float(time_file.readline().split()[1])] = ['первый глоток']
    #     parsed_time[float(time_file.readline().split()[1])] = ['сигнал перед питьём воды']

    time_file.close()
    type_file.close()
    return parsed_time

"""
ЗДЕСЬ БУДЕМ ФОРМИРОВАТЬ 4 ФАЙЛА С ИНФОРМАЦИЕЙ о:
- вкусовых оценках образца в слепой дегустации
- оценках схожести напитка с оригинальной кока-колой 
- готовности платить за каждый из образцов колы в слепой дегустации
- оценках стоимости образца в слепой дегустации
"""
def WTP_price_taste(folder):

    path_vol = f'{folder}/DATA/'
    vol_nameS = os.listdir(path_vol)
    parsed_results = dict.fromkeys(vol_nameS)

    for vol_name in vol_nameS:
        path_to_volunteer_data = folder
        WTP_dict = {
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
        taste_dict = {
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
        price_dict = {
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
        sim_dict = {
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

        file1 = open(f'{path_to_volunteer_data}/DATA/{vol_name}/first.txt', 'r', encoding='utf-8')
        file1.readline()
        file_order = open(f'{path_to_volunteer_data}/DATA/{vol_name}/order.txt', 'r', encoding='utf-8')
        lines_about_order = file_order.readlines()

        # аналогично функции parsed_files, вводим множество для проверки это первая или вторая проба колы
        brand_check = set()

        for line in lines_about_order:

            current_cola = line.strip() # Strips the newline character
            if current_cola in brand_check:
                current_cola = current_cola + '2'
            else:
                brand_check.add(current_cola)
                current_cola = current_cola + '1'

            file1.readline()
            taste_dict[current_cola] = file1.readline().strip()
            file1.readline()
            sim_dict[current_cola] = file1.readline().strip()
            file1.readline()
            WTP_dict[current_cola] = file1.readline().strip().replace('|', '').strip()
            file1.readline()
            price_dict[current_cola] = file1.readline().strip().replace('|', '').strip()

        parsed_results[vol_name] = {
            'taste': taste_dict,
            'similarity': sim_dict,
            'WTP': WTP_dict,
            'price': price_dict
        }
        file1.close()
        file_order.close()

    return parsed_results


'''функция для экспорта данных по WTP, оценке вкуса и цены'''
def export_wtp_etc(folder, parsed_results):

    first_line = "NAME; cola1; cola2; cola_zero1; cola_zero2; d_cola1; d_cola2; d_zero1; d_zero2; funky1; funky2; chernogolovka1; chernogolovka2;\n"
    taste_file = open(f'{folder}/results/taste.csv', "w")
    sim_file = open(f'{folder}/results/similar.csv', "w")
    WTP_file = open(f'{folder}/results/WTP.csv', "w")
    price_file = open(f'{folder}/results/price.csv', "w")
    taste_file.write(first_line)
    sim_file.write(first_line)
    WTP_file.write(first_line)
    price_file.write(first_line)

    for name in parsed_results.keys():
        taste_dict = parsed_results[name]['taste']
        sim_dict = parsed_results[name]['similarity']
        WTP_dict = parsed_results[name]['WTP']
        price_dict = parsed_results[name]['price']

        line_taste = name
        line_sim = name
        line_WTP = name
        line_price = name

        for brand in taste_dict.keys():
            line_taste += ';' + taste_dict[brand]
            line_sim += ';' + sim_dict[brand]
            line_WTP += ';' + WTP_dict[brand]
            line_price += ';' + price_dict[brand]

        line_taste += '\n'
        line_sim += '\n'
        line_WTP += '\n'
        line_price += '\n'

        taste_file.write(line_taste)
        sim_file.write(line_sim)
        WTP_file.write(line_WTP)
        price_file.write(line_price)

    taste_file.close()
    sim_file.close()
    WTP_file.close()
    price_file.close()


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
        [sg.Submit('Построить график', key='-PLOT-', disabled=True)],
        [sg.Canvas(key='-CANVAS-')],
        [sg.Button('Добавить отрезок', key='-SEG-', disabled=True),
         sg.Button('Сохранить данные по волонтёру', key='-ADD-', disabled=True),
         sg.Button('Выгрузить таблицу', key='-FFT-', disabled=True),
         sg.Button('Выгрузить WTP etc', key='-ETC-', disabled=True)]
    ]

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
            with open(f'{folder}/data_about_volunteers.csv', encoding='windows-1251') as f:
                f.readline()
                for row in f:
                    row = row.strip().split(';')
                    final_data[row[0]] = row[1:]
            #ещё сразу спарсим информацию о WTP, оценке вкуса и цены. Если нужно, их можно выгрузить отдельно
            parsed_wtp_etc = WTP_price_taste(folder)
            window['-ETC-'].update(disabled=False)

        if event == '-VOL-':
            flag_timestamps = False
            path_time = f'{folder}/DATA/{values["-VOL-"]}/times.txt'
            path_type = f'{folder}/DATA/{values["-VOL-"]}/order.txt'
            path_answers = f'{folder}/DATA/{values["-VOL-"]}/first.txt'
            path_eeg = f'{folder}/DATA/{values["-VOL-"]}'
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
            for i in range(len(eeg_signals)):
                with open(f'{folder}/DATA/{values["-VOL-"]}/{eeg_signals[i]}') as f: # какой файл выбран
                    data[eeg_signals[i]].append( list([float(i.replace(',', '.')) * 1e-6 for i in list(csv.reader(f, delimiter=';'))[0]]))
                    eeg_signals[i] = f'{data[eeg_signals[i]][0]}, {data[eeg_signals[i]][1]}, {eeg_signals[i]}'
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

                if fig_agg is not None:
                    delete_fig_agg(fig_agg)

                fig = fig_maker_multi(window, data, a, b)
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
                    delete_fig_agg(fig_agg)
                d = data_for_one_plot[a:b]

                fig = fig_maker(window, d, a, b)
                fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                window.Refresh()
                window['-SEG-'].update(disabled=False)
                window['-ADD-'].update(disabled=False)
                window['-FFT-'].update(disabled=False)
            # нужен ли функционал, чтобы можно было потом выбрать, по какому промежутку строим?

        if event == '-SEG-':
            type = values['-TIME-'].split(': ')[1].strip()
            start = float(values['-START-'].replace(',', '.'))
            finish = start + float(values['-LEN-'].replace(',', '.'))
            line_eeg = []
            for v in data.values():
                freqs = [str(i).replace('.', ',') for i in calc_fft(v[-1], start, finish)] #v[-1] - это данные сигнала
                line_eeg.extend(freqs[:2])
            pre_data[type].extend(line_eeg)

        if event == '-ADD-':
            volunteer = values['-VOL-']
            print(volunteer)
            for k in final_data.keys():
                if final_data[k][0] == volunteer:
                    final_data[k].append(pre_data)
                    break
            sg.popup("Данные сохранены")
            for k, v in final_data.items():
                print(k, v)

        if event == '-FFT-':
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
                    for brand, fft_results in values[-1].items():

                        print(';'.join([id, values[1], values[2], brand, parsed_wtp_etc[name]['taste'][brand],
                                        parsed_wtp_etc[name]['similarity'][brand], parsed_wtp_etc[name]['WTP'][brand],
                                        parsed_wtp_etc[name]['price'][brand]] + fft_results))
                        print(';'.join([id, values[1], values[2], brand, parsed_wtp_etc[name]['taste'][brand],
                                        parsed_wtp_etc[name]['similarity'][brand], parsed_wtp_etc[name]['WTP'][brand],
                                        parsed_wtp_etc[name]['price'][brand]] + fft_results), file=csv_result)

            sg.popup("Файл сохранён в папку")
        if event == '-ETC-':
            export_wtp_etc(folder, parsed_wtp_etc)
            sg.popup("Файл сохранён в папку results")
    window.close()

