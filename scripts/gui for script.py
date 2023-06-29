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
def fig_maker(window, data, time_start=8.6, time_finish=9.6):  # this should be called as a thread, then time.sleep() here would not freeze the GUI
   global RATE
   t = np.arange(time_start/RATE, time_finish/RATE, 1 / RATE)
   fig = mplt.figure.Figure(figsize=(8, 4), dpi=100)
   ax = fig.add_subplot(1, 1, 1)
   ax.plot(t, data)
   ax.set_xlabel("Время, сек")
   ax.set_ylabel("Амплитуда, миллиВольты")
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
- готовности платить за каждый из образцов шоколада в слепой дегустации
- оценках стоймости образца в слепой дегустации
- вкусовых оценках образца в слепой дегустации
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
    with open(f'{folder}/results/WTP.csv', "w") as text_file:
        text_file.write(first_line)
    with open(f'{folder}/results/price.csv', "w") as text_file:
        text_file.write(first_line)
    vol_nameS = os.listdir(path_vol)
    for vol_name in vol_nameS:

        path_to_volunteer_data = folder

        WTP_array = [vol_name, 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA']
        Taste_array = [vol_name, 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA']
        Price_array = [vol_name, 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA']
        line_WTP = ''
        line_Taste = ''
        line_Price = ''

        file1 = open(f'{path_to_volunteer_data}/DATA/{vol_name}/first.txt', 'r', encoding='utf-8')

        file_order = open(f'{path_to_volunteer_data}/DATA/{vol_name}/order.txt', 'r', encoding='utf-8')
        Lines_about_order = file_order.readlines()

        # Strips the newline character
        for line in Lines_about_order:
            current_cola = line.strip()
            if WTP_array[string_structure[current_cola][0]] == 'NA':
                file1.readline()
                Taste_array[string_structure[current_cola][0]] = (file1.readline()[:-1])
                file1.readline()
                WTP_array[string_structure[current_cola][0]] = (file1.readline()[:-2])
                file1.readline()
                Price_array[string_structure[current_cola][0]] = (file1.readline()[:-2])
            else:
                file1.readline()
                Taste_array[string_structure[current_cola][1]] = (file1.readline()[:-1])
                file1.readline()
                WTP_array[string_structure[current_cola][1]] = (file1.readline()[:-2])
                file1.readline()
                Price_array[string_structure[current_cola][1]] = (file1.readline()[:-2])

        file1.close()
        file_order.close()

        for count in range(13):
            line_WTP = line_WTP + WTP_array[count] + ';'
            line_Taste = line_Taste + Taste_array[count] + ';'
            line_Price = line_Price + Price_array[count] + ';'

        line_WTP = line_WTP + '\n'
        line_Taste = line_Taste + '\n'
        line_Price = line_Price + '\n'

        with open(f'{folder}/results/taste.csv', "a") as text_file:
            text_file.write(line_Taste)

        with open(f'{folder}/results/WTP.csv', "a") as text_file:
            text_file.write(line_WTP)

        with open(f'{folder}/results/price.csv', "a") as text_file:
            text_file.write(line_Price)


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
            #print(type(os.listdir(path_vol)))
            window['-VOL-'].update(disabled=False, values=os.listdir(path_vol))
            window['-ETC-'].update(disabled=False)

        if event == '-VOL-':
            path_time = f'{folder}/DATA/{values["-VOL-"]}/times.txt'
            path_type = f'{folder}/DATA/{values["-VOL-"]}/order.txt'
            path_answers = f'{folder}/DATA/{values["-VOL-"]}/first.txt'
            path_eeg = f'{folder}/DATA/{values["-VOL-"]}'
            pattern = "EEG*"
            listOfFiles = os.listdir(path_eeg)
            #здесь можно ещё добавить пояснение, что это за сигнал, откуда
            #так работает быстрее - мы не загружаем сразу все данные,
            eeg_signals = [file for file in listOfFiles if fnmatch.fnmatch(file, pattern)]
            window['-ELEC-'].update(disabled=False, values=eeg_signals)

        if event == '-ELEC-':
            chosen_electrode = values['-ELEC-']
            dict_times = parse_files(path_time,path_type,path_answers)
            timestamps = [f'{str(k)} : {"; ".join(v)}' for k, v in dict_times.items()]
            window['-TIME-'].update(disabled=False, values=timestamps)

        if event == '-TIME-':
            stamp = float(values['-TIME-'].split(':')[0])
            #print(stamp)
            window['-START-'].update(disabled=False, value=stamp)
            length = len(dict_times.keys())
            window['-LEN-'].update(disabled=False, value=length)
            window['-PLOT-'].update(disabled=False)
        if event == '-PLOT-':
            f = open(f'{folder}/DATA/{values["-VOL-"]}/{values["-ELEC-"]}')  # какой файл выбран
            data = list([float(i.replace(',', '.')) * 1e-6 for i in list(csv.reader(f, delimiter=';'))[0]]) #данные ЭЭГ с конкретного электрода
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
            d = data[a:b]

            fig = fig_maker(window, d, a, b)
            fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
            window.Refresh()
            window['-ADD-'].update(disabled=False)
            window['-FFT-'].update(disabled=False)
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

