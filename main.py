import socket
import ssl
import base64
import getpass
import logging
import smtplib

import sys

path = 'smtp_5.log'
path2 = 'smtp_5.log'


def send_notification(email, txt):
    sys.stderr = open(path, 'w')
    sender = '**********@yandex.ru'
    sender_password = '********'
    mail_lib = smtplib.SMTP_SSL('smtp.yandex.ru', 465)
    mail_lib.set_debuglevel(1)
    mail_lib.login(sender, sender_password)

    msg = 'From: %s\r\nTo: %s\r\nContent-Type: text/plain; charset="utf-8"\r\nSubject: %s\r\n\r\n' % (
        sender, email, 'Тема сообщения')
    msg += txt
    mail_lib.sendmail(sender, email, msg.encode('utf8'))
    mail_lib.quit()


# отправка сообщения на сервер и вывод ответа на экран
def send_to_server(client_socket, command, argument=""):
    client_socket.send((command + argument + '\r\n').encode())
    print("CLIENT: " + command + argument + "<CRLF>")
    logging.info("CLIENT: " + command + argument + "<CRLF>")


# получение ответа сервера вывод ответа на экран
def receive_from_server(client_socket):
    response = client_socket.recv(4096)
    print("Server: %s" % response.decode('utf-8'))
    logging.info("Server: %s" % response.decode('utf-8'))
    return response.decode('utf-8')


# подключение к серверу
def initialize_connection(host, port, ssl=False):
    client_socket = socket.socket()
    if ssl:
        client_socket = switch_on_SSL(client_socket)
    client_socket.connect((host, port))
    print("Connected to %s through %s port" % (host, port))
    logging.info("Connected to %s through %s port" % (host, port))
    return client_socket


# включение защищенного соединения
def switch_on_SSL(client_socket):
    return ssl.wrap_socket(client_socket)


# ввод текста сообщения, заканчивающий строкой из точки
def SMTP_text_input():
    text = ""
    while True:
        s = input()
        if s == '.':
            break
        text += s
    return text


# формирования заголовка сообщения
def SMTP_header_make(msg_from, msg_to, subject):
    return "FROM: " + msg_from + "\r\n" + \
           "TO: " + msg_to + "\r\n" + \
           "SUBJECT: " + subject


# авторизация по протоколу SMTP
def SMTP_authorization(client_socket, login, password):
    send_to_server(client_socket, "AUTH LOGIN")
    receive_from_server(client_socket)

    encoded_login = base64.b64encode(login.encode()).decode()
    send_to_server(client_socket, encoded_login)
    receive_from_server(client_socket)

    encoded_password = base64.b64encode(password.encode()).decode()
    send_to_server(client_socket, encoded_password)
    receive_from_server(client_socket)


# выход по протоколу SMTP
def SMTP_quit(client_socket):
    send_to_server(client_socket, "QUIT")
    receive_from_server(client_socket)
    client_socket.close()


# отправка сообщения по протоколу SMTP
def SMTP_send_message(host, port, login, password, msg_to, msg_subject, msg_text):
    client_socket = initialize_connection(host, port)
    receive_from_server(client_socket)

    send_to_server(client_socket, "EHLO ", "localhost")
    receive_from_server(client_socket)
    send_to_server(client_socket, 'HELP')
    receive_from_server(client_socket)
    # если требуется защищенное соединение
    if port != 25:
        send_to_server(client_socket, "STARTTLS")
        receive_from_server(client_socket)
        client_socket = switch_on_SSL(client_socket)

    SMTP_authorization(client_socket, login, password)

    send_to_server(client_socket, "MAIL FROM:", "<" + login + ">")
    receive_from_server(client_socket)

    send_to_server(client_socket, "RCPT TO:", "<" + msg_to + ">")
    receive_from_server(client_socket)

    send_to_server(client_socket, "DATA")
    receive_from_server(client_socket)

    msg_header = SMTP_header_make(login, msg_to, msg_subject)
    send_to_server(client_socket, msg_header)
    send_to_server(client_socket, "")
    send_to_server(client_socket, msg_text)
    send_to_server(client_socket, ".")
    receive_from_server(client_socket)

    SMTP_quit(client_socket)


# авторизация по протоколу POP
def POP_authorization(client_socket, login, password):
    send_to_server(client_socket, "USER ", login)
    receive_from_server(client_socket)

    send_to_server(client_socket, "PASS ", password)
    receive_from_server(client_socket)


# статус почтового ящика
def POP_get_email_status(client_socket):
    send_to_server(client_socket, "STAT")
    receive_from_server(client_socket)


# статус соединения
def POP_get_connection_status(client_socket):
    send_to_server(client_socket, "NOOP")
    receive_from_server(client_socket)


# получение сообщения
def POP_get_message(client_socket, msg_number):
    send_to_server(client_socket, "RETR ", msg_number)
    var = receive_from_server(client_socket)
    while var != '.\r\n':
        var = receive_from_server(client_socket)


# удаление сообщения
def POP_delete_message(client_socket, msg_number):
    send_to_server(client_socket, "DELE ", msg_number)
    receive_from_server(client_socket)


# вывод номеров сообщений и их размеров
def POP_list_messages(client_socket):
    send_to_server(client_socket, "LIST")
    var = receive_from_server(client_socket)
    while var != '.\r\n':
        var = receive_from_server(client_socket)


# выход по протоколу POP
def POP_quit(client_socket):
    send_to_server(client_socket, "QUIT")
    receive_from_server(client_socket)


def POP_menu():
    # host = "pop.gmail.com"
    host = "pop.yandex.ru"
    port = 995
    login = input("Login: ")
    password = getpass.getpass('Password: ')

    client_socket = None
    if port == 110:
        client_socket = initialize_connection(host, port)
    else:
        client_socket = initialize_connection(host, port, True)
    receive_from_server(client_socket)

    actions = {
        '1': "Авторизация",
        '2': "Статус соединения",
        '3': "Статус электронного ящика",
        '4': "Список сообщений",
        '5': "Получения сообщения",
        '6': "Удаления сообщения",
        '7': "Выход",
    }

    while True:
        for key in actions:
            print(key, " - ", actions[key])

        action = input()
        if action not in actions:
            continue
        if action == '7':
            POP_quit(client_socket)
            break
        if action == '1':
            POP_authorization(client_socket, login, password)
            continue
        if action == '2':
            POP_get_connection_status(client_socket)
            continue
        if action == '3':
            POP_get_email_status(client_socket)
            continue
        if action == '4':
            POP_list_messages(client_socket)
            continue
        msg_number = input("Номер сообщения: ")
        if action == '5':
            POP_get_message(client_socket, msg_number)
            continue
        if action == '6':
            POP_delete_message(client_socket, msg_number)
            continue


def SMTP_menu():
    # host = 'smtp.gmail.com'
    host = "smtp.yandex.ru"
    port = 587

    actions = {
        '1': "SEND MESSAGE",
        '2': "EXIT",
    }

    while True:
        for key in actions:
            print(key, " - ", actions[key])
        action = input()
        if action not in actions:
            continue
        if action == '1':
            send_notification("********@yandex.ru", "test_message")

        if action == '2':
            break


logging.basicConfig(filename="smtp_5.log", level=logging.DEBUG, filemode="w")

actions = {
    '1': "SMTP",
    '2': "POP",
    '3': "EXIT",
}

while True:
    for key in actions:
        print(key, " - ", actions[key])
    action = input()
    if action not in actions:
        continue
    if action == '1':
        SMTP_menu()
        continue
    if action == '2':
        POP_menu()
        continue
    if action == '3':
        break