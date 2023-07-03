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
    print(time_start, time_finish)
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
def parse_files(path_time, path_type, path_answers):
    parsed_time = dict() #словарь, в котором ключами будут метки времени, а значениями то, что происходит
    time_file = open(path_time, encoding="utf-8")
    ans_file = open(path_answers, encoding="utf-8")
    type_file = open(path_type, encoding="utf-8")
    #    parsed_time = {float(row): [] for row in time_file}
    parsed_time[float(time_file.readline().split()[1])] = ['начало эксперимента']
    for i in range(12):
        parsed_time[float(time_file.readline().split()[1])] = ['проба', type_file.readline()]
        parsed_time[float(time_file.readline().split()[1])] = ['сигнал перед питьём воды']
    for i in range(6):
        parsed_time[float(time_file.readline().split()[1])] = ['просмотр изображения']
        parsed_time[float(time_file.readline().split()[1])] = ['первый глоток']
        parsed_time[float(time_file.readline().split()[1])] = ['сигнал перед питьём воды']
    return parsed_time

"""
ЗДЕСЬ БУДЕМ ФОРМИРОВАТЬ 3 ФАЙЛА С ИНФОРМАЦИЕЙ о:
- вкусовых оценках образца в слепой дегустации
- оценках схожести напитка с оригинальной кока-колой 
- готовности платить за каждый из образцов колы в слепой дегустации
- оценках стоимости образца в слепой дегустации
"""
def WTP_price_taste(folder):
    string_structure = {
        "cola": [1, 2],
        "cola_zero": [3, 4],
        "d_cola": [5, 6],
        "d_zero": [7, 8],
        "funky": [9, 10],
        "chernogolovka": [11, 12]
    }

    first_line = "NAME; cola1; cola2; cola_zero1; cola_zero2; d_cola1; d_cola2; d_zero1; d_zero2; funky1; funky2; chernogolovka1; chernogolovka2\n"
    with open(f'{folder}/results/taste.csv', "w") as text_file:
        text_file.write(first_line)
    with open(f'{folder}/results/similar.csv', "w") as text_file:
        text_file.write(first_line)
    with open(f'{folder}/results/WTP.csv', "w") as text_file:
        text_file.write(first_line)
    with open(f'{folder}/results/price.csv', "w") as text_file:
        text_file.write(first_line)
    vol_nameS = os.listdir(path_vol)
    for vol_name in vol_nameS:
        path_to_volunteer_data = folder
        WTP_array = [vol_name, 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA']
        taste_array  = [vol_name, 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA']
        price_array = [vol_name, 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA']
        sim_array = [vol_name, 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA']

        file1 = open(f'{path_to_volunteer_data}/DATA/{vol_name}/first.txt', 'r', encoding='utf-8')
        file1.readline()
        file_order = open(f'{path_to_volunteer_data}/DATA/{vol_name}/order.txt', 'r', encoding='utf-8')
        lines_about_order = file_order.readlines()

        for line in lines_about_order:
            current_cola = line.strip() # Strips the newline character
            if WTP_array[string_structure[current_cola][0]] == 'NA':
                file1.readline()
                taste_array [string_structure[current_cola][0]] = file1.readline().strip()
                file1.readline()
                sim_array [string_structure[current_cola][0]] = file1.readline().strip()
                file1.readline()
                WTP_array[string_structure[current_cola][0]] = file1.readline().replace('|', '').strip()
                file1.readline()
                price_array[string_structure[current_cola][0]] = file1.readline().replace('|', '').strip()
            else:
                file1.readline()
                taste_array [string_structure[current_cola][1]] = file1.readline().strip()
                file1.readline()
                sim_array [string_structure[current_cola][1]] = file1.readline().strip()
                file1.readline()
                WTP_array[string_structure[current_cola][1]] = file1.readline().replace('|', '').strip()
                file1.readline()
                price_array[string_structure[current_cola][1]] = file1.readline().replace('|', '').strip()

        file1.close()
        file_order.close()


        line_WTP = ';'.join(WTP_array) +  '\n'
        line_taste = ';'.join(taste_array) +  '\n'
        line_price = ';'.join(price_array) +  '\n'
        line_sim = ';'.join(sim_array) +  '\n'

        with open(f'{folder}/results/taste.csv', "a") as text_file:
            text_file.write(line_taste)

        with open(f'{folder}/results/similar.csv', "a") as text_file:
            text_file.write(line_sim)

        with open(f'{folder}/results/WTP.csv', "a") as text_file:
            text_file.write(line_WTP)

        with open(f'{folder}/results/price.csv', "a") as text_file:
            text_file.write(line_price)


'''функция для экспорта данных по WTP, оценке вкуса и цены'''
def export_wtp_etc(folder, WTP_array, taste_array, price_array):
    for count in range(13):
        line_WTP = line_WTP + WTP_array[count] + ';'
        line_taste = line_taste + taste_array[count] + ';'
        line_price = line_price + price_array[count] + ';'

    line_WTP = line_WTP + '\n'
    line_taste = line_taste + '\n'
    line_price = line_price + '\n'

    with open(f'{folder}/results/taste.csv', "a") as text_file:
        text_file.write(line_taste)

    with open(f'{folder}/results/WTP.csv', "a") as text_file:
        text_file.write(line_WTP)

    with open(f'{folder}/results/price.csv', "a") as text_file:
        text_file.write(line_price)


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
    final_data = []
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
        [sg.Button('Добавить отрезок для анализа', key='-ADD-', disabled=True), sg.Button('Рассчитать БПФ', key='-FFT-', disabled=True), sg.Button('Выгрузить ключевые показатели', key='-ETC-', disabled=True)]
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
            dict_times = parse_files(path_time, path_type, path_answers)
            timestamps = [f'{str(k)} : {"; ".join(v)}' for k, v in dict_times.items()]
            window['-TIME-'].update(disabled=False, values=timestamps)

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
            length = len(dict_times.keys())
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
                #!!!!!!
                #d = data[a:b]

                fig = fig_maker_multi(window, data, a, b)
                fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                window.Refresh()
                window['-ADD-'].update(disabled=False)
                window['-FFT-'].update(disabled=False)

            else:
                file_csv = values["-ELEC-"].split(', ')[-1]
                data_for_one_plot = data[file_csv][-1]

                m = values['-TIME-']
                print(f)
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
                # window['-ADD-'].update(disabled=False)
                # window['-FFT-'].update(disabled=False)
            # нужен ли функционал, чтобы можно было потом выбрать, по какому промежутку строим?
        if event == '-ADD-': # может быть, убрать эту кнопку? сразу считать БПФ и писать в файл??
            final_data.append([values["-ELEC-"], values['-TIME-'], str(a / RATE).replace('.', ','), str(b / RATE).replace('.', ','), d])
            sg.popup("Данные сохранены")
            print(len(d))  # debug


        if event == '-FFT-':
            path_result=f'{folder}/results/'
            with open(
                    f'{path_result}/result {time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year} {time.localtime().tm_hour}-{time.localtime().tm_min}.csv',
                    'w', newline='') as csv_result:
                res = csv.writer(csv_result, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                res.writerow(
                    ['Электрод', 'Номер метки', 'Время', 'Продолжительность', 'Альфа', 'Бета', 'Гамма', 'Дельта',
                     'Тета'])
                for row in final_data:
                    freqs = [str(i).replace('.', ',') for i in calc_fft(row[-1], float(row[-3].replace(',', '.')), float(row[-2].replace(',', '.')))]
                    res.writerow(row[:-1] + freqs)
                sg.popup("Файл сохранён в папку")
        if event == '-ETC-':
            WTP_price_taste(folder)
            sg.popup("Файл сохранён в папку results")
    window.close()

