import re

import pandas

cisco_exp = '\S+\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+\S+\s+(\S+)'
h3c_exp = '([0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4})\s+\S+\s+\S+\s+(\S+)\s+\S+'
path1 = r'D:\Users\CXX\Desktop\python项目\Auto_Search_mac\test\h3c.txt'
path2 = r'D:\Users\CXX\Desktop\python项目\Auto_Search_mac\test\cisco.txt'
a = [path1, path2]

database = pandas.DataFrame(columns=['hostname', 'ip', 'protocol', 'manufacturer', 'username', 'password',
                                     'password_enable', 'flag', 'mac_data', 'thread', 'log_filename'])
# mac_data = pandas.DataFrame(columns=['mac', 'interface'])
database.loc['Row1'] = ['Center-Cisco4507', '200.100.100.1', 'telnet', 'CISCO', 'zsyk4507-1', 'zsykCISCO2017-1',
                        'zsykCISCO2017-1', True, pandas.DataFrame(columns=['mac', 'interface']), None, None]
database.loc['Row2'] = ['Center-', '200.100.100.2', 'telnet', 'CISCO', 'zsyk4507-1', 'zsykCISCO2017-1',
                        'zsykCISCO2017-1', True, pandas.DataFrame(columns=['mac', 'interface']), None, None]

for index, path in enumerate(a):
    with open(path, 'r') as f:
        text = f.read()
        mac_list = re.findall(h3c_exp, text)
        row = f'Row{index + 1}'
        if not mac_list:
            mac_list = re.findall(cisco_exp, text)
        for i, (mac, interface) in enumerate(mac_list):
            # mac_list[i] = (mac.replace('.', '-'), interface)
            database.loc[row, 'mac_data'].loc[i] = [mac.replace('.', '-'), interface]
        # mac_data = pandas.DataFrame(mac_list, columns=['mac', 'interface'])


# print(database)
# print(database.loc['Row1','mac_data'])
# print(database.loc['Row2','mac_data'])

def search_mac():
    mac_address = 'd867.d9dc.467f'.strip().replace('.','-')
    mac_exp = '[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}'
    search = re.match(mac_exp, mac_address)
    if not search:
        print('输入错误')
        return
    match_data = []
    for _, (hostname, _, _, _, _, _, _, flag, mac_data, _, _) in database.iterrows():
        match = mac_data['mac'] == mac_address
        if match.any:
            mac_data_row = mac_data.loc[match]
            for _, (mac, interface) in mac_data_row.iterrows():
                match_data.append([hostname, interface, mac])
    for a in match_data:
        print(a)


search_mac()
