import sys, os

path = os.getcwd() 
sys.path.append(f'{path}/modules') # Добавляем путь перед импортом! 

# Подключение модулей
import requests
import pdfkit
from bs4 import BeautifulSoup as BS
from urllib3.exceptions import InsecureRequestWarning

# Процедура преобразования html в pdf ---------------------------------------------
def HtmlToPdf(n_, pa_, ar_):
    # Входные данные: номер выпуска, номер раздела, номер статьи
    # Выходные данные: -
    # Процедура преобразовывает html-статью в pdf  

    # Преобразование html-статьи в pdf
    config = pdfkit.configuration(wkhtmltopdf=path + '/wkhtmltopdf/bin/wkhtmltopdf.exe')
    pdfkit.from_file(f'site/ru/{n_}/{pa_}/{ar_}/article.html', f'site/ru/{n_}/{pa_}/{ar_}/article.pdf', configuration=config,
                 verbose=False, options={'enable-local-file-access': True})
    

# Процедура загрузки изображений --------------------------------------------------
def DownloadImg(dataImg_, n_, pa_, ar_):
    # Входные данные: список тегов изображений, номер выпуска, номер раздела, номер статьи 
    # Выходные данные: -
    # Процедура загружает все изображения для статьи на диск

    # Создание директории
    CreateDirectory(f'/site/ru/{n_}/{pa_}/{ar_}/article.files')

    # Загрузка изображений (цикл по списку изображений)
    for img in dataImg_:

        # Скачивание изображения по имени и url сайта
        img_name = img.attrs.get('src')
        img_url = f'https://network-journal.mpei.ac.ru/ru/{n_}/{pa_}/{ar_}/' + img_name 
        response = requests.get(img_url, verify=False).content
        # Имя + путь
        filname = f'./site/ru/{n_}/{pa_}/{ar_}/' + (img_name)
        # Сохранение изображения
        try:
            with open(filname, 'wb') as f:
                f.write(response)
        except: 
            pass


# Процедура получения данных из HTML страницы --------------------------------------------
def GetData(html_):
    # Входные данные: объект, содержащий html страницу
    # Выходные данные: объект, содержащий статью в html формате 
    # Процедура извлекает текст статьи из html-страницы

    # Получение текста статьи из страницы для различных случаев
    data_ = html_.select('.Section1')
    if data_ == []:
        data_ = html_.select('.WordSection1')
        if data_ == []:
            data_ = html_.select('body')
            if len(data_) > 1: 
                data_ = data_[1]
            else:
                data_ = data_[0].select('table')
                data_ = data_[3].select('tr')
                data_ = data_[1]
        else:
            data_ = data_[len(data_) - 1]
    else:
        data_ = data_[0]
    return data_


# Процедура загрузки аннотации --------------------------------------------
def DownloadAnnotation(html_, direct_):
    # Входные данные: объект, содержащий html-страницу, директория для загрузки
    # Выходные данные: -
    # Процедура сохраняет аннотацию в формате html

    # Получение текста аннотации из страницы для различных случаев
    data_ = html_.select('body')
    if len(data_) > 2:
        data_ = data_[2]
    else:
        if len(data_) > 1:
            data_ = data_[1]
        else: 
            data_ = data_[0].select('tr')[6]

    # Преобразование аннотации в строку
    annotation_ = str(data_)

    # Сохранение аннотации
    with open(path + f'/site/ru/{direct_}/annotation.html','w',encoding='utf-8') as f:
        f.write('<meta charset="UTF-8">' + annotation_)


# Процедура загрузки статьи --------------------------------------------
def DownloadArticle(html_, n_, pa_, ar_):
    # Входные данные: объект, содержащий html-страницу, номер выпуска, номер раздела, номер статьи
    # Выходные данные: -
    # Процедура загружает статью и изображения

    # Получение текста статьи
    data_ = GetData(html_)
    article_ = str(data_)

    # Создание директории для статьи
    CreateDirectory(f'/site/ru/{n_}/{pa_}/{ar_}')

    # Сохранение статьи
    with open(path + f'/site/ru/{n_}/{pa_}/{ar_}/article.html','w',encoding='utf-8') as f:
        f.write('<meta charset="UTF-8">' + article_)

    # Загрузка изображений, если они имеются
    if (len(data_.select('img')) > 0):
        dataImg_ = data_.select('img')
        DownloadImg(dataImg_, n_, pa_, ar_)


# Процедура создания директории ------------------------------------------
def CreateDirectory(direct_):
    # Входные данные: требуемая директория
    # Выходные данные: -
    # Процедура создает необходимую директорию

    # Создание в корневой директории указанную, если ее нет
    direct_ = path + direct_
    if not os.path.isdir(direct_):
        os.makedirs(direct_, exist_ok=True)


# Основная программа ==================================================================================

# Отключение предупреждений 
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
# Корневой путь
path = os.getcwd() 
# Ввод номера выпуска журнала для загрузки
try:
    n = int(input('Введите номер выпуска: '))
except:
    n = -1
# Проверка на корректность номера выпуска
if (n < 40 and n > 0):

    # Создание директории для выпуска
    direct = f'/site/ru/{n}'
    CreateDirectory(direct)

    # Запрос к серверу для аннотации к выпуску
    r = requests.get(f'http://network-journal.mpei.ac.ru/cgi-bin/main.pl?l=ru&n={n}', verify=False)
    # Получение контента
    html = BS(r.content, 'html.parser')
    # Загрузка аннотации к выпуску
    direct = f'{n}'
    DownloadAnnotation(html, direct)

    # Номер раздела
    pa = 1

    # Запрос к серверу для аннотации к разделу
    r = requests.get(f'http://network-journal.mpei.ac.ru/cgi-bin/main.pl?l=ru&n={n}&pa={pa}', verify=False)

    # Цикл по разделам выпуска
    while r.status_code == 200:

        # Создание директории для раздела
        direct = f'/site/ru/{n}/{pa}'
        CreateDirectory(direct)

        # Получение контента
        html = BS(r.content, 'html.parser')
        # Загрузка аннотации к разделу
        direct = f'{n}/{pa}'
        DownloadAnnotation(html, direct)

        # Номер статьи
        ar = 1
        # Запрос к серверу для статьи
        r = requests.get(f'http://network-journal.mpei.ac.ru/cgi-bin/main.pl?l=ru&n={n}&pa={pa}&ar={ar}', verify=False)

        # Цикл по статьям раздела
        while r.status_code == 200:

            # Получение контента
            html = BS(r.content, 'html.parser')
            # Загрузка статьи
            DownloadArticle(html, n, pa, ar)

            # Преобразование в PDF
            try:
                HtmlToPdf(n, pa, ar)
            except:
                pass

            ar += 1
            # Запрос к серверу для статьи
            r = requests.get(f'http://network-journal.mpei.ac.ru/cgi-bin/main.pl?l=ru&n={n}&pa={pa}&ar={ar}', verify=False)

        pa += 1
        # Запрос к серверу для аннотации к разделу
        r = requests.get(f'http://network-journal.mpei.ac.ru/cgi-bin/main.pl?l=ru&n={n}&pa={pa}', verify=False)

    print(f'Загрузка выпуска {n} завершена!')
else:
    print('Ошибка ввода!')