#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Выполнить индивидуальное задание 1 лабораторной работы 2.19, добавив
возможность работы с исключениями и логгирование.
"""

from dataclasses import dataclass, field
from datetime import datetime
import logging
import sys
from typing import List
import xml.etree.ElementTree as ET


# Класс пользовательского исключения в случае, если неверно
# введен номер маршрута.
class IllegalNumberError(Exception):
    def __init__(self, number, message="Illegal number"):
        self.number = number
        self.message = message
        super(IllegalNumberError, self).__init__(message)

    def __str__(self):
        return f"{self.number} -> {self.message}"


# Класс пользовательского исключения в случае, если неверно
# введено время маршрута.
class IllegalTimeError(Exception):
    pass


# Класс пользовательского исключения в случае, если введенная
# команда является недопустимой.
class UnknownCommandError(Exception):
    def __init__(self, command, message="Unknown command"):
        self.command = command
        self.message = message
        super(UnknownCommandError, self).__init__(message)

    def __str__(self):
        return f"{self.command} -> {self.message}"


@dataclass(frozen=True)
class Routes:
    destination: str
    number: int
    time: str


@dataclass
class Way:
    routes: List[Routes] = field(default_factory=lambda: [])

    def add(self, destination: str, number: int, time: str):
        if number < 0:
            raise IllegalNumberError(number)

        try:
            datetime.strptime(time, "%H:%M")
        except IllegalTimeError as err:
            print(err)

        self.routes.append(
            Routes(
                destination=destination,
                number=number,
                time=time
            )
        )

        self.routes.sort(key=lambda route: route.destination)

    def __str__(self):
        # Заголовок таблицы.
        table = []
        line = '+-{}-+-{}-+-{}-+'.format(
            '-' * 30,
            '-' * 4,
            '-' * 20
        )
        table.append(line)
        table.append(
            '| {:^30} | {:^4} | {:^20} |'.format(
                "Пункт назначения",
                "№",
                "Время"
            )
        )
        table.append(line)
        # Вывести данные о всех сотрудниках.
        for route in self.routes:
            table.append(
                '| {:<30} | {:>4} | {:<20} |'.format(
                    route.destination,
                    route.number,
                    route.time
                )
            )
        table.append(line)
        return '\n'.join(table)

    def select(self, period: str) -> List[Routes]:
        result: List[Routes] = []

        for route in self.routes:
            time_route = route.time
            time_route1 = datetime.strptime(time_route, "%H:%M")
            time_select = datetime.strptime(period, "%H:%M")
            if time_select < time_route1:
                result.append(route)

        # Возвратить список выбранных маршрутов.
        return result

    def load(self, filename: str) -> None:
        with open(filename, 'r', encoding='utf8') as fin:
            xml = fin.read()
        parser = ET.XMLParser(encoding="utf8")
        tree = ET.fromstring(xml, parser=parser)
        self.routes = []
        for route_element in tree:
            destination, number, time = None, None, None
            for element in route_element:
                if element.tag == 'destination':
                    destination = element.text
                elif element.tag == 'number':
                    number = int(element.text)
                elif element.tag == 'time':
                    time = element.text
                if destination is not None and number is not None \
                        and time is not None:
                    self.routes.append(
                        Routes(
                            destination=destination,
                            number=number,
                            time=time
                        )
                    )

    def save(self, filename: str):
        root = ET.Element('workers')
        for route in self.routes:
            route_element = ET.Element('route')

            destination = ET.SubElement(route_element, 'destination')
            destination.text = route.destination

            number_element = ET.SubElement(route_element, 'number')
            number_element.text = str(route.number)

            time_element = ET.SubElement(route_element, 'time')
            time_element.text = route.time

            root.append(route_element)

        tree = ET.ElementTree(root)
        with open(filename, 'wb') as f:
            tree.write(f, encoding='utf8', xml_declaration=True)


if __name__ == '__main__':
    # Выполнить настройку логгера.
    logging.basicConfig(
        filename='routes1.log',
        level=logging.INFO
    )
    # Список маршрутов.
    way = Way()
    # Организовать бесконечный цикл запроса команд.
    while True:
        try:
            # Запросить команду из терминала.
            command = input(">>> ").lower()
            # Выполнить действие в соответствие с командой.

            if command == 'exit':
                break

            elif command == 'add':
                # Запросить данные о работнике.
                destination = input("Направление? ")
                number = int(input("Номер? "))
                time = input("Время? ")
                # Добавить работника.
                way.add(destination, number, time)
                logging.info(
                    f"Добавлен маршрут: {destination}, №{number}, "
                    f"в {time}.")

            elif command == 'list':
                # Вывести список.
                print(way)
                logging.info("Отображен список маршрутов.")

            elif command.startswith('select '):
                # Разбить команду на части для выделения времени.
                parts = command.split(maxsplit=1)
                # Запросить маршруты.
                selected = way.select(parts[1])
                # Вывести результаты запроса.
                if selected:
                    for idx, route in enumerate(selected, 1):
                        print(
                            '{:>4}: {}'.format(idx, route.destination)
                        )
                        logging.info(
                            f"Найдено {len(selected)} маршрутов с "
                            f"временем отправления после {parts[1]}."
                        )
                else:
                    print("Маршруты не найдены.")
                    logging.warning(
                        f"Маршруты с временем отправления после {parts[1]}."
                    )

            elif command.startswith('load '):
                # Разбить команду на части для имени файла.
                parts = command.split(maxsplit=1)
                # Загрузить данные из файла.
                way.load(parts[1])
                logging.info(f"Загружены данные из файла {parts[1]}.")

            elif command.startswith('save '):
                # Разбить команду на части для имени файла.
                parts = command.split(maxsplit=1)
                # Сохранить данные в файл.
                way.save(parts[1])
                logging.info(f"Сохранены данные в файл {parts[1]}.")

            elif command == 'help':
                # Вывести справку о работе с программой.
                print("Список команд:\n")
                print("add - добавить мавшрут;")
                print("list - вывести список маршрутов;")
                print("select <время> - маршруты после указанного времени;")
                print("load <имя_файла> - загрузить данные из файла;")
                print("save <имя_файла> - сохранить данные в файл;")
                print("help - отобразить справку;")
                print("exit - завершить работу с программой.")

            else:
                raise UnknownCommandError(command)

        except Exception as exc:
            logging.error(f"Ошибка: {exc}")
            print(exc, file=sys.stderr)
