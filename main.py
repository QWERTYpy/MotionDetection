"""
Python 3.9.10 (tags/v3.9.10:f2f3f53, Jan 17 2022, 15:14:21) [MSC v.1929 64 bit (AMD64)] on win32
"""
import cv2  # Импортируем модуль OpenCV
import tkinter as tk  # Для создания интерфейса пользователя
from tkinter.filedialog import askopenfilenames  # Отвечает за открытие диалога выбора файла
from PIL import Image, ImageTk  # Отвечает за обработку картинок
import os
import configparser
import tkinter.messagebox
import time

import detector as dt

"""
Нужно добавить проверку вводимых значений
"""
config = configparser.ConfigParser()
config.read("detector.ini")

# Во сколько раз уменьшить фрейм видео для просмотра
frame_zoom = int(config["Detector"]["frame_zoom"])
# Количество пропускаемых фреймов (переход к указанному фрейму занимает больше времени чем считывание)
play_speed = int(config["Detector"]["play_speed"])
# Сдвиг фреймов при детекции движения
frame_shift = int(config["Detector"]["frame_shift"])
# Зона поиска
xy_coord = []
# Размер искомого объекта
size_detect = 20
# Кортеж адресов обрабатываемых файлов
filepath = ()
# Чувствительность ffmpeg
sens_ff = 4


def open_file():
    """
    Функция отвечает за открытие файла
    """
    global filepath
    filepath = askopenfilenames(
        filetypes=[('Видео файлы', '*.avi'), ('Все файлы', '*')]
    )
    if not filepath:
        return
    lab_f_count["text"] = len(filepath)
    lab_o_count["text"] = 0
    but_start['text'] = 'Старт'
    but_ffmpeg['text'] = 'Ffmpeg det'


def start(flag=True):
    """
    Функция обработки нажатия кнопки Старт
    """
    if len(xy_coord) == 2:
        if but_start['text'] == 'Старт' and flag:
            but_start['text'] = 'Стоп'
            lab_o_count['text'] = 0
        elif but_start['text'] == "Стоп" and but_pause['text'] == 'Пауза' and flag:
            but_start['text'] = 'Старт'

        for file_path_id in range(int(lab_o_count['text']), len(filepath)):
            file_path = filepath[file_path_id]
            result_det = dt.detector(file_path, chk_video.get(), xy_coord, frame_zoom,
                                     size_detect, lab_o_proc, window, frame_shift, play_speed, but_start, but_pause)
            if result_det == 'Correct':
                result_cor = dt.corrector(file_path, chk_video.get(), xy_coord, frame_zoom,
                                          size_detect, lab_o_proc, window, frame_shift, play_speed, but_start,
                                          but_pause)
                if result_cor == 'Pause': break
                elif result_cor == 'Ffmpeg':
                    print("Для корректной работы необходим файл ffmpeg.exe")
                    break
            elif result_det == 'Pause': break

            if but_start['text'] == "Стоп" and but_pause['text'] == 'Пауза':
                lab_o_count["text"] = filepath.index(file_path) + 1
                window.update()

            # Если стоит отметка об объединении и конвертирован последний файл, то запустить объединение
            if chk_cut.get() and len(filepath) == filepath.index(file_path) + 1:
                my_file = open("list.txt", "w+")  # Создаем файл для хранения имен файлов для объединения
                for name_file in os.listdir(os.path.dirname(file_path)):
                    if 'detect' in name_file:
                        my_file.write("file '" + os.path.dirname(file_path) + "/" + name_file + "'\n")
                my_file.close()
                os.system('ffmpeg -f concat -safe 0 -i list.txt -c copy -y ' + file_path[:-4] +
                          '_all_result' + file_path[len(file_path) - 4:])
                os.remove('list.txt')
    elif len(xy_coord) == 0:
        tkinter.messagebox.showinfo("Внимание", "Пожалуйста, укажите зону обнаружения и размер объекта детекции.")


def pause():
    if but_start['text'] == 'Старт':
        return False
    if but_pause['text'] == 'Пауза':
        but_pause['text'] = 'Продолжить'
    else:
        but_pause['text'] = 'Пауза'
        start(False)


