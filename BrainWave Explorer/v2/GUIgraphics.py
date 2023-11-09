import numpy as np
import matplotlib as mplt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

'''
в этом файле содержатся функции для отрисовки графиков на интерфейсе приложения
'''


'''функция для обновления графика'''
def fig_maker(window, RATE, data_one_channel, time_start=8.6, time_finish=9.6):  # this should be called as a thread, then time.sleep() here would not freeze the GUI
   t = np.arange(time_start/RATE, time_finish/RATE, 1 / RATE)
   fig = mplt.figure.Figure(figsize=(8, 4), dpi=100)
   ax = fig.add_subplot(1, 1, 1)
   ax.plot(t, data_one_channel)
   ax.set_xlabel("Время, сек")
   ax.set_ylabel("Амплитуда, миллиВольты")
   window.write_event_value('-THREAD-', 'done.')
   time.sleep(1)
   return fig

def fig_maker_multi(window, RATE, data, time_start=8, time_finish=9):  # this should be called as a thread, then time.sleep() here would not freeze the GUI
   t = np.arange(time_start / RATE, time_finish / RATE, 1 / RATE)

   fig = mplt.figure.Figure(figsize=(8, 4), dpi=100)
   gs = fig.add_gridspec(8, hspace=0)
   axs = gs.subplots(sharex=True, sharey=True)
   i = 0
   print(data)
   for v in data.values():
       print(type(v[-1]), v[-1], time_start, time_finish)
       axs[i].plot(t, v[-1][int(time_start):int(time_finish)])
       axs[i].set_ylabel(v[0],  rotation=0, fontweight='bold', color='orange')
       axs[i].label_outer()    # Hide x labels and tick labels for all but bottom plot
       i += 1


   window.write_event_value('-THREAD-', 'done.')
   time.sleep(1)
   return fig

def fig_maker_multi_ica(window, RATE, data, time_start=8, time_finish=9):  # this should be called as a thread, then time.sleep() here would not freeze the GUI
   '''
   функция, для отрисовки сразу двух графиков: самого сигнала и сигнала после ica
   :param window:
   :param RATE: 500, количество считываний в секунду
   :param data: dict, в нём -1 значение - сгнал после ica, -2 - сам сигнал
   :param time_start: int - время начала временной шкалы
   :param time_finish: int - точка окнчания временной шкалы
   :return: None
   '''
   t = np.arange(time_start / RATE, time_finish / RATE, 1 / RATE)

   fig = mplt.figure.Figure(figsize=(8, 4), dpi=100)
   gs = fig.add_gridspec(8, hspace=0)
   axs = gs.subplots(sharex=True, sharey=True)
   i = 0
   for k, v in data.items():
       axs[i].plot(t, v[-2][int(time_start):int(time_finish)])
       axs[i].plot(t, v[-1][:-1], color='darkorange')
       axs[i].set_ylabel(k[4:],  rotation=0, fontweight='bold', color='orange')
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
