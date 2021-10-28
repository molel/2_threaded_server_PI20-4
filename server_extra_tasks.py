import socket
from threading import Thread
from tkinter import *
from tkinter.font import Font
from time import sleep
from datetime import datetime
from keyboard import *


# функция получения информации из файла аутентификации и ее записи в соответствующий словарь
def read_logins(filename: str):
    with open(filename, "r") as file:
        try:
            for row in file:
                login = row.split(":")[0]  # разбивка записи на логин и пароль
                password = row.split(":")[1]
                Server.logins[login] = password[:-1]  # добавление записи в соответствующий словарь
        except Exception as e:
            print(str(e))
            pass


# функция добавления новой пары логин:пароль в файл аутентификации
def add_login(filename: str, login: str, password: str):
    with open(filename, "a") as file:
        file.write(login + ":" + password + "\n")


# функция добавления новой записи в файл логов
def write_log(filename: str, log: str):
    with open(filename, "a") as file:
        file.write(f"{datetime.now()}:\n{log}\n\n")


# генератор записей из файла логов
def logs_generator(filename: str):
    with open(filename, "r") as file:
        for row in file:
            yield row


# функция очистки файла
def clear_file(filename: str):
    open(filename, "w").close()


# класс сервера
class Server:
    LOGINS: str = "auth.txt"  # файл аутентификации
    LOG: str = "log.txt"  # файл логов
    BUTTON: str = "enter"  # кнопка для ввода
    paused_ports: list = []  # список приостановленных портов
    users: dict = dict()  # словарь подключенных (после успешного входа) соединений в виде conn: login
    logins: dict = dict()  # словарь аутентификации в виде login: password

    def __init__(self):
        # открытие сокета
        self.socket: socket = self.open_socket()

        # создание и настройка окна
        self.window: Tk = Tk()  # создание окна
        self.text_field: Text = Text(self.window)  # создание текстового поля
        self.input_field: Entry = Entry(self.window)  # создание поля ввода
        self.is_focused: BooleanVar = BooleanVar()  # переменная проверки фокусировки окна
        self.configure_window()

        # создание словаря вида команда: ссылка на функцию
        self.commands: dict = {
            "exit": self.exit,  # выход
            "pause": self.pause,  # приостановка порта
            "readlogs": self.read_logs,  # вывод логов
            "cllogs": self.clear_logs,  # очистка файла логов
            "cllogins": self.clear_logins  # очистка файла аутентификации
        }

        # создание всех необходимых потоков
        self.accept_thread: Thread = Thread(name="accept", target=self.accept, daemon=True)
        # принятие новых подключений
        self.console_thread: Thread = Thread(name="console", target=self.console, daemon=True)
        # обработка команд сервера
        self.accept_thread.start()
        self.console_thread.start()
        self.threads: list = []  # список потоков, работающих с пользователями

        # запуск окна
        self.window.mainloop()

    # функция открытия сокета
    @staticmethod
    def open_socket() -> socket:
        sock: socket = socket.socket()
        try:
            sock.bind(("127.0.0.1", 9091))
            sock.listen(2)
        except:
            sock.close()
            raise Exception("Can't start the server")
        return sock

    # функция настройки окна
    def configure_window(self):
        self.window.title("Server")
        self.window.configure(bg="#20805E")
        self.window.geometry("400x600")
        self.window.resizable(0, 0)
        self.window.bind('<FocusIn>', lambda _: self.is_focused.set(True))
        self.window.bind('<FocusOut>', lambda _: self.is_focused.set(False))

        self.text_field.configure(font=Font(size=9, weight="bold"), bg="#000000", fg="#FFFFFF", width=380, height=35)
        self.text_field.pack(side=TOP, padx=10, pady=10)

        self.input_field.configure(font=Font(size=9, weight="bold"), bg="#000000", fg="#FFFFFF", width=380)
        self.input_field.pack(side=TOP, padx=10, pady=10)
        self.input_field.focus_set()

    # функция принятия новых подключений
    def accept(self):
        while True:
            try:
                accept: tuple = self.socket.accept()
                conn: socket.socket = accept[0]
                addr: tuple = accept[1]
                write_log(Server.LOG, f"Установлено соединение с {addr[0]}, {addr[1]}")
                self.threads.append(
                    Thread(name=f"{conn};{addr}", target=self.request_login, args=[conn, addr, ], daemon=True).start())
            except:
                continue

    # функция запроса логина
    def request_login(self, conn: socket.socket, addr: tuple):
        conn.send("Введите логин:".encode())  # запрос логин
        login: str = conn.recv(2048).decode()  # получение логина

        write_log(Server.LOG, f"{addr[0]}, {addr[1]} ввел логин {login}")

        if login in Server.logins.keys():  # проверка существования логина
            self.request_password(conn, addr, login)  # запрос пароля
        else:
            self.request_new_password(conn, addr, login)  # запрос нового пароля

    # функция запроса нового пароля
    def request_new_password(self, conn: socket.socket, addr: tuple, login: str):
        conn.send("Задайте пароль:".encode())  # запрос нового пароля
        password: str = conn.recv(2048).decode()  # получение нового пароля

        write_log(Server.LOG, f"{addr[0]}, {addr[1]} задал пароль {password}")

        Server.logins[login] = password  # установка нового пароля
        conn.send("Вход выполнен".encode())  # сообщение о входе

        write_log(Server.LOG, f"{addr[0]}, {addr[1]} успешно подсоединился к чату")

        add_login(Server.LOGINS, login, password)  # запись в файл аутентификации
        Server.users[conn] = login  # добавление подключения
        self.accept_and_send(conn, addr)  # запуск работы с пользователем

    # функция запроса пароля
    def request_password(self, conn: socket.socket, addr: tuple, login: str):
        conn.send("Введите пароль:".encode())  # запрос пароля
        password: str = conn.recv(2048).decode()  # получение пароля

        write_log(Server.LOG, f"{addr[0]}, {addr[1]} ввел пароль {password}")

        if password == Server.logins[login]:  # проверка пароля
            conn.send("Вход выполнен".encode())  # сообщение о входе

            write_log(Server.LOG, f"{addr[0]}, {addr[1]} успешно подсоединился к чату")

            Server.users[conn] = login  # добавление подключения
            self.accept_and_send(conn, addr)  # запуск работы с пользователем
        else:
            self.request_password(conn, addr, login)  # повторный запрос пароля

    # функция работы с пользователем
    def accept_and_send(self, conn: socket.socket, addr: tuple):
        while True:
            if addr[1] not in self.paused_ports:  # проверка порта на приостановленность
                try:
                    data: str = conn.recv(2048).decode()  # получение сообщения

                    write_log(Server.LOG, f"{addr[0]}, {addr[1]} прислал сообщение:\n{data}\n")

                    self.send_all(data, Server.users[conn])  # отправка сообщения всем подключенным пользователям
                except ConnectionResetError:
                    Server.users.pop(conn)  # удаление подключения при разрыве соединения
                    break

    # функция отправки сообщения всем пользователям
    @staticmethod
    def send_all(message: str, user: str):
        for conn in Server.users.keys():  # обход каждого подключенного пользователя
            try:
                byte_array = bytearray(f"{user}:\n{message}\t({len(message)})".encode())
                conn.send(byte_array)  # отправка сообщения
            except:
                print(conn, " doesn't work")  # сообщение об ошибке

    # функция обработки команд сервера
    def console(self):
        while True:
            if is_pressed(self.BUTTON) and self.is_focused.get():
                # проверка на нажатие кнопки отправки и фокусировки окна
                try:
                    command: str = self.input_field.get()  # считывание команды
                    self.input_field.delete(0, END)  # очистка поля ввода
                    if command != "":  # проверка на непустую команду
                        if " " in command:  # проверка на наличие аргументов
                            arg: int = int(command.split(" ")[1])  # получение команды
                            command: str = command.split(" ")[0]  # получение аргумента
                            self.text_field.insert(END, command + " " + str(arg) + "\n")
                            # вывод команды в текстовое поле
                            self.commands[command](arg)  # обработка команды
                        else:
                            self.text_field.insert(END, command + "\n")  # вывод команды в текстовое поле
                            self.commands[command]()  # обработка команды
                except:
                    self.text_field.insert(END, "Команда не найдена\n")  # вывод об ошибке
                finally:
                    self.text_field.see(END)  # прокрутка текстового поля
                    sleep(0.5)

    # функция завершения работы
    def exit(self):
        self.socket.close()  # закрытие сокета
        self.window.quit()  # закрытие окна

    # функция приостановки порта
    def pause(self, port: str):
        self.paused_ports.append(port)  # добавление порта в список приостановленных

    # функция вывода файла логов
    def read_logs(self):
        for row in logs_generator(Server.LOG):  # вызов генератора логов
            self.text_field.insert(END, row)  # вывод лога в текстовое поле
        self.text_field.see(END)  # прокрутка текстового поля

    # функция очистки файла логов
    @staticmethod
    def clear_logs():
        clear_file(Server.LOG)

    # функция очистки файла аутентификации
    @staticmethod
    def clear_logins():
        clear_file(Server.LOGINS)


def main():
    read_logins(Server.LOGINS)  # получение содержимого файла аутентификации
    Server()  # запуск сервера


if __name__ == '__main__':
    main()
