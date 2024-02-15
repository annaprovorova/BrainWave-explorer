import os

import numpy as np
from scipy.fft import rfft, rfftfreq
from parse import time_range

import matplotlib.pyplot as plt

import mne
from mne.preprocessing import ICA

'''
FFT - быстрое дискретное преобразование Фурье. 
В данном файле содержатся функции, позволяющие применить его к данным эксперимента.
Также здесь мы избавляемся от артефактов моргания с помощью ICA, применённого к данным ЭЭГ
'''

def calc_fft(data, RATE, time_start, time_finish):
    '''
    функция для расчёта FFT и разделения его по диапазонам частот
    :param data: list, один сигнал ЭЭГ
    :param RATE: int, частота 500 Гц
    :param time_start: float время начала расчёта
    :param time_finish: float время окончания расчёта
    :return: [agr_alpha, agr_beta] суммарная мощность сигнала по альфа и бета частотам
    '''
    data = data[time_start*RATE: time_finish*RATE+1]
    print(time_start, time_finish)
    yf = np.abs(rfft(data))**2
    time_for_axes = np.arange(time_start, time_finish, 1/RATE)
    xf = rfftfreq(len(time_for_axes), 1/RATE)
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
    return [str(agr_alpha), str(agr_beta), str(agr_gamma), str(agr_delta), str(agr_teta)]


def ica_preproc_first_5_sec(path, RATE):
    '''
    :param path: str, путь к папке с данными
    :return: data: dict, словарь, ключ - фамилия волонтёра, значение - словарь по типам кока-колы
    '''
    path_vol = fr'{path}\DATA'
    data = {}
    cola_types = {}
    cola_times = {}
    for vol in os.listdir(path_vol):
        path_time = fr'{path}\DATA\{vol}\times.txt'
        path_type = f'{path}\DATA\{vol}\order.txt'
        cola_times = time_range(path_time,  type='close', path_type=path_type)
        cola_types = {}
        raw = mne.io.read_raw_edf(fr"{path_vol}\{vol}\{vol}.edf", preload=True)
        raw.apply_function(lambda x: x * 1e-6) #переводим в милливольты
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
        filt_raw = raw.copy().filter(l_freq=1.0, h_freq=None) #Рекомендуется использовать фильтр низких частот с частотой больше 1 Гц.
                                                              #для удаления низкочастотных дрейфов, которые могут негативно повлиять на качество подбора ICA.

        cola_times = dict(sorted(cola_times.items()))
        for cola in cola_times:
            sec = filt_raw.copy()

            sec.crop(tmin=cola_times[cola][0], tmax=cola_times[cola][1])
            ica = ICA(n_components=5, max_iter="auto", random_state=97)
            ica.fit(sec)
            explained_var_ratio = ica.get_explained_variance_ratio(
                sec, components=[0, 1, 2], ch_type="eeg"
            )
            num_component = explained_var_ratio[max(explained_var_ratio)]
            ica.apply(sec, exclude=[num_component])

            cola_types[cola] = []

            ch_exp = {} # словарь для значений, разложенных в ряд Фурье
            time_start = 2
            time_finish = 3
            for ch_name, channel in zip(ch_names, sec.get_data()):

                tmp = calc_fft(channel, RATE, time_start=time_start, time_finish=time_finish)
                ch_exp[ch_name[4:] + '_a_1'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_1'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_1'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+1, time_finish=time_finish+1)
                ch_exp[ch_name[4:] + '_a_2'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_2'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_2'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+2, time_finish=time_finish+2)
                ch_exp[ch_name[4:] + '_a_3'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_3'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_3'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+3, time_finish=time_finish+3)
                ch_exp[ch_name[4:] + '_a_4'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_4'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_4'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+4, time_finish=time_finish+4)
                ch_exp[ch_name[4:] + '_a_5'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_5'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_5'] = tmp[2]
            ch_ = dict(sorted(ch_exp.items()))
            print(ch_exp)
            cola_types[cola] = ';'.join(ch_exp.values()).replace('.', ',')
        data[vol] = cola_types
    return data


def ica_preproc_last_5_sec(path, RATE):
    '''
    :param path: str, путь к папке с данными
    :return: data: dict, словарь, ключ - фамилия волонтёра, значение - словарь по типам кока-колы
    '''
    path_vol = fr'{path}\DATA'
    data = {}
    cola_types = {}
    cola_times = {}
    file_extract = open('for_images_filtred.csv', 'w', encoding='UTF-8')
    for vol in os.listdir(path_vol):
        path_time = fr'{path}\DATA\{vol}\times.txt'
        path_type = f'{path}\DATA\{vol}\order.txt'
        cola_times = time_range(path_time, type='close', path_type=path_type)
        cola_types = {}
        raw = mne.io.read_raw_edf(fr"{path_vol}\{vol}\{vol}.edf", preload=True)
        raw.apply_function(lambda x: x * 1e-6) #переводим в милливольты
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
        filt_raw = raw.copy().filter(l_freq=1.0, h_freq=None) #Рекомендуется использовать фильтр низких частот с частотой больше 1 Гц.
                                                              #для удаления низкочастотных дрейфов, которые могут негативно повлиять на качество подбора ICA.

        cola_times = dict(sorted(cola_times.items()))
        for cola in cola_times:
            sec = filt_raw.copy()

            sec.crop(tmin=cola_times[cola][0], tmax=cola_times[cola][1])
            ica = ICA(n_components=5, max_iter="auto", random_state=97)
            ica.fit(sec)
            # explained_var_ratio = ica.get_explained_variance_ratio(
            #     sec, components=[0, 1, 2], ch_type="eeg"
            # )
            # num_component = explained_var_ratio[max(explained_var_ratio)]
            ica.apply(sec, exclude=[0]) #num_component

            cola_types[cola] = []

            ch_exp = {}

            # выбор отрезков, по которым считаем FFT
            # пока без обобщения, у меня считается просто с -10 по -5
            n_sec = sec.get_data().shape[1] // RATE
            # time_start = n_sec - 10
            # time_finish = n_sec - 5
            time_start = n_sec - (n_sec // 3)
            time_finish = time_start + 5
            if time_finish > n_sec:
                time_start = n_sec - 5
                time_finish = n_sec

            # print(sec.get_data().shape, cola_times)
            # print(n_sec, time_start, time_finish)
            for ch_name, channel in zip(ch_names, sec.get_data()):
                # print(f'{vol};{cola};{ch_name};{";".join(map(str, list(channel)))}', file=file_extract)
                # print(channel.shape)
                tmp = calc_fft(channel, RATE, time_start=time_start, time_finish=time_finish)
                ch_exp[ch_name[4:] + '_a_1'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_1'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_1'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+1, time_finish=time_finish+1)
                ch_exp[ch_name[4:] + '_a_2'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_2'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_2'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+2, time_finish=time_finish+2)
                ch_exp[ch_name[4:] + '_a_3'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_3'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_3'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+3, time_finish=time_finish+3)
                ch_exp[ch_name[4:] + '_a_4'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_4'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_4'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+4, time_finish=time_finish+4)
                ch_exp[ch_name[4:] + '_a_5'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_5'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_5'] = tmp[2]
            ch_exp = dict(sorted(ch_exp.items())) # сортировка нужна для того, чтобы данные шли по каналам по секундам внутри канала
            cola_types[cola] = ';'.join(ch_exp.values()).replace('.', ',')
        data[vol] = cola_types
        # break
    file_extract.close()
    return data


def no_ica_last_5_sec(path, RATE):
    '''
    функция считает разложение на альфа и бета волны без применения ICA
    :param path: str, путь к папке с данными
    :return: data: dict, словарь, ключ - фамилия волонтёра, значение - словарь по типам кока-колы
    '''
    path_vol = fr'{path}\DATA'
    data = {}
    cola_types = {}
    cola_times = {}
    file_extract = open('for_images.csv', 'w', encoding='UTF-8')
    for vol in os.listdir(path_vol):
        path_time = fr'{path}\DATA\{vol}\times.txt'
        path_type = f'{path}\DATA\{vol}\order.txt'
        cola_times = time_range(path_time, type='close', path_type=path_type)
        cola_types = {}
        raw = mne.io.read_raw_edf(fr"{path_vol}\{vol}\{vol}.edf", preload=True)
        raw.apply_function(lambda x: x * 1e-6) #переводим в милливольты
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

        cola_times = dict(sorted(cola_times.items()))
        for cola in cola_times:
            sec = raw.copy()

            sec.crop(tmin=cola_times[cola][0], tmax=cola_times[cola][1])
            cola_types[cola] = []

            ch_exp = {}

            # выбор отрезков, по которым считаем FFT
            # пока без обобщения, у меня считается просто с -10 по -5
            n_sec = sec.get_data().shape[1]// RATE
            # time_start = n_sec - 5 # ВОТ ТУТ ИЗМЕНИЛА ВРЕМЯ, БЕРЁМ ПОСЛЕДНИЕ 5 СЕКУНД!!!
            # time_finish = n_sec
            time_start = n_sec -(n_sec // 3)
            time_finish = time_start + 5
            if time_finish > n_sec:
                time_start = n_sec - 5
                time_finish = n_sec
            print(cola_times[cola][0], cola_times[cola][1], time_start, time_finish, n_sec)
            # print(sec.get_data().shape, cola_times)
            # print(n_sec, time_start, time_finish)
            print(f'ИМЯ:{vol}, начало:{cola_times[cola][0]}, конец: {cola_times[cola][1]}, длина: {n_sec}, сек расчёта: {time_start}, cola: {cola}')
            for ch_name, channel in zip(ch_names, sec.get_data()):
                # print(type(channel))
                # print(f'{vol};{cola};{ch_name};{";".join(map(str, list(channel)))}', file=file_extract)
                tmp = calc_fft(channel, RATE, time_start=time_start, time_finish=time_finish)

                ch_exp[ch_name[4:] + '_a_1'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_1'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_1'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+1, time_finish=time_finish+1)
                ch_exp[ch_name[4:] + '_a_2'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_2'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_2'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+2, time_finish=time_finish+2)
                ch_exp[ch_name[4:] + '_a_3'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_3'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_3'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+3, time_finish=time_finish+3)
                ch_exp[ch_name[4:] + '_a_4'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_4'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_4'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+4, time_finish=time_finish+4)
                ch_exp[ch_name[4:] + '_a_5'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_5'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_5'] = tmp[2]

            ch_exp = dict(sorted(ch_exp.items()))
            cola_types[cola] = ';'.join(ch_exp.values()).replace('.', ',')
        data[vol] = cola_types
        # break
    file_extract.close()
    return data


def ica_preproc_open_5_sec(path, RATE, order=[]):
    '''
    Функция для выгрузки отчёта по эксперименту в открытую, берём с -6 по -1 секунды перед сигналом о завершении ответов на вопросы
    :param path: str, путь к папке с данными
    :return: data: dict, словарь, ключ - фамилия волонтёра, значение - словарь по типам кока-колы
    '''
    path_vol = fr'{path}\DATA'
    data = {}
    cola_types = {}
    cola_times = {}
    for vol in os.listdir(path_vol):
        print(vol)
        path_time = fr'{path}\DATA\{vol}\times.txt'
        # path_type = f'{path}\DATA\{vol}\order.txt'
        cola_times = time_range(path_time, type='open', order=order)
        print(cola_times)
        cola_types = {}
        raw = mne.io.read_raw_edf(fr"{path_vol}\{vol}\{vol}.edf", preload=True)
        raw.apply_function(lambda x: x * 1e-6) #переводим в милливольты
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
        filt_raw = raw.copy().filter(l_freq=1.0, h_freq=None) #Рекомендуется использовать фильтр низких частот с частотой больше 1 Гц.
                                                              #для удаления низкочастотных дрейфов, которые могут негативно повлиять на качество подбора ICA.

        cola_times = dict(sorted(cola_times.items()))
        for cola in cola_times:
            sec = filt_raw.copy()

            sec.crop(tmin=cola_times[cola][0], tmax=cola_times[cola][1])
            ica = ICA(n_components=5, max_iter="auto", random_state=97)
            ica.fit(sec)
            explained_var_ratio = ica.get_explained_variance_ratio(
                sec, components=[0, 1, 2], ch_type="eeg"
            )
            num_component = explained_var_ratio[max(explained_var_ratio)]
            ica.apply(sec, exclude=[num_component])

            cola_types[cola] = []

            ch_exp = {}

            # выбор отрезков, по которым считаем FFT
            # пока без обобщения, у меня считается просто с -10 по -5
            n_sec = sec.get_data().shape[1]// RATE
            time_start = n_sec - 10
            time_finish = n_sec - 5
            # print(sec.get_data().shape, cola_times)
            # print(n_sec, time_start, time_finish)
            for ch_name, channel in zip(ch_names, sec.get_data()):
                # print(channel.shape)
                tmp = calc_fft(channel, RATE, time_start=time_start, time_finish=time_finish)
                ch_exp[ch_name[4:] + '_a_1'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_1'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_1'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+1, time_finish=time_finish+1)
                ch_exp[ch_name[4:] + '_a_2'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_2'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_2'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+2, time_finish=time_finish+2)
                ch_exp[ch_name[4:] + '_a_3'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_3'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_3'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+3, time_finish=time_finish+3)
                ch_exp[ch_name[4:] + '_a_4'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_4'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_4'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+4, time_finish=time_finish+4)
                ch_exp[ch_name[4:] + '_a_5'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_5'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_5'] = tmp[2]
            ch_exp = dict(sorted(ch_exp.items()))
            cola_types[cola] = ';'.join(ch_exp.values()).replace('.', ',')
        data[vol] = cola_types
    return data


def no_ica_open_5_sec(path, RATE, order=[]):
    '''
    Функция для выгрузки отчёта по эксперименту в открытую, берём с -6 по -1 секунды перед сигналом о завершении ответов на вопросы
    БЕЗ ICA преобразования
    :param path: str, путь к папке с данными
    :return: data: dict, словарь, ключ - фамилия волонтёра, значение - словарь по типам кока-колы
    '''
    path_vol = fr'{path}\DATA'
    data = {}
    cola_types = {}
    cola_times = {}
    for vol in os.listdir(path_vol):
        print(vol)
        path_time = fr'{path}\DATA\{vol}\times.txt'
        # path_type = f'{path}\DATA\{vol}\order.txt'
        print(vol)
        cola_times = time_range(path_time, type='open', order=order)
        print(cola_times)
        cola_types = {}
        raw = mne.io.read_raw_edf(fr"{path_vol}\{vol}\{vol}.edf", preload=True)
        raw.apply_function(lambda x: x * 1e-6) #переводим в милливольты
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

        cola_times = dict(sorted(cola_times.items()))
        for cola in cola_times:
            sec = raw.copy()

            sec.crop(tmin=cola_times[cola][0], tmax=cola_times[cola][1])
            cola_types[cola] = []

            ch_exp = {}

            # выбор отрезков, по которым считаем FFT
            # пока без обобщения, у меня считается просто с -6 по -1
            n_sec = sec.get_data().shape[1]// RATE
            time_start = n_sec - 10
            time_finish = n_sec - 5
            # print(sec.get_data().shape, cola_times)
            # print(n_sec, time_start, time_finish)
            for ch_name, channel in zip(ch_names, sec.get_data()):
                # print(channel.shape)
                tmp = calc_fft(channel, RATE, time_start=time_start, time_finish=time_finish)
                ch_exp[ch_name[4:] + '_a_1'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_1'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_1'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+1, time_finish=time_finish+1)
                ch_exp[ch_name[4:] + '_a_2'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_2'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_2'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+2, time_finish=time_finish+2)
                ch_exp[ch_name[4:] + '_a_3'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_3'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_3'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+3, time_finish=time_finish+3)
                ch_exp[ch_name[4:] + '_a_4'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_4'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_4'] = tmp[2]
                tmp = calc_fft(channel, RATE, time_start=time_start+4, time_finish=time_finish+4)
                ch_exp[ch_name[4:] + '_a_5'] = tmp[0]
                ch_exp[ch_name[4:] + '_b_5'] = tmp[1]
                ch_exp[ch_name[4:] + '_g_5'] = tmp[2]
            ch_exp = dict(sorted(ch_exp.items()))
            cola_types[cola] = ';'.join(ch_exp.values()).replace('.', ',')
        data[vol] = cola_types
    return data


if __name__ == "__main__":
    #приделать progress bar в своё удовольствие

    # progressbar = [
    #     [sg.ProgressBar(len(mylist), orientation='h', size=(51, 10), key='progressbar')]
    # ]
    # outputwin = [
    #     [sg.Output(size=(78, 20))]
    # ]
    #
    # layout = [
    #     [sg.Frame('Progress', layout=progressbar)],
    #     [sg.Frame('Output', layout=outputwin)],
    #     [sg.Submit('Start'), sg.Cancel()]
    # ]
    #
    # window = sg.Window('Custom Progress Meter', layout)
    # progress_bar = window['progressbar']
    #
    # while True:
    #     event, values = window.read(timeout=10)
    #     if event == 'Cancel' or event is None:
    #         break
    #     elif event == 'Start':
    #         for i, item in enumerate(mylist):
    #             print(item)
    #             time.sleep(1)
    #             progress_bar.UpdateBar(i + 1)
    #
    # window.close()

    order = ['cola',
                  'chernogolovka',
                  'cola_zero',
                  'd_cola',
                  'd_zero',
                  'funky']

    # d = ica_preproc_last_5_sec(r'C:\Users\Анна\Desktop\EEG_Analysis\COCA COLA', 500)
    # print(d)

    ica_preproc_last_5_sec(r'C:\Users\Анна\Desktop\EEG_Analysis\Coca Cola\DASHA', 500)
    # d_open = ica_preproc_last_5_sec(r'C:\Users\Анна\Desktop\EEG_Analysis\CC Masha\Experiment — копия', 500)
    # print(d_open)

    # raw = mne.io.read_raw_edf(fr"C:\Users\Анна\Desktop\EEG_Analysis\COCA COLA\DATA\Быкова\Быкова.edf", preload=True)
    # raw.apply_function(lambda x: x * 1e-6)  # переводим в милливольты
    # ch_names = ['EEG Fp1',
    #             'EEG Fp2',
    #             'EEG F3',
    #             'EEG F4',
    #             'EEG P3',
    #             'EEG P4',
    #             'EEG O1',
    #             'EEG O2',
    #             ]
    # raw.pick(ch_names)
    # raw1 = raw.copy()
    # raw.crop(tmin=39.0, tmax=73.0)
    # raw1.crop(tmin=39.0, tmax=42.0)
    # data = raw.get_data()[0]
    # data1 = raw1.get_data()[0]
    # # plt.plot(data)
    #
    # a, b = calc_fft(data, 500, time_start= 1, time_finish=2)
    # a2, b2 = calc_fft(data, 500, time_start= 2, time_finish=3)
    # print(a, a2, b, b2)
    # plt.plot(data1, color='darkorange')
    # plt.show()