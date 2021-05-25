import os
import re

from celery.schedules import crontab

from electron import celery_app
from xml.etree import ElementTree as ET

from electron.settings import BASE_DIR
from store.models import Category, Product
import csv


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(minute=0, hour=5), impex())


def atol_import(file_name='imported/export_atol.txt', encoding="windows-1251", start_line=3):

    file = os.path.join(BASE_DIR, file_name)

    with open(file, 'r') as f:
        reader = csv.reader(f, delimiter=';')

        # ignore_starting_with = ('#', '@')  # Игнорируем строки начинающиеся с
        for row in reader:
            if len(row) < 25:
                continue
            try:
                # row = row.split(sep=";")
                # logger.info(f'Row is {row}')
                key = row[0]
                article = row[25]
                price = row[4]
                name = row[2]
                name = re.sub(r'^\([^)]+\)\s*', '', name)
                parent = row[15]
                if len(name) < 3:
                    continue
                if len(article) == 0 and len(price) == 0 and len(row) > 55:
                    try:
                        category = Category.objects.get(id=key)
                    except:
                        category = Category.objects.create(id=key)
                    category.name = name
                    category.save()
                else:
                    try:
                        product = Product.objects.get(id=key)
                    except:
                        category = Category.objects.get(id=parent)
                        product = Product.objects.create(id=key, category=category)
                    product.title = name
                    product.article = article
                    product.price = float(price)
                    product.save()
                    print(key, name)

            except Exception as e:
                print(f'{e}\n\t{row}')
                # logger.error(f'Bad row is {row}\n\t {e}')
                pass


def xml_import(file_name='imported/export.xml'):
    file = os.path.join(BASE_DIR, file_name)
    """
    Parse XML-file with struct:
        <?xml version="1.0" encoding="windows-1251" ?>
        <items date="22.02.21">
        <nom id="36291" name="AUTO MOBIL Очиститель двигателя, 440мл 3-028" art="01013">
            <prices>
                <price  name="Розничная" value="113"/>
            </prices>
            <whs>
                <scl name="ЭЛЕКТРОН  ул. Ленина, 28" count="0" />
                <scl name="Магазин-склад ЭЛЕКТРИКА" count="3" />
            </whs>
        </nom>
        ...
        </items>
    """
    root = ET.parse(file).getroot()

    print(root)

    for node in root.findall('nom'):
        name = node.get('name')
        id = node.get('id')
        # article = node.get('art')
        whs = []
        for sub in node.findall('whs/scl'):
            whs.append(sub.get("count"))

        denied = 0
        try:
            product = Product.objects.get(id=id)
            product.warehouse1 = whs[0]
            product.warehouse2 = whs[1]
            product.save()
        except Exception as e:
            denied += 1
            # Товары, которых не оказалось в alol файле (без категорий) отбрасываются
            print(f'{e}\n\t{node}')
            print('\tid:', id, 'name:', name)

    print('Отброшено:', denied)


def impex():
    atol_import()
    # xml_import()
    print('import finished')
