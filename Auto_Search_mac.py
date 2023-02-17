import datetime
import io
import logging
import os
import re
import sys
import threading
import time
import encodings.idna

import openpyxl
import pandas
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QTextCursor, QColor, QPalette
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from netmiko import ConnectHandler


# logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%I:%M:%S %p', level=logging.DEBUG)


# 重写logging.Handlerm的emit函数
class StringLoggerHandler(logging.Handler):
    def __init__(self, stream):
        super().__init__()
        self.stream = stream

    def emit(self, record):
        self.stream.write(self.format(record))


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
    def __init__(self, ip='', username='', password='', secret='', port=22, session_log='', device_type='',
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
            hostname_ip = self.hostname + '_' + self.ip
            logger = logging.getLogger('red')
            logger.info(f'登录失败：{hostname_ip:<45} {e}')

    def send_command(self, command):
        self.login()
        if self.conn is None:
            return False
        try:
            self.conn.enable()
            for i in range(len(command)):
                self.conn.send_command(command_string=command[i], read_timeout=10)
            flag = True
        except Exception as e:
            logger = logging.getLogger('red')
            logger.info(f'错误：{self.hostname}_{self.ip} 输入命令获取信息异常，异常信息为：{e}')
            flag = False
        finally:
            self.conn.disconnect()
        return flag

    # 由于H3C v3版本取消回显限制需要进入配置模式较为麻烦，所以定制特殊的函数自动交互下一页动作。
    def send_command_custom(self, command):
        self.login()
        if self.conn is None:
            return False
        try:
            self.conn.enable()
            for i in range(len(command)):
                self.conn.write_channel(f'{command[i]}{self.conn.RETURN}')
                # 循环多次输入空格，自动下一页动作
                for _ in range(20):
                    time.sleep(0.2)
                    self.conn.write_channel(' ')
            flag = True
        except Exception as e:
            logger = logging.getLogger('red')
            logger.info(f'错误：{self.hostname}_{self.ip} 输入命令获取信息异常，异常信息为：{e}')
            flag = False
        finally:
            self.conn.disconnect()
            # 去掉分页符字符串，包括其中的乱码
            with open(self.session_log, 'r+') as f:
                more_str = '  ---- More ----\x1b[42D                                          \x1b[42D'
                text = f.read().replace(more_str, '')
                f.truncate(0)
                f.seek(0)
                f.write(text)
        return flag



class Ui_MainWindow(QtWidgets.QWidget):
    signal_textEide_upgrade = pyqtSignal(str, str)

    def setupUi(self, MainWindow):
        self.stream_black = io.StringIO()
        self.stream_red = io.StringIO()
        self.database = None
        self.mac_address = ''
        self.log_dir = './缓存文件/'
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 600)
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
        self.checkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox.setObjectName("checkBox")
        self.gridLayout.addWidget(self.checkBox, 2, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.toolButton.clicked.connect(self.load_config_xlxs)
        self.pushButton.clicked.connect(self.collect_mac_address)
        self.signal_textEide_upgrade.connect(self.textEdit_upgrade)

        # 启动日志记录器
        self.set_logger()
        threading.Thread(target=self.load_stream_black, daemon=True).start()
        threading.Thread(target=self.load_stream_red, daemon=True).start()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MAC地址搜索工具"))
        self.toolButton.setText(_translate("MainWindow", "..."))
        self.pushButton.setText(_translate("MainWindow", "搜索"))
        self.lineEdit.setPlaceholderText(_translate("MainWindow", "请选择设备信息文件"))
        self.lineEdit_2.setPlaceholderText(_translate("MainWindow", "请输入MAC地址：xxxx-xxxx-xxxx"))
        self.checkBox.setText(_translate("MainWindow", "在当前缓存中查找"))
        self.textEdit.setReadOnly(True)
        self.lineEdit_2.setText('f88c-2137-781c')

    # 加载用户密码xlsx文件，将对应数据加入到database中
    def load_config_xlxs(self):
        # 弹出对话框，选择文件路径
        filename, _ = QFileDialog.getOpenFileName(caption='请选择配置文件', filter='Excel files (*.xlsx)')
        # 判断文件路径为空则终止函数
        if filename == '': return
        # 将获取路径转换为windows格式路径
        windows_path = os.path.normpath(filename).replace('/', '\\')
        _, file_ext = os.path.splitext(windows_path)
        # 将路径文本设置到lineEdit文本框
        self.lineEdit.setText(windows_path)
        # 尝试打开xlsx文件，打开失败弹出错误对话框并终止函数
        try:
            workbook = openpyxl.load_workbook(filename)
        except:
            QMessageBox.about(ui, "错误", '账号密码表文件打开错误')
            return
        # 获取excel文件工作簿的第一个工作表
        sheet = workbook.worksheets[0]
        # 创建database为pandas.DataFrame数据类型
        self.database = pandas.DataFrame(columns=['hostname', 'ip', 'protocol', 'manufacturer', 'username', 'password',
                                                  'password_enable', 'flag', 'mac_data', 'thread', 'log_filename',
                                                  'version'])
        # 循环每行，将数据导入database
        for row, data in enumerate(sheet.rows):
            if row == 0:
                # 表格第一行为表头，需要跳过。
                continue
            new_row = f'Row{row}'
            # 将数据导入database，其中mac_data列为嵌套一个pandas.DataFrame数据类型，列索引为['mac', 'interface']
            self.database.loc[new_row] = [data[0].value, data[2].value, data[4].value, data[5].value, data[8].value,
                                          data[9].value, data[10].value, False,
                                          pandas.DataFrame(columns=['mac', 'interface']), None, None, data[6].value]
        self.logger_black.info('已导入设备信息')

    # 根据database中每一行的ip等信息，创建对应登录会话子线程,启动子线程，登录设备自动输入命令收集信息，将会话日志文件信息导入database中
    def collect_mac_address(self):
        if self.database is None:
            QMessageBox.about(ui, "错误", '请输入账号密码表文件')
            return
        # 获取mac地址输入框文本，去掉头尾空格，将格式转换为 xxxx-xxxx-xxxx
        self.mac_address = self.lineEdit_2.text().strip().replace('.', '-')
        # 判断是否为有效的mac地址
        mac_exp = '[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}'
        match = re.match(mac_exp, self.mac_address)
        if not match:
            QMessageBox.about(ui, '错误', '请输入正确格式的mac地址')
            return
        if not self.checkBox.isChecked():  # 判断是否根据当前缓存文件搜索，如果勾选则跳过搜集信息函数
            # 调用create_thread函数，根据database数据内容创建子线程
            self.create_thread()
            # 子线程调用start_thread函数启动子线程
            threading.Thread(target=self.start_thread, daemon=True).start()
        else:
            self.search_mac(self.mac_address)

    # 根据设备信息创建子线程，并加入database中
    def create_thread(self):
        for row, data in self.database.iterrows():
            ip = data.loc['ip']
            hostname = data.loc['hostname']
            protocol = data.loc['protocol']
            manufacturer = data.loc['manufacturer']
            if manufacturer == 'CISCO' and protocol == 'telnet':
                device_type = 'cisco_ios_telnet'
                port = 23
                command = ['show mac address-table', 'show running-config']
            elif manufacturer == 'H3C' and protocol == 'ssh':
                device_type = 'cisco_ios'
                port = 22
                command = ['show mac address-table', 'show running-config']
            elif manufacturer == 'H3C' and protocol == 'telnet':
                device_type = 'hp_comware_telnet'
                port = 23
                command = ['display mac-address', 'display current-configuration']
            elif manufacturer == 'H3C' and protocol == 'ssh':
                device_type = 'hp_comware'
                port = 22
                command = ['display mac-address', 'display current-configuration']
            else:
                continue
            username = '' if data.loc['username'] is None else data.loc['username']
            password = data.loc['password']
            password_enable = '' if data.loc['password_enable'] is None else data.loc['password_enable']
            version = data.loc['version']
            # 判断缓存文件目录是否存在，不存在则新建
            log_dir = self.log_dir
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            log_filename = f'{log_dir}{hostname}_{ip}.log'

            self.database.loc[row, 'log_filename'] = log_filename

            # 根据相应参数实例化TerminalClient，并创建对应子线程。
            client_class = TerminalClient(ip, username, password, secret=password_enable, port=port,
                                          session_log=log_filename, device_type=device_type, hostname=hostname)
            # thread = MyThread(client_class.send_command, args=(command,))
            if version == 'CMW-V3':
                thread = MyThread(client_class.send_command_custom, args=(command,))
            else:
                thread = MyThread(client_class.send_command, args=(command,))

            # client_class = Test_class
            # thread = MyThread(client_class.send_command, args=(client_class, command,))

            # 将子线程保存到database
            self.database.loc[row, 'thread'] = thread

    # 启动子线程，并限制最多同时只有10个子线程激活
    def start_thread(self):
        for _, (hostname, ip, _, _, _, _, _, _, _, thread, _, _) in self.database.iterrows():
            thread.start()
            hostname_ip = hostname + '_' + ip
            self.logger_black.info(f'开始登录：{hostname_ip:<45} 收集mac地址信息')
            while len(threading.enumerate()) >= 14:
                time.sleep(0.2)
        # 调用wait_thread函数，等待子线程结束，并整理相关数据
        self.wait_thread()
        # 调用search_mac函数，从database中搜索目标mac地址。
        self.search_mac(self.mac_address)

    # 将线程结果返回database的"flag",线程获取mac地址表成功返回True，否则返回False
    def wait_thread(self):
        for row, (hostname, ip, _, _, _, _, _, _, _, thread, _, _) in self.database.iterrows():
            thread.join()
            # 调用子线程的get_result()函数获取返回结果加入database，并根据结果输出日志信息
            self.database.loc[row, 'flag'] = self.database.loc[row, 'thread'].get_result()
            hostname_ip = hostname + '_' + ip
            if self.database.loc[row, 'flag']:
                self.logger_black.info(f'已完成：  {hostname_ip:<45} mac地址信息收集')
            else:
                self.logger_red.info(f'无法完成：{hostname_ip:<45} mac地址信息收集失败，登录或命令异常。')

            # 调用load_logfile()函数，将mac地址表信息导入database中，其中log_filename为登录设备会话保存的日志记录文件路径
            log_filename = self.database.loc[row, 'log_filename']
            self.load_mac_address_table(row, log_filename)

        # 调用statistic_thread函数，统计登录设备获取信息成功与否，并输出相关日志
        self.statistic_thread()

    # 统计子线程登录设备获取信息是否成功,输出相关日志信息
    def statistic_thread(self):
        successful = self.database[self.database['flag'].isin([True])]
        failure = self.database[self.database['flag'].isin([False])]
        failure_txt_list = ''
        for index, (hostname, ip, _, _, _, _, _, _, _, _, _, _) in failure.iterrows():
            failure_txt = f'\n{hostname}_{ip}'
            failure_txt_list += failure_txt
        if len(failure) == 0:
            self.logger_black.info('-' * 30 + f'\n已完成信息收集，成功个数：{len(successful)}，失败个数：{len(failure)}\n' + '-' * 30)
        else:
            self.logger_black.info(
                '-' * 30 + f'\n已完成信息收集，成功个数：{len(successful)}，失败个数：{len(failure)}，\n信息收集失败设备请手工搜索，如下：{failure_txt_list}\n' + '-' * 30)

    # 将登录设备获取的mac地址表信息导入database中
    def load_mac_address_table(self, row, log_filename):
        try:
            with open(log_filename, 'r') as f:
                cisco_exp = '\S+\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+\S+\s+([a-zA-Z0-9/,]+)( +[a-zA-Z0-9/]+){0,1}'
                h3c_exp = '([0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4})\s+\S+\s+\S+\s+(\S+)\s+\S+'
                text = f.read()
                # 正则匹配H3C格式的文本
                mac_list = re.findall(h3c_exp, text)
                if not mac_list:
                    # 正则匹配Cisco格式的文本
                    cisco_list = re.findall(cisco_exp, text)
                    for i in cisco_list:
                        # 去掉元组中空元素
                        i_without_empty = tuple(filter(lambda x: x != '', i))
                        mac_list.append((i_without_empty[0], i_without_empty[-1].strip()))
                # 去重,mac地址条目从不同vlan学习到可能有很多条，去重只保留一条数据
                mac_list = list(set(mac_list))
                # 循环将列表mac和interface数据放入database。
                for index, (mac, interface) in enumerate(mac_list):
                    # 将思科的mac地址格式转换为华三mac地址格式，同一格式为：xxxx-xxxx-xxxx
                    self.database.loc[row, 'mac_data'].loc[index] = [mac.replace('.', '-'), interface]
        except Exception as e:
            hostname_ip = os.path.splitext(os.path.basename(log_filename))[0]
            self.logger_red.info(f'打开文件:{hostname_ip:<45}失败')

    def search_mac(self, mac_address):
        # 从database中搜索mac地址为mac_address的数据，并将hostname、interface、mac添加到match_data列表
        match_data = []
        for _, (hostname, ip, _, _, _, _, _, flag, mac_data, _, _, _) in self.database.iterrows():
            # 获取符合条件的行
            match_mac = mac_data['mac'] == mac_address
            if match_mac.any:
                mac_data_row = mac_data.loc[match_mac]
                for _, (mac, interface) in mac_data_row.iterrows():
                    count = len(mac_data.loc[mac_data['interface'] == interface])
                    log_filename = f'{self.log_dir}{hostname}_{ip}.log'
                    interface_mode, interface_config = self.get_interface_mode(log_filename, interface)
                    match_data.append([hostname, ip, interface, mac, count, interface_mode, interface_config])
        if not match_data:
            self.logger_red.info('没有搜索到目标mac地址')
        else:
            now_time = datetime.datetime.now().strftime('%H:%M:%S')
            self.logger_black.info('-' * 15 + '已匹配的目标:' + '-' * 15 + now_time)
            self.logger_black.info(f'{"设备名称":<26}{"接口":<22}{"mac地址":<14}{"端口模式":<6}{"端口mac地址数量":<12}')
            best = []
            for hostname, ip, interface, mac, count, interface_mode, interface_config in match_data:
                self.logger_black.info(f'{hostname:<30}{interface:<23}{mac:<16}{interface_mode:<10}{count:<16}')
                if interface_mode == 'access':
                    best.append([hostname, ip, interface, mac, interface_mode, count, interface_config])
            if best:
                self.logger_red.info('-' * 14 + '最佳匹配的目标:' + '-' * 14)
                for hostname, ip, interface, mac, interface_mode, count, interface_config in best:
                    self.logger_black.info(f'{"设备名称":<26}{"接口":<22}{"mac地址":<14}{"端口模式":<6}{"端口下mac数量":<12}')
                    self.logger_black.info(f'{hostname:<30}{interface:<23}{mac:<16}{interface_mode:<10}{count:<16}')
                    self.logger_black.info(f'端口配置:\n{interface_config}')
                self.logger_red.info('请结合端口mac地址数量和配置综合判断')
            else:
                self.logger_black.info('-' * 30)
                self.logger_red.info('没有找到端口为access模式目标')

    # 获取接口类型是否为access接口，输入缓存文件名和接口，输出接口mode
    def get_interface_mode(self, log_filename, interface):
        # 因为思科mac地址表的端口号为简写，所以需要插入正则表达式所需字符".*?"以匹配配置文件中的配置
        try:
            index = re.search('\d', interface).start()
            interface = list(interface)
            interface.insert(index, '.*?')
            interface = ''.join(interface)
        except:
            self.logger_red.info('插入字符串失败')

        interface_exp = f'[#!]\n(interface {interface}\n(\s.*\n)+)[#!]'
        with open(log_filename, 'r') as f:
            text = f.read()
        inerface_re_ = re.findall(interface_exp, text)
        if inerface_re_:
            inerface_configre = inerface_re_[0][0]
            access_config_exp = 'port link-type trunk|switchport mode trunk'
            access_re = re.findall(access_config_exp, inerface_configre)
            if not access_re:
                interface_mode = 'access'
            else:
                interface_mode = 'trunk'
            return interface_mode, inerface_configre
        else:
            # 无法找到interface的配置，返回字符串None, None
            return 'Unknown', 'None'

    # 设置日志记录器,并循环读取stream中的日志信息，将日志信息打印到窗口textEidt
    def set_logger(self):
        self.logger_black = logging.getLogger('black')
        self.logger_black.setLevel(logging.INFO)
        console_handler = StringLoggerHandler(ui.stream_black)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(message)s\n')
        console_handler.setFormatter(formatter)
        self.logger_black.addHandler(console_handler)
        self.logger_red = logging.getLogger('red')
        self.logger_red.setLevel(logging.INFO)
        console_handler = StringLoggerHandler(ui.stream_red)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(message)s\n')
        console_handler.setFormatter(formatter)
        self.logger_red.addHandler(console_handler)

    def load_stream_black(self):
        while True:
            if self.stream_black.tell() > 0:
                lock.acquire()
                self.stream_black.seek(0)  # 移动至read_pos位置
                log_mess = self.stream_black.getvalue()  # 从当前位置往后读取数据
                self.stream_black.truncate()  # 删除已读取的流数据
                lock.release()
                self.signal_textEdit_upgrade(log_mess)
                time.sleep(0.3)

    def load_stream_red(self):
        while True:
            if self.stream_red.tell() > 0:
                lock.acquire()
                self.stream_red.seek(0)  # 移动至read_pos位置
                log_mess = self.stream_red.getvalue()  # 从当前位置往后读取数据
                self.stream_red.truncate()  # 删除已读取的流数据
                lock.release()
                self.signal_textEdit_upgrade(log_mess, color='red')
                time.sleep(0.3)

    # 设置函数链接主线程信号
    def signal_textEdit_upgrade(self, message, color='black'):
        self.signal_textEide_upgrade.emit(message, color)

    # 信号槽函数
    def textEdit_upgrade(self, log_mess, color):
        lock.acquire()
        palette = self.textEdit.palette()
        palette.setColor(QPalette.Text, QColor(color))
        self.textEdit.setPalette(palette)
        self.textEdit.moveCursor(QTextCursor.End)
        self.textEdit.insertPlainText(log_mess)
        self.textEdit.moveCursor(QTextCursor.End)
        lock.release()


if __name__ == "__main__":
    filename = r'zsyk-oz-out.xlsx'
    lock = threading.Lock()
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
