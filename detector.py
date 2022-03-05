"""
Python 3.9.10 (tags/v3.9.10:f2f3f53, Jan 17 2022, 15:14:21) [MSC v.1929 64 bit (AMD64)] on win32
Данный модуль отвечает за детекцию движения
"""

import cv2  # Импортируем модуль OpenCV
import time
import os


# import main

def corrector(name_file: str, chk_video_det, xy_coord: list, frame_zoom: int, size_detect: int,
              lab_o_proc, window, frame_shift, play_speed):
    """Данная функция восстанавливает файл с поврежденной временной шкалой и запускает детектор.
    name_file - Имя файла, который передается в обработку
    play_speed - Скорость воспроизведения (Пока не работает)
    chk_video_det - Флаг отображения окна воспроизведения при поиске
    xy_coord - Список координат зоны поиска
    frame_zoom - Коэффициент сжатия видео при отображении
    size_detect - Размер детектируемого объекта
    lab_o_proc - Ссылка на метку для отображения прогресса
    window - Ссылка на окно
    frame_shift - Сдвиг фреймов при обнаружении движения
    play_speed - Пропуск фреймов для ускорения

    """
    if os.path.exists("ffmpeg.exe"):
        os.system('ffmpeg -i "' + name_file + '" -map 0:v -vcodec copy -bsf:v h264_mp4toannexb  -y "'+ name_file[:-4]+'_source-video.h264"')
        os.system(
            'ffmpeg -fflags +genpts -r 25 -i "' + name_file[:-4] + '_source-video.h264" -vcodec copy -y "' + name_file[:-4] + '_recovered.avi"')
        os.remove(name_file[:-4] + '_source-video.h264')
        detector(name_file[:-4] + '_recovered.avi', chk_video_det, xy_coord, frame_zoom, size_detect,
                 lab_o_proc, window, frame_shift, play_speed)

    else:
        print("Для корректной работы необходим файл ffmpeg.exe")


