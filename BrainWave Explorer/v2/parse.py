import os
import PySimpleGUI as sg

'''
в этом файле находятся функции для парсинга данных в единую отчётную таблицу по результатам эксперимента
'''

def parse_files(path_time, path_type, order=[]):
    '''
    функция для парсинга меток времени, вида продукта и ответов

    :param path_time: путь к файлу times.txt в котором содержатся 43 записи о ходе эксперимента. 26 записей о ходе эксперимента в слепую, 17 записей о ходе в закрытую.
                        ход эксперимента в закрытую: проба, ответ на вопросы. Мы берём метку после ответа на вопросы
                                                    Мы пропускаем первую строку, потому что это время на занесение фамилии
                                                    И пропускаем 26 строку, это глоток воды между экспериментом в открытую и экспериментом в закрытую
                        ход эксперимента в открытую: проба, ответ на вопросы, вода. Мы берём метку после ответа на вопросы
    :param path_type: путь к файлу order.txt. Это порядок пробы продуктов в эксперименте
    :return: parsed_time:dict словарь, в котором спаршены тип продукта и время. Ещё раз Время берём ПЕРЕД сигналом о том, что мы получили ответы на вопросы.
    '''
    parsed_time_closed = dict() #словарь, в котором ключами будут метки времени, а значениями то, что происходит ЗАКРЫТЫЙ ТЕСТ
    parsed_time_open = dict()  # словарь, в котором ключами будут метки времени, а значениями то, что происходит ОТКРЫТЫЙ ТЕСТ
    time_file = open(path_time, encoding="utf-8")
    type_file = open(path_type, encoding="utf-8")
    # в изначальном файлике все данные повторяются по 2 раза.
    # нам удобнее ввести уникальные значения, например, cola1 и cola2
    # поэтому мы заводим множество, с помощью которого будем проверять, встречался ли нам уже такой бренд
    brand_check = set()

    time_file.readline() #пропускаем строку в файле с началом эксперимента


    for i in range(12):
        label = float(time_file.readline().split()[-1])
        next_label = float(time_file.readline().split()[-1])
        cola_type = type_file.readline().strip()
        if cola_type in brand_check:
            parsed_time_closed[label] = [cola_type + '2', next_label-label]
        else:
            parsed_time_closed[label] = [cola_type + '1', next_label - label]
            brand_check.add(cola_type)

    time_file.readline()  # пропускаем строку в файле, питьё воды после закрытого эксперимента
    #теперь время для данных в открытую
    order = ['cola',
                      'chernogolovka',
                      'cola_zero',
                      'd_cola',
                      'd_zero',
                      'funky']
    for i in range(6):
        label = float(time_file.readline().split()[-1])
        next_label = float(time_file.readline().split()[-1])
        parsed_time_open[label] = [order[i], next_label-label]

    time_file.close()
    type_file.close()

    return parsed_time_closed, parsed_time_open

