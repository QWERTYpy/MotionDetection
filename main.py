"""
Python 3.9.10 (tags/v3.9.10:f2f3f53, Jan 17 2022, 15:14:21) [MSC v.1929 64 bit (AMD64)] on win32
"""
import cv2  # Импортируем модуль OpenCV
import tkinter as tk  # Для создания интерфейса пользователя
from tkinter.filedialog import askopenfilenames  # Отвечает за открытие диалога выбора файла
from PIL import Image, ImageTk  # Отвечает за обработку картинок
import os
import configparser

import detector as dt

"""
Нужно добавить паузу и досрочное прерывание
добавить слияние файлов обнаружения в один
Добавить уменьшение пропускаемых фреймов при обнаружении движения
Выявлена ошибка и файлами Бивард. Они все идут через конвертацию

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


def start():
    """
    Функция обработки нажатия кнопки Старт
    """
    if len(xy_coord) == 2:
        for file_path in filepath:
            if not dt.detector(file_path, chk_video.get(), xy_coord, frame_zoom,
                               size_detect, lab_o_proc, window, frame_shift, play_speed):
                dt.corrector(file_path, chk_video.get(), xy_coord, frame_zoom,
                             size_detect, lab_o_proc, window, frame_shift, play_speed)
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
        print("Пожалуйста, укажите зону обнаружения и размер объекта детекции.")


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


def zone_detect():
    """
    Функция отображает первый кадр для выбора на нем зоны детекции
    @return:
    """
    global imgtk
    # Так как после отработки функции переменные удаляются, для отображения картинки делаем переменную глобальной
    cap = cv2.VideoCapture(filepath[0])  # Захватываем видео с файла
    global frame_width
    global frame_height
    global xy_coord
    frame_width = (cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Получаем размер исходного видео
    frame_height = (cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if len(xy_coord) == 0:
        xy_coord.append([2, 2])
        xy_coord.append([int(frame_width) // frame_zoom, int(frame_height) // frame_zoom])

    def apply():
        """
        Функция обработки нажатия кнопки - Применить
        """
        global size_detect
        size_detect = ent_proc.get()
        # print(size_detect)
        window_zone.destroy()

    _, frame = cap.read()
    frame = cv2.resize(frame, (int(frame_width) // frame_zoom, int(frame_height) // frame_zoom),
                       interpolation=cv2.INTER_AREA)
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    cap.release()
    window_zone = tk.Toplevel(window)
    window_zone.title("выберите зону детекции")
    window_zone.rowconfigure([0, 1, 2, 3], minsize=30)
    window_zone.columnconfigure([0, 1], minsize=100)
    lab_text_zone = tk.Label(window_zone, text="Чувствительность\nВ _% от зоны поиска")
    btn_prim = tk.Button(window_zone, text="Применить", width=12, command=apply)
    ent_proc = tk.Entry(window_zone)  # Создаем виджет с пустой строкой
    ent_proc.insert(0, str(size_detect))  # Выводим в эту строку значение по умолчанию 50%
    global lab_coord
    lab_text_zone.grid(row=0, column=1, sticky='s', padx=5, pady=5)
    btn_prim.grid(row=3, column=1, padx=5, pady=5)
    ent_proc.grid(row=1, column=1, sticky='n', padx=5, pady=5)
    global canvas
    canvas = tk.Canvas(window_zone, width=int(frame_width) // frame_zoom, height=int(frame_height) // frame_zoom)
    canvas.create_image(0, 0, anchor="nw", image=imgtk)
    canvas.create_rectangle(xy_coord[0][0], xy_coord[0][1], xy_coord[1][0], xy_coord[1][1], outline='#3F0', width=3,
                            tags="myRectangle")
    canvas.grid(row=0, column=0, rowspan=4, padx=5, pady=5)
    canvas.bind('<Button-1>', motion)


window = tk.Tk()  # Создается главное окно
window.title("Детектор движения в файле v.1.2")  # Установка названия окна
window.resizable(width=False, height=False)
window.rowconfigure([0, 1, 2, 3, 4], minsize=30)
window.columnconfigure([0, 1, 2], minsize=100)

# imgtk = ImageTk.PhotoImage()
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
lab_chk.grid(row=3, column=0, sticky="w")
lab_chk_cut.grid(row=4, column=0, sticky="w")
window.mainloop()