def detector(name_file: str, chk_video_det, xy_coord: list, frame_zoom: int, size_detect: int,
             lab_o_proc, window, frame_shift, play_speed) -> bool:
    """Данная функция производит поиск движения в заданной области, в текущем файле.
    name_file - Имя файла, который передается в обработку
    chk_video_det - Флаг отображения окна воспроизведения при поиске
    xy_coord - Список координат зоны поиска
    frame_zoom - Коэффициент сжатия видео при отображении
    size_detect - Размер детектируемого объекта
    lab_o_proc - Ссылка на метку для отображения прогресса
    window - Ссылка на окно
    frame_shift - Сдвиг фреймов при обнаружении движения
    play_speed - Пропуск фреймов для ускорения

    """
    none_frame: int = 0  # Счетчик для проверки пустых фреймов
    start_detect = time.time()  # Получение времени начала обработки видео файла

    cap = cv2.VideoCapture(name_file)  # Захватываем видео с файла
    #cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
    off_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Получаем общее количество фреймов

    frame_width_det = (cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Получаем размер исходного видео
    frame_height_det = (cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    output = cv2.VideoWriter(name_file[:-4] + "_detect" + name_file[len(name_file) - 4:],
                             cv2.VideoWriter_fourcc('H', '2', '6', '4'), 20,
                             (int(frame_width_det), int(frame_height_det)))  # Параметры выгрузки MJPG PIM1 XVID
    if chk_video_det:
        cv2.namedWindow(name_file, 0)  # Определяем окно вывода
    while True:  # Вывод кадров производится в цикле
        ret1, frame1 = cap.read()
        # Данное смещение позволяет сгруппировать очертания двигающегося объекта
        for _ in range(frame_shift):
           cap.read()
        ret2, frame2 = cap.read()
        # Данное смещение служит для ускорения
        for _ in range(play_speed):
           cap.read()
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == off_frames:
            break
        if not ret1 * ret2:
            none_frame += 1
            if none_frame > 10:
                print('Превышено допустимое количество пустых фреймов. Начато восстановление файла.')
                output.release()  # Закрываем файл для вывода
                os.remove(name_file[:-4] + '_detect' + name_file[len(name_file) - 4:])  # Удаляем его
                return False  # Возвращаем флаг, что надо запустить восстановление
            continue

        # frame1=frame1[y1_search:y2_search,x1_search:x2_search] #Обрезка фрейма до нужного размера. Может пригодиться
        # frame2=frame2[y1_search:y2_search,x1_search:x2_search]
        # Вывод в процентах прогресса
        lab_o_proc["text"] = str(cap.get(cv2.CAP_PROP_POS_FRAMES) * 100 // off_frames+1) + " %"
        window.update()  # Обновление окна для отрисовки прогресса
        if ret2:
            if chk_video_det:
                # Метод для визуализации массива кадров
                frame1 = algorithm_detector_1(frame1, frame2, xy_coord, frame_zoom, size_detect, output)
                cv2.imshow(name_file, frame1)
                cv2.resizeWindow(name_file, int(frame_width_det) // 2,
                                 int(frame_height_det) // 2)  # Устанавливаем размер окна вывода
        else:
            break
        if chk_video_det and cv2.getWindowProperty(name_file, 1) == 1:  # Выход из программы по закрытию окна
            break
        if cv2.waitKey(2) == 27:  # Выход по ESC
            break

    cap.release()
    output.release()
    # Проверяем количество сохраненных фреймов
    output = cv2.VideoCapture(name_file[:-4] + "_detect" + name_file[len(name_file) - 4:])
    frames_output = int(output.get(cv2.CAP_PROP_FRAME_COUNT))
    output.release()
    cv2.destroyAllWindows()
    if frames_output == 0:  # Если сохраненных фреймов нет, то удаляем файл
        os.remove(name_file[:-4] + '_detect' + name_file[len(name_file) - 4:])  # Удаляем его
    end_detect = time.time()  # Время завершения обработки видео файла
    # Выводит время затраченное на обработку файла
    print(name_file, '->', str(time.strftime("%M:%S", time.localtime(end_detect - start_detect))))

    return True


def algorithm_detector_1(frame1, frame2, xy_coord: list, frame_zoom: int, size_detect: int, output):
    x1_search = xy_coord[0][0] * frame_zoom
    y1_search = xy_coord[0][1] * frame_zoom
    x2_search = xy_coord[1][0] * frame_zoom
    y2_search = xy_coord[1][1] * frame_zoom
    # Обработка видео фрейма для определения движения
    diff_frame = cv2.absdiff(frame1, frame2)  # Вычитаем из одного кадра другой
    gray_frame = cv2.cvtColor(diff_frame, cv2.COLOR_BGR2GRAY)  # перевод кадров в черно-белую градацию
    blur_frame = cv2.GaussianBlur(gray_frame, (5, 5), 0)  # фильтрация лишних контуров
    _, thresh_frame = cv2.threshold(blur_frame, 20, 255,
                                    cv2.THRESH_BINARY)  # метод для выделения кромки объекта белым цветом любое
    # значение больше 20 станет белым 255
    dilated_frame = cv2.dilate(thresh_frame, None, iterations=3)  # расширение белой зоны
    '''
    данный метод противоположен методу erosion(), т.е. эрозии объекта, 
    и расширяет выделенную на предыдущем этапе область
    '''

    contours, _ = cv2.findContours(dilated_frame, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)  # cv2.RETR_TREE нахождение массива контурных точек
    cv2.rectangle(frame1, (x1_search, y1_search), (x2_search, y2_search), (255, 0, 0), 2)  # Зона поиска
    for contour in contours:
        (x, y, w, h) = cv2.boundingRect(
            contour)
        '''
        преобразование массива из предыдущего этапа в кортеж из четырех координат
        метод contourArea() по заданным contour точкам, здесь кортежу, 
        вычисляет площадь зафиксированного объекта в каждый момент времени, это можно проверить
        '''
        if (w * h) < ((x2_search - x1_search) * (y2_search - y1_search) * int(size_detect) // 100):
            continue
        if not (x + w > x1_search and x < x2_search and y + h > y1_search and y < y2_search):
            continue
        output.write(frame2)  # Записываем не измененный фрейм
        cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Получение прямоугольника из точек кортежа
        Рисуем красную точку
        cv2.circle(frame1, (int(frame_width_det) - 50, int(frame_height_det) - 40), 10, (0, 0, 255),-1)
        # Также можно было просто нарисовать контур объекта
        # cv2.drawContours(frame1, contours, -1, (0, 255, 0), 2)
    return frame1