def parse_files_honey(path_time, path_type, order=[]):
    '''
    функция для парсинга меток времени, вида МЁДА и ответов

    :param path_time: путь к файлу times.txt в котором содержатся 51 запись о ходе эксперимента.24 записей о ходе эксперимента в слепую, 27 записей о ходе в закрытую.
                        ход эксперимента в закрытую: проба, ответ на вопросы. Мы берём метку после ответа на вопросы
                                                    Мы пропускаем первую строку, потому что это время на занесение фамилии
                                                    И пропускаем 26 строку, это глоток воды между экспериментом в открытую и экспериментом в закрытую
                        ход эксперимента в открытую: проба, ответ на вопросы, вода. Мы берём метку после ответа на вопросы
    :param path_type: путь к файлу order.txt. Это порядок пробы продуктов в эксперименте
    :return: parsed_time:dict словарь, в котором спаршены тип продукта и время. Ещё раз Время берём ПЕРЕД сигналом о том, что мы получили ответы на вопросы.
    '''
    parsed_time_closed = dict() #словарь, в котором ключами будут метки времени, а значениями то, что происходит ЗАКРЫТЫЙ ТЕСТ
    parsed_time_open = dict()  # словарь, в котором ключами будут метки времени, а значениями то, что происходит ОТКРЫТЫЙ ТЕСТ
    time_file = open(path_time, encoding="utf-8")
    type_file = open(path_type, encoding="utf-8")

    time_file.readline() #пропускаем строку в файле с началом эксперимента

    for i in range(7):
        label = float(time_file.readline().split()[-1])
        time_file.readline() # пропускаем метку окончания пробования
        next_label = float(time_file.readline().split()[-1])
        honey_type = type_file.readline().strip()
        parsed_time_closed[label] = [honey_type, next_label-label]

    time_file.readline()  # пропускаем строку в файле, питьё воды после закрытого эксперимента

    #теперь время для данных в открытую

    for i in range(6):
        label = float(time_file.readline().split()[-1])
        time_file.readline()  # пропускаем метку окончания пробования
        time_file.readline()  # пропускаем метку оценки
        # time_file.readline()  # пропускаем метку питья воды

        next_label = float(time_file.readline().split()[-1])
        parsed_time_open[label] = [order[i], next_label-label]
    # в файлике для последней пробы меньше строк, поэтому обрабатываем отдельно
    label = float(time_file.readline().split()[-1])
    print(label)
    time_file.readline()
    next_label = float(time_file.readline().split()[-1])
    parsed_time_open[label] = [order[i+1], next_label - label]
    time_file.close()
    type_file.close()

    return parsed_time_closed, parsed_time_open



