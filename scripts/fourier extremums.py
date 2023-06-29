import numpy as np
from scipy.fft import rfft, rfftfreq, fft, fftfreq #FFT = Fast Fourier Transform
import csv
import matplotlib.pyplot as plt

RATE = 500 #частота в 1 с
'''считываем данные о времени'''
timeline = []
with open(r'C:\Users\Анна\Desktop\ВШЭ\ВШЭ\ВШЭ\данные с эксперимента\CSV_Export\DATA\Усанин\first.txt', newline='') as u:
    time = csv.reader(u, delimiter=' ')
    for row in time:
        t = float(row[1])

        timeline.append(int(t * RATE))

'''создаём массив с данными с каждого электрода
данные по каждому электроду порезаны на кусочки по временным меткам'''
eeg = []
for i in range(0, 21):
        with open(f'EEG_{i}.csv', newline='') as f:
            #при считывании данные переводим из наноВольт в миллиВольты(1е-06)
            #разлепляем их по ";", заменяем "," на ".", чтобы корректно перевести в формат рациональных чисел
            data = list([float(i.replace(',', '.')) * 1e-6 for i in list(csv.reader(f, delimiter=';'))[0]])
            slice_data = [data[:timeline[0]]]
            for i in range(1, len(timeline)):
                slice_data.append(data[timeline[i-1]:timeline[i]])
            eeg.append(slice_data)

'''создадим двумерный массив, в котором будем считать максимальные мощности на каждом 
сигнале с электрода на каждом временном кусочке'''
extremums = []
for i in range(len(eeg)):
    max_row = []
    for j in range(len(timeline)):
        y = fft(eeg[i][j])
        m = max(np.abs(y))
        max_row.append(m) #берем np.abs() потому, что значения – комплексные числа.
    extremums.append(max_row)

x = [i/RATE for i in timeline]
print(x)
y = extremums[0]
plt.plot(x, y)
plt.grid()
plt.show()