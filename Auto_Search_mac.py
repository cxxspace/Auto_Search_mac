import logging
import os
import re
import sys
import threading
import time

import openpyxl
import pandas
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from netmiko import ConnectHandler
from PyQt5 import QtCore, QtWidgets

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%I:%M:%S %p', level=logging.DEBUG)


class MyThread(threading.Thread):
    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args
        self.daemon = True

    def run(self):
        self.result = self.func(*self.args)  # 在执行函数的同时，把结果赋值给result,
        # 然后通过get_result函数获取返回的结果

    def get_result(self):
        try:
            return self.result
        except Exception as e:
            return None


class TerminalClient:
    def __init__(self, ip='', username='', password='', secret='', port=22, session_log=r'./缓存文件/', device_type='',
                 hostname=''):
        self.ip = ip
        self.hostname = hostname
        self.username = username
        self.password = password
        self.secret = secret
        self.port = port
        self.device_type = device_type
        self.session_log = session_log
        self.dev = {'host': self.ip,
                    'username': self.username,
                    'password': self.password,
                    'secret': self.secret,
                    'port': self.port,
                    'session_log': self.session_log,
                    'device_type': self.device_type,
                    }
        self.conn = None

    def login(self):
        try:
            self.conn = ConnectHandler(**self.dev)
        except Exception as e:
            logging.debug('登录失败:')

    def send_command(self, command):
        self.login()
        if self.conn is None:
            return False
        self.conn.send_command(command_string=command, read_timeout=10)
        return True


class Test_class:
    def __init__(self, ip='', username='', password='', secret='', port=22, log_filename=r'./缓存文件/', device_type='',
                 hostname=''):
        self.ip = ip
        self.hostname = hostname
        self.username = username
        self.password = password
        self.secret = secret
        self.port = port
        self.device_type = device_type
        self.log_filename = log_filename
        self.dev = {'host': self.ip,
                    'username': self.username,
                    'password': self.password,
                    'secret': self.secret,
                    'port': self.port,
                    'session_log': self.log_filename,
                    'device_type': self.device_type,
                    }
        self.conn = None

    def send_command(self, command):
        time.sleep(5)
        return True


class Ui_MainWindow(QtWidgets.QWidget):

    def setupUi(self, MainWindow):
        self.database = None
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.toolButton = QtWidgets.QToolButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolButton.sizePolicy().hasHeightForWidth())
        self.toolButton.setSizePolicy(sizePolicy)
        self.toolButton.setMinimumSize(QtCore.QSize(80, 20))
        self.toolButton.setMaximumSize(QtCore.QSize(80, 20))
        self.toolButton.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.toolButton.setObjectName("toolButton")
        self.gridLayout.addWidget(self.toolButton, 0, 4, 1, 1)
        self.textEdit = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit.setObjectName("textEdit")
        self.gridLayout.addWidget(self.textEdit, 1, 0, 1, 5)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 2, 1, 1, 1)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_2.sizePolicy().hasHeightForWidth())
        self.lineEdit_2.setSizePolicy(sizePolicy)
        self.lineEdit_2.setMinimumSize(QtCore.QSize(250, 0))
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.gridLayout.addWidget(self.lineEdit_2, 2, 2, 1, 1)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setMinimumSize(QtCore.QSize(30, 0))
        self.pushButton.setMaximumSize(QtCore.QSize(80, 16777215))
        self.pushButton.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 2, 4, 1, 1)
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setObjectName("lineEdit")
        self.gridLayout.addWidget(self.lineEdit, 0, 0, 1, 3)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.toolButton.clicked.connect(self.load_config_xlxs)
        self.pushButton.clicked.connect(self.collect_mac_address)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MAC地址搜索工具"))
        self.toolButton.setText(_translate("MainWindow", "..."))
        self.pushButton.setText(_translate("MainWindow", "搜索"))
        self.lineEdit.setPlaceholderText(_translate("MainWindow", "请选择账号密码表文件"))
        self.lineEdit_2.setPlaceholderText(_translate("MainWindow", "请输入MAC地址：xxxx-xxxx-xxxx"))

    def load_config_xlxs(self):
        filename, _ = QFileDialog.getOpenFileName(caption='请选择配置文件', filter='Excel files (*.xlsx)')
        if filename == '': return
        windows_path = os.path.normpath(filename).replace('/', '\\')
        _, file_ext = os.path.splitext(windows_path)
        self.lineEdit.setText(windows_path)
        try:
            workbook = openpyxl.load_workbook(filename)
        except:
            QMessageBox.about(ui, "错误", '账号密码表文件打开错误')
            return
        sheet = workbook.worksheets[0]
        self.database = pandas.DataFrame(columns=['hostname', 'ip', 'protocol', 'manufacturer', 'username', 'password',
                                                  'password_enable', 'flag', 'mac_data', 'thread', 'log_filename'])
        for row, data in enumerate(sheet.rows):
            if row == 0:
                # 表格第一行为表头，需要跳过。
                continue
            new_row = f'Row{row}'
            self.database.loc[new_row] = [data[0].value, data[2].value, data[4].value, data[5].value, data[8].value,
                                          data[9].value,
                                          data[10].value, False, None, None, None]
        print(self.database)

    def collect_mac_address(self):
        if self.database is None:
            QMessageBox.about(ui, "错误", '请输入账号密码表文件')
            return
        for row, data in self.database.iterrows():
            ip = data.loc['ip']
            hostname = data.loc['hostname']
            protocol = data.loc['protocol']
            manufacturer = data.loc['manufacturer']
            if manufacturer == 'CISCO' and protocol == 'telnet':
                device_type = 'cisco_ios_telnet'
                port = 23
                command = 'show mac address-table'
            elif manufacturer == 'H3C' and protocol == 'ssh':
                device_type = 'cisco_ios'
                port = 22
                command = 'show mac address-table'
            elif manufacturer == 'H3C' and protocol == 'telnet':
                device_type = 'hp_comware_telnet'
                port = 23
                command = 'display mac-address'
            elif manufacturer == 'H3C' and protocol == 'ssh':
                device_type = 'hp_comware'
                port = 22
                command = 'display mac-address'
            else:
                continue
            username = data.loc['username']
            password = data.loc['password']
            password_enable = data.loc['password_enable']
            log_filename = f'./缓存文件/{hostname}_{ip}.log'
            self.database.loc[row, 'log_filename'] = log_filename
            # client_class = TerminalClient(ip, username, password, secret=password_enable, port=port,
            #                               session_log=log_filename, device_type=device_type, hostname=hostname)
            # thread = MyThread(client_class.send_command, args=(client_class,command,))
            client_class = Test_class
            thread = MyThread(client_class.send_command, args=(client_class, command,))

            self.database.loc[row, 'thread'] = thread

        # 启动子线程，并限制最多同时只能有10个线程激活
        for thread in self.database['thread']:
            thread.start()
            while len(threading.enumerate()) >= 11:
                time.sleep(0.2)

        # 将线程结果返回database的"flag",线程获取mac地址表成功返回True，否则返回False
        for row, _ in self.database.iterrows():
            self.database.loc[row, 'thread'].join()
            # 调用子线程的get_result()函数获取返回结果
            self.database.loc[row, 'flag'] = self.database.loc[row, 'thread'].get_result()
            log_filename = self.database.loc[row, 'log_filename']
            # 调用load_logfile（）函数，将mac地址表信息导入database
            self.load_logfile(row, log_filename)

    def load_logfile(self, row, log_filename):
        with open(log_filename, 'r') as f:
            cisco_exp = '\S+\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+\S+\s+(\S+)'
            h3c_exp = '([0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4})\s+\S+\s+\S+\s+(\S+)\s+\S+'
            text = f.read()
            mac_list = re.findall(h3c_exp, text)
            if mac_list == []:
                mac_list = re.findall(cisco_exp, text)
                # 将思科的mac地址格式转换为华三mac地址格式，同一格式为：xxxx-xxxx-xxxx
                for index, (mac, interface) in enumerate(mac_list):
                    mac_list[index] = (mac.replace('.', '-'), interface)
            mac_data = pandas.DataFrame(mac_list, columns=['mac', 'interface'])
            self.database.loc[row, 'mac_data'] = mac_data

    def search_mac(self):
        mac_address = self.lineEdit_2.text().rstrip()
        mac_exp = '[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}'
        match = re.match(mac_exp, mac_address)
        if not match:
            QMessageBox.about('错误', '请输入正确格式的mac地址')
            return
        match_data = []
        for hostname, _, _, _, _, _, _, flag, mac_data, _, _ in self.database.iterrows():
            mac_data_row = mac_data.loc[mac_data['mac'] == mac_address]
            interface = mac_data.loc[mac_data_row, 'interface']
            match_data.append([hostname, interface, mac_address])
        print(match_data)


if __name__ == "__main__":
    filename = r'zsyk-oz-out.xlsx'
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
