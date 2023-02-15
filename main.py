import re

import pandas

cisco_exp = '\S+\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+\S+\s+(\S+)'
h3c_exp = '([0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4})\s+\S+\s+\S+\s+(\S+)\s+\S+'
path1 = r'C:\Users\SYSTEC-00058\Desktop\python代码\Auto_Search_mac\test\h3c.txt'
path2 = r'C:\Users\SYSTEC-00058\Desktop\python代码\Auto_Search_mac\test\cisco.txt'
a = [path1, path2]

database = pandas.DataFrame(columns=['hostname', 'ip', 'protocol', 'manufacturer', 'username', 'password',
                                     'password_enable', 'flag', 'mac_data', 'thread', 'log_filename'])
mac_data = pandas.DataFrame(columns=['mac', 'interface'])
database.loc['Row1'] = ['Center-Cisco4507', '200.100.100.1', 'telnet', 'CISCO', 'zsyk4507-1', 'zsykCISCO2017-1',
                        'zsykCISCO2017-1', True, mac_data, None, None]
database.loc['Row2'] = ['Center-', '200.100.100.2', 'telnet', 'CISCO', 'zsyk4507-1', 'zsykCISCO2017-1',
                        'zsykCISCO2017-1', True, mac_data, None, None]

for index, path in enumerate(a):
    with open(path, 'r') as f:
        text = f.read()
        mac_list = re.findall(h3c_exp, text)
        row = f'Row{index + 1}'
        if mac_list == []:
            mac_list = re.findall(cisco_exp, text)
            for i, (mac, interface) in enumerate(mac_list):
                mac_list[i] = (mac.replace('.', '-'), interface)
                database.loc[row, 'mac_data'].loc[i] = [mac,interface]
        # mac_data = pandas.DataFrame(mac_list, columns=['mac', 'interface'])

print(database)
print(database.loc['Row1','mac_data'])
print(database.loc['Row2','mac_data'])

def search_mac():
    mac_address = 'd867-d9dc-467f'
    mac_exp = '[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}'
    match = re.match(mac_exp, mac_address)
    if not match:
        print('没有找到')
        return
    match_data = []
    for hostname, _, _, _, _, _, _, flag, mac_data, _, _ in database.iterrows():
        mac_data_row = mac_data.loc[mac_data['mac'] == mac_address]
        interface = mac_data.loc[mac_data_row, 'interface']
        match_data.append([hostname, interface, mac_address])
    print(match_data)