def WTP_price_taste(folder, type='close', order=[]):
    """
    ЗДЕСЬ БУДЕМ ФОРМИРОВАТЬ 4 словаря С ИНФОРМАЦИЕЙ о:
    - вкусовых оценках образца в слепой дегустации
    - оценках схожести напитка с оригинальной кока-колой
    - готовности платить за каждый из образцов колы в слепой дегустации
    - оценках стоимости образца в слепой дегустации
    """

    path_vol = f'{folder}/DATA/'
    vol_nameS = os.listdir(path_vol)
    parsed_results = dict.fromkeys(vol_nameS)
    if type == 'close':
        for vol_name in vol_nameS:
            path_to_volunteer_data = folder
            WTP_dict = {
                    "chernogolovka1": [],
                    "chernogolovka2": [],
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

                }
            taste_dict = {
                    "chernogolovka1": [],
                    "chernogolovka2": [],
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
                }
            price_dict = {
                    "chernogolovka1": [],
                    "chernogolovka2": [],
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
                }
            sim_dict = {
                    "chernogolovka1": [],
                    "chernogolovka2": [],
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

    if type=='open':
        for vol_name in vol_nameS:
            path_to_volunteer_data = folder
            WTP_dict = dict.fromkeys(order,[])
            taste_stated_dict = dict.fromkeys(order,[])
            taste_revealed_dict = dict.fromkeys(order,[])
            price_dict = dict.fromkeys(order,[])

            file1 = open(f'{path_to_volunteer_data}/DATA/{vol_name}/first.txt', 'r', encoding='utf-8')
            first = file1.readlines()[97:]

            for i in range(0, 36, 6):
                price_dict[order[i//6]], taste_stated_dict[order[i//6]], _ = first[i+1].split('|')
                taste_revealed_dict[order[i//6]] = first[i+3].rstrip()
                WTP_dict[order[i//6]] = first[i+5].strip().replace('|', '').strip()

            parsed_results[vol_name] = {
                'taste_stated': taste_stated_dict,
                'taste_revealed': taste_revealed_dict,
                'WTP': WTP_dict,
                'price': price_dict
            }
            file1.close()
        print(parsed_results)
        return parsed_results


def parse_features(folder, type='close', order=[]):
    """
    Из данных опроса мы вытаскиваем данные по каждому признаку
    """

    path_vol = f'{folder}/DATA/'
    vol_nameS = os.listdir(path_vol)
    parsed_results = dict.fromkeys(vol_nameS)
    types_of_product = open(f'{folder}/DATA/{vol_nameS[0]}/order.txt').readlines()
    sort_order = sorted(set(order))
    double_order = []
    for i in order:
        double_order.append(i + '1')
        double_order.append(i + '2')

    if type == 'close':
        for vol_name in vol_nameS:
            path_to_volunteer_data = folder
            WTP_dict = {
                    "chernogolovka1": [],
                    "chernogolovka2": [],
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

                }
            taste_dict = {
                    "chernogolovka1": [],
                    "chernogolovka2": [],
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
                }
            price_dict = {
                    "chernogolovka1": [],
                    "chernogolovka2": [],
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
                }
            sim_dict = {
                    "chernogolovka1": [],
                    "chernogolovka2": [],
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

    if type=='open':
        for vol_name in vol_nameS:
            path_to_volunteer_data = folder
            WTP_dict = dict.fromkeys(order,[])
            taste_stated_dict = dict.fromkeys(order,[])
            taste_revealed_dict = dict.fromkeys(order,[])
            price_dict = dict.fromkeys(order,[])

            file1 = open(f'{path_to_volunteer_data}/DATA/{vol_name}/first.txt', 'r', encoding='utf-8')
            first = file1.readlines()[97:]

            for i in range(0, 36, 6):
                price_dict[order[i//6]], taste_stated_dict[order[i//6]], _ = first[i+1].split('|')
                taste_revealed_dict[order[i//6]] = first[i+3].rstrip()
                WTP_dict[order[i//6]] = first[i+5].strip().replace('|', '').strip()

            parsed_results[vol_name] = {
                'taste_stated': taste_stated_dict,
                'taste_revealed': taste_revealed_dict,
                'WTP': WTP_dict,
                'price': price_dict
            }
            file1.close()
        print(parsed_results)
        return parsed_results


'''функция для экспорта данных по WTP, оценке вкуса и цены'''
def export_wtp_etc(folder, parsed_results):
    try:
        taste_file = open(f'{folder}/results/taste.csv', "w")
        sim_file = open(f'{folder}/results/similar.csv', "w")
        WTP_file = open(f'{folder}/results/WTP.csv', "w")
        price_file = open(f'{folder}/results/price.csv', "w")
        first_line = "NAME; chernogolovka1; chernogolovka2; cola1; cola2; cola_zero1; cola_zero2; d_cola1; d_cola2; d_zero1; d_zero2; funky1; funky2; \n"
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
    except:
        sg.popup('Проверьте существование папки "results"')
        return -1


def time_range(path_time, type='close', path_type='', order=[]):
    '''
    Функция, которая парсит файлики order и time для расчёта ICA
    Описаниe хода экспериментов см. в функции parse_types
    :param path_time: str, путь к файлу с метками времени
    :param path_type: str, путь к файлу order.txt с информацией о ходе эксперимента
    :return: parsed_types: dict, ключи - метки кока-колы, значения - интервалы времени, когда этот образец пробовали
    '''
    time_file = open(path_time, encoding="utf-8")
    if type == 'close':
        parsed_types_close = {}  # список временных отрезков
        type_file = open(path_type, encoding="utf-8")
        cola_types = type_file.readlines()

        # в изначальном файлике все данные повторяются по 2 раза.
        # нам удобнее ввести уникальные значения, например, cola1 и cola2
        # поэтому мы заводим множество, с помощью которого будем проверять, встречался ли нам уже такой бренд
        brand_check = set()

        time_file.readline()  # пропускаем строку в файле с началом эксперимента

        for i in range(12):
            label = float(time_file.readline().split()[-1])
            next_label = float(time_file.readline().split()[-1])
            cola_type = cola_types[i].rstrip()
            if cola_type in brand_check:
                parsed_types_close[cola_type + '2'] = [label, next_label]
            else:
                parsed_types_close[cola_type+ '1'] = [label, next_label]
                brand_check.add(cola_type)

        return parsed_types_close

    else:
        parsed_types_open = {}

        time = time_file.readlines()[26:]
        print(time)
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!', len(time))
        for i in range(0, 18, 3):
            label = float(time[i].split()[-1])
            next_label = float(time[i+1].split()[-1])
            #print(i, i//3, label, next_label)
            parsed_types_open[order[i//3]] = [label, next_label]

        time_file.close()

        return parsed_types_open