def motion(event):
    """
    Функция определения позиции курсора
    """
    global xy_coord
    x, y = event.x, event.y
    xy_coord.append([x, y])
    if len(xy_coord) == 2:
        canvas.create_rectangle(xy_coord[0][0], xy_coord[0][1], xy_coord[1][0], xy_coord[1][1], outline='#3F0', width=3,
                                tags="myRectangle")
    elif len(xy_coord) == 3:
        del xy_coord[0]
        del xy_coord[0]
        canvas.delete("myRectangle")


def apply(s_d, w_d,s_f):
    """
    Функция обработки нажатия кнопки - Применить
    """
    global size_detect
    global sens_ff
    size_detect = s_d
    sens_ff = s_f
    # print(size_detect)
    w_d.destroy()


def zone_detect():
    """
    Функция отображает первый кадр для выбора на нем зоны детекции
    @return:
    """
    global imgtk
    # Так как после отработки функции переменные удаляются, для отображения картинки делаем переменную глобальной
    if not len(filepath):
        tkinter.messagebox.showinfo("Внимание", "Пожалуйста, выберите файл для обработки.")
        return False
    cap = cv2.VideoCapture(filepath[0])  # Захватываем видео с файла
    global xy_coord
    frame_width = (cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Получаем размер исходного видео
    frame_height = (cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if len(xy_coord) == 0:
        xy_coord.append([2, 2])
        xy_coord.append([int(frame_width) // frame_zoom, int(frame_height) // frame_zoom])

    _, frame = cap.read()
    frame = cv2.resize(frame, (int(frame_width) // frame_zoom, int(frame_height) // frame_zoom),
                       interpolation=cv2.INTER_AREA)
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    imgtk = ImageTk.PhotoImage(image=Image.fromarray(cv2image))
    cap.release()
    window_zone = tk.Toplevel(window)
    window_zone.title("выберите зону детекции")
    window_zone.rowconfigure([0, 1, 2, 3, 4], minsize=30)
    window_zone.columnconfigure([0, 1], minsize=100)
    _, x_win, y_win = window.geometry().split('+')
    window_zone.geometry('+'+x_win+'+'+y_win)
    lab_text_zone = tk.Label(window_zone, text="Чувствительность\nВ _% от зоны поиска")
    lab_ffmpeg = tk.Label(window_zone, text="Чувствительность ffmpeg\n [1..9]")
    btn_prim = tk.Button(window_zone, text="Применить", width=12, command=lambda: apply(ent_proc.get(), window_zone,
                                                                                        ent_ffmpeg.get()))
    ent_proc = tk.Entry(window_zone)  # Создаем виджет с пустой строкой
    ent_proc.insert(0, str(size_detect))  # Выводим в эту строку значение по умолчанию 50%
    ent_ffmpeg = tk.Entry(window_zone)
    ent_ffmpeg.insert(0,str(sens_ff))
    lab_text_zone.grid(row=0, column=1, sticky='s', padx=5, pady=5)
    ent_proc.grid(row=1, column=1, sticky='n', padx=5, pady=5)
    lab_ffmpeg.grid(row=2, column=1, sticky='s', padx=5, pady=5)
    ent_ffmpeg.grid(row=3, column=1, sticky='n', padx=5, pady=5)
    btn_prim.grid(row=4, column=1, padx=5, pady=5)

    global canvas
    canvas = tk.Canvas(window_zone, width=int(frame_width) // frame_zoom, height=int(frame_height) // frame_zoom)
    canvas.create_image(0, 0, anchor="nw", image=imgtk)
    canvas.create_rectangle(xy_coord[0][0], xy_coord[0][1], xy_coord[1][0], xy_coord[1][1], outline='#3F0', width=3,
                            tags="myRectangle")
    canvas.grid(row=0, column=0, rowspan=5, padx=5, pady=5)
    canvas.bind('<Button-1>', motion)


def ffmpeg_det():
    if len(xy_coord) == 2:
        but_ffmpeg['text'] = 'В работе'
        window.update()
        width_ff = str((xy_coord[1][1] - xy_coord[0][1]) * frame_zoom)
        height_ff = str((xy_coord[1][0] - xy_coord[0][0]) * frame_zoom)
        x_ff = str(xy_coord[0][0] * frame_zoom)
        y_ff = str(xy_coord[0][1] * frame_zoom)
        def ff_time(ff_t):
            h = int(ff_t // 3600)
            m = int((ff_t // 60) % 60)
            s = int(ff_t % 60)
            return "%02d:%02d:%02d" % (h, m, s)

        for file_path_id in range(int(lab_o_count['text']), len(filepath)):
            file_path = filepath[file_path_id]
            start_detect = time.time()
            os.system('ffmpeg -i '+file_path+' -vf "crop='+width_ff+':'+height_ff+':'+x_ff+':'+y_ff+",select='gt(scene,0.00"+
                      sens_ff+")',"+'setpts=N/(25*TB)" -y '+ file_path[:-4] +
                      '_crop_detect' + file_path[len(file_path) - 4:])
            """
            os.system('ffmpeg -i ' + file_path + ' -vf "crop=' + width_ff + ':' + height_ff + ':' + x_ff + ':' + y_ff +
                      ",select='gt(scene,0.00" + sens_ff + ")'," + 'showinfo" -f null - > '+file_path+'.txt 2>&1')
            if os.path.exists(file_path+'.txt'):
                print('Существует')
                file_inf = open(file_path+'.txt', 'r')
                sec_inf = []
                for line in file_inf:
                    if "pts_time:" in line:
                        sec_inf.append(int(float(line[line.find("pts_time:")+9:line.find("pos:")])))

                print(sec_inf)
                for id in list(sec_inf):
                    if sec_inf.count(id) > 1:
                        sec_inf.remove(id)

                print(sec_inf)
                sec_line = []
                sec_id = 0
                print('Длина', len(sec_inf))
                #print(sec_inf[64])
                while sec_id < len(sec_inf):
                    #print(sec_id)
                    left_sec = sec_inf[sec_id]
                    while sec_inf[sec_id] - left_sec < 1:
                        if sec_id < len(sec_inf)-1:
                            sec_id+=1
                        else:
                            sec_id+=1
                            break
                    sec_id-=1
                    right_sec = sec_inf[sec_id]
                    sec_line.append([left_sec, right_sec])
                    sec_id += 1
                print(sec_line)

                def ff_rec():
                    #global sec_line
                    print(sec_line)
                    for ff_list_id in range(0, len(sec_line)):
                        if ff_list_id == len(sec_line) - 1:
                            return sec_line
                        if sec_line[ff_list_id + 1][0] - sec_line[ff_list_id][1] <= 2:
                            sec_line.insert(ff_list_id, [sec_line[ff_list_id][0], sec_line[ff_list_id + 1][1]])
                            sec_line.pop(ff_list_id + 1)
                            sec_line.pop(ff_list_id + 1)
                            break
                    ff_rec()

                ff_rec()
                print(sec_line)
                print(sec_line)
                for ss, to in sec_line:
                    print(ff_time(ss), ff_time(to+1))
                    os.system('ffmpeg -ss '+ff_time(ss)+' -to '+ff_time(to+1)+' -i '+file_path+' -c copy -y '+file_path[:-4] +
                    str("%03d" % sec_line.index([ss, to]))+ "ff_tmp" + file_path[len(file_path) - 4:])
                    #ffmpeg -ss 00:00:01 -to 00:00:02 -i pr.avi -c copy -y out2.avi

            my_file = open("list.txt", "w+")  # Создаем файл для хранения имен файлов для объединения
            for name_file in os.listdir(os.path.dirname(file_path)):
                if 'ff_tmp' in name_file:
                    my_file.write("file '" + os.path.dirname(file_path) + "/" + name_file + "'\n")
            my_file.close()
            os.system('ffmpeg -f concat -safe 0 -i list.txt -c copy -y ' + file_path[:-4] +
                    '_all_result' + file_path[len(file_path) - 4:])
            os.remove('list.txt')
            file_inf.close()
            os.remove(file_path+'.txt')
            for name_file in os.listdir(os.path.dirname(file_path)):
                if 'ff_tmp' in name_file:
                    os.remove(os.path.dirname(file_path) + "/" + name_file)

            lab_o_count["text"] = filepath.index(file_path) + 1
            window.update()
            end_detect = time.time()  # Время завершения обработки видео файла
            # Выводит время затраченное на обработку файла
            print(file_path, '->', str(time.strftime("%M:%S", time.localtime(end_detect - start_detect))))
            # ffmpeg -i test.avi -vf "crop=300:300:1200:200,select='gt(scene,0.009)',setpts=N/(25*TB)" -y out2.mp4
            # ffmpeg -i pr.avi -vf "crop=300:300:740:300,select='gt(scene,0.004)',showinfo" -f null - > cor.log 2>&1
            # Если стоит отметка об объединении и конвертирован последний файл, то запустить объединение
            """
        but_ffmpeg['text'] = 'Готово'
        window.update()
        #if chk_cut.get() and len(filepath) == filepath.index(file_path) + 1:
        #    my_file = open("list.txt", "w+")  # Создаем файл для хранения имен файлов для объединения
        #    for name_file in os.listdir(os.path.dirname(file_path)):
        #        if 'detect' in name_file:
        #            my_file.write("file '" + os.path.dirname(file_path) + "/" + name_file + "'\n")
        #    my_file.close()
        #    os.system('ffmpeg -f concat -safe 0 -i list.txt -c copy -y ' + file_path[:-4] +
        #            '_all_result' + file_path[len(file_path) - 4:])
        #    os.remove('list.txt')

    elif len(xy_coord) == 0:
        tkinter.messagebox.showinfo("Внимание", "Пожалуйста, укажите зону обнаружения и размер объекта детекции.")

window = tk.Tk()  # Создается главное окно
window.title("Детектор движения в файле v.1.2")  # Установка названия окна
window.resizable(width=False, height=False)
window.geometry('350x150+100+100')
window.rowconfigure([0, 1, 2, 3, 4], minsize=30)
window.columnconfigure([0, 1, 2], minsize=100)

# Создаем необходимые элементы управления
# Файлов: шт
lab_file = tk.Label(text="Файлов:")
lab_f_count = tk.Label(text="0")
# Кнопка открытия диалога выбора файлов
but_o_file = tk.Button(text="Открыть", width=12, command=open_file)
# Кнопка открытия диалога выбора зоны детекции
but_zone = tk.Button(text="Зона детекции", width=12, command=zone_detect)
# Прогресс:  __%
lab_proc = tk.Label(text="Прогресс:")
lab_o_proc = tk.Label(text="0 %")
# Обработано: шт
lab_obr = tk.Label(text="Обработано:")
lab_o_count = tk.Label(text="0")
# Чекбокс выбора отображать ли видео при поиске
chk_video = tk.IntVar()
chk_video.set(0)
lab_chk = tk.Checkbutton(text="Отображать видео", variable=chk_video)
lab_chk.select()
# Чекбокс выбора склейки фрагментов
chk_cut = tk.IntVar()
chk_cut.set(0)
lab_chk_cut = tk.Checkbutton(text="Склеить фрагменты", variable=chk_cut)
lab2 = tk.Label(text="00:00")
but_start = tk.Button(text="Старт", command=start, width=12)
but_pause = tk.Button(text="Пауза", command=pause, width=12)
but_ffmpeg = tk.Button(text='Ffmpeg det', command=ffmpeg_det, width=12)

# Размещаем его на экране
lab_file.grid(row=0, column=0)
lab_f_count.grid(row=0, column=1)
but_o_file.grid(row=0, column=2)
lab_proc.grid(row=1, column=0)
lab_o_proc.grid(row=1, column=1)
but_zone.grid(row=1, column=2)
lab_obr.grid(row=2, column=0)
lab_o_count.grid(row=2, column=1)
but_start.grid(row=2, column=2)
but_pause.grid(row=3, column=2)
but_ffmpeg.grid(row=4,column=2)
lab_chk.grid(row=3, column=0, sticky="w")
lab_chk_cut.grid(row=4, column=0, sticky="w")
window.mainloop()
