import socket
from threading import Thread
from tkinter import *
from tkinter.font import Font
from time import sleep
from keyboard import *


# класс Клиента
class Client:
    BUTTON: str = "enter"  # кнопка для ввода

    def __init__(self):
        # открытие сокета
        self.socket: socket.socket = self.open_socket()

        # создание и настройка окна
        self.window: Tk = Tk()  # создание окна
        self.text_field: Text = Text(self.window)  # создание текстового поля
        self.input_field: Entry = Entry(self.window)  # создание поля ввода
        self.is_focused: BooleanVar = BooleanVar()  # переменная проверки фокусировки окна
        self.configure_window()

        # создание всех необходимых потоков
        self.accept_thread: Thread = Thread(name="accept", target=self.accept)
        # принятие сообщений
        self.send_thread: Thread = Thread(name="send", target=self.send)
        # отправка сообщений
        self.accept_thread.start()
        self.send_thread.start()

        # запуск окна
        self.window.mainloop()

    # функция открытия сокета
    @staticmethod
    def open_socket() -> socket.socket:
        sock: socket.socket = socket.socket()
        try:
            sock.connect(("127.0.0.1", 9091))
        except:
            sock.close()
            raise "Can't connect to the server"
        return sock

    # функция настройки окна
    def configure_window(self):
        self.window.title("Client")
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

    # функция принятие сообщений
    def accept(self):
        while True:
            try:
                data: str = self.socket.recv(2048).decode()
                # получения сообщения и его разбивка на пользователя и само сообщение
                # user: str = data[0]  # получение пользователя
                # message: str = "".join(data[1:])  # получения сообщения
                if data == "Введите логин:" or \
                        data == "Введите пароль:" or \
                        data == "Задайте пароль:" or \
                        data == "Вход выполнен":  # проверка на служебное сообщение
                    self.text_field.insert(END, data + "\n")  # вывод сообщения
                else:
                    self.text_field.insert(END, data + "\n")  # вывод сообщения
            except:
                sleep(0.5)
            finally:
                self.text_field.see(END)  # прокрутка текстового поля

    def send(self):
        while True:
            if is_pressed(self.BUTTON) and self.is_focused.get():
                # проверка на нажатие кнопки отправки и фокусировки окна
                data: str = self.input_field.get()  # считывание сообщения
                self.input_field.delete(0, END)  # очистка поля ввода
                try:
                    self.socket.send(bytearray(data.encode()))  # отправка сообщения
                except:
                    print("Send ERROR")  # вывод сообщения об ошибке
                finally:
                    sleep(1)


def main():
    Client()  # запуск клиента


if __name__ == '__main__':
    main()
