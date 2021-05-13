import os
import sys
import redis
import bios
import shutil
import netifaces


def __get_own_ip() -> str:
    if 'POD_IP' in os.environ:
        myip = os.environ['POD_IP']
    else:
        # with open('/etc/hosts') as f:
        #     hosts = f.read()
        # #print(hosts)
        # myip = hosts.splitlines()[-1].split()[0]
        myip = netifaces.ifaddresses('eth0')[2][0]['addr']
    return myip


def __publish_ip(name: str, ip: str):
    client = redis.Redis(host="redis", port=6379)

    client.set(name, ip)
    client.publish(name, ip)


def __get_ip(name: str) -> str:
    client = redis.Redis(host="redis", port=6379)
    p = client.pubsub()
    p.subscribe(name)
    ip = client.get(name)
    if not ip:
        print("waiting for", name, "...")
        while True:
            message = p.get_message()
            if message and not message['data'] == 1:
                message = message['data'].decode('utf-8')
                ip = message
                break
    else:
        ip = ip.decode('utf-8')
    return ip


def init_mme():
    mme_ip = __get_own_ip()
    print(f"mme_ip {mme_ip}")
    __publish_ip('mme_ip', mme_ip)
    
    hss_ip = __get_ip('hss_ip')
    sgwc_ip = __get_ip('sgwc_ip')
    smf_ip = __get_ip('smf_ip')
    
    print(f"hss_ip {hss_ip}")
    print(f"sgwc_ip {sgwc_ip}")
    print(f"smf_ip {smf_ip}")

    config = bios.read('/5gs/etc/open5gs/mme.yaml')
    config['mme']['s1ap'] = {'addr': mme_ip}
    config['mme']['gtpc'] = {'addr': mme_ip}
    config['sgwc']['gtpc'] = {'addr': sgwc_ip}
    config['smf']['gtpc'] = {'addr': smf_ip}
    bios.write('/5gs/etc/open5gs/mme.yaml', config, file_type='yaml')
    
    file_in = "/5gs/etc/freeDiameter/mme.conf"
    file_out = "/5gs/etc/freeDiameter/mme.conf.new"
    with open(file_in, "r") as f:
        lines = f.readlines()
    with open(file_out, "w") as f:
        for line in lines:
            if line.startswith('\n'):
                continue
            elif line.startswith('#'):
                continue
            elif line.startswith("ListenOn"):
                f.write('ListenOn = "{mme_ip}";\n'.format(mme_ip=mme_ip))
                continue
            elif line.startswith("ConnectPeer"):
                f.write('ConnectPeer = "hss.localdomain" { ConnectTo = "%s"; No_TLS; };\n' % hss_ip)
                continue
            else:
                f.write(line)
        f.write('\n')
        f.flush()
    shutil.copyfile(file_out, file_in)
    with open(file_in, "r") as f:
        print(f.read())


def init_sgwc():
    sgwc_ip = __get_own_ip()
    print(f"sgwc_ip {sgwc_ip}")
    __publish_ip('sgwc_ip', sgwc_ip)

    sgwu_ip = __get_ip('sgwu_ip')
    print(f"sgwu_ip {sgwu_ip}")

    config = bios.read('/5gs/etc/open5gs/sgwc.yaml')
    config['sgwc']['gtpc'] = {'addr': sgwc_ip}
    config['sgwc']['pfcp'] = {'addr': sgwc_ip}
    config['sgwu']['pfcp'] = {'addr': sgwu_ip}
    bios.write('/5gs/etc/open5gs/sgwc.yaml', config, file_type='yaml')


def init_smf():
    smf_ip = __get_own_ip()
    print(f"smf_ip {smf_ip}")
    __publish_ip('smf_ip', smf_ip)

    nrf_ip = __get_ip('nrf_ip')
    upf_ip = __get_ip('upf_ip')
    pcrf_ip = __get_ip('pcrf_ip')
    print(f"nrf_ip {nrf_ip}")
    print(f"upf_ip {upf_ip}")
    print(f"pcrf_ip {pcrf_ip}")

    config = bios.read('/5gs/etc/open5gs/smf.yaml')
    config['smf']['sbi'] = {'addr': smf_ip, 'port': 7777}
    config['smf']['pfcp'] = {'addr': smf_ip}
    config['smf']['gtpc'] = {'addr': smf_ip}
    config['smf']['gtpu'] = {'addr': smf_ip}
    config['nrf']['sbi'] = {'addr': nrf_ip, 'port': 7777}
    config['upf']['pfcp'] = {'addr': upf_ip}
    bios.write('/5gs/etc/open5gs/smf.yaml', config, file_type='yaml')

    file_in = "/5gs/etc/freeDiameter/smf.conf"
    file_out = "/5gs/etc/freeDiameter/smf.conf.new"
    with open(file_in, "r") as f:
        lines = f.readlines()
    with open(file_out, "w") as f:
        for line in lines:
            if line.startswith('\n'):
                continue
            elif line.startswith('#'):
                continue
            elif line.startswith("ListenOn"):
                f.write('ListenOn = "{smf_ip}";\n'.format(smf_ip=smf_ip))
                continue
            elif line.startswith("ConnectPeer"):
                f.write('ConnectPeer = "pcrf.localdomain" { ConnectTo = "%s"; No_TLS; };\n' % pcrf_ip)
                continue
            else:
                f.write(line)
        f.write('\n')
        f.flush()
    shutil.copyfile(file_out, file_in)
    with open(file_in, "r") as f:
        print(f.read())


def init_amf():
    amf_ip = __get_own_ip()
    print(f"amf_ip {amf_ip}")
    __publish_ip('amf_ip', amf_ip)
    nrf_ip = __get_ip('nrf_ip')
    print(f"nrf_ip {nrf_ip}")

    config = bios.read('/5gs/etc/open5gs/amf.yaml')
    config['amf']['sbi'] = {'addr': amf_ip, 'port': 7777}
    config['amf']['ngap'] = {'addr': amf_ip}
    config['nrf']['sbi'] = {'addr': nrf_ip, 'port': 7777}
    bios.write('/5gs/etc/open5gs/amf.yaml', config, file_type='yaml')


def init_sgwu():
    sgwu_ip = __get_own_ip()
    print(f"sgwu_ip {sgwu_ip}")
    __publish_ip('sgwu_ip', sgwu_ip)

    config = bios.read('/5gs/etc/open5gs/sgwu.yaml')
    config['sgwu']['pfcp'] = {'addr': sgwu_ip}
    config['sgwu']['gtpu'] = {'addr': sgwu_ip}
    bios.write('/5gs/etc/open5gs/sgwu.yaml', config, file_type='yaml')


def init_upf():
    upf_ip = __get_own_ip()
    print(f"upf_ip {upf_ip}")
    __publish_ip('upf_ip', upf_ip)

    config = bios.read('/5gs/etc/open5gs/upf.yaml')
    config['upf']['pfcp'] = {'addr': upf_ip}
    config['upf']['gtpu'] = {'addr': upf_ip}
    bios.write('/5gs/etc/open5gs/upf.yaml', config, file_type='yaml')


def init_hss():
    hss_ip = __get_own_ip()
    print(f"hss_ip {hss_ip}")
    __publish_ip('hss_ip', hss_ip)

    mme_ip = __get_ip('mme_ip')
    print(f"mme_ip {mme_ip}")
    
    config = bios.read('/5gs/etc/open5gs/hss.yaml')
    config['db_uri'] = 'mongodb://mongodb/open5gs'
    bios.write('/5gs/etc/open5gs/hss.yaml', config, file_type='yaml')

    file_in = "/5gs/etc/freeDiameter/hss.conf"
    file_out = "/5gs/etc/freeDiameter/hss.conf.new"
    with open(file_in, "r") as f:
        lines = f.readlines()
    with open(file_out, "w") as f:
        for line in lines:
            if line.startswith('\n'):
                continue
            elif line.startswith('#'):
                continue
            elif line.startswith("ListenOn"):
                f.write('ListenOn = "{hss_ip}";\n'.format(hss_ip=hss_ip))
                continue
            elif line.startswith("ConnectPeer"):
                f.write('ConnectPeer = "mme.localdomain" { ConnectTo = "%s"; No_TLS; };\n' % mme_ip)
                continue
            else:
                f.write(line)
        f.write('\n')
        f.flush()
    shutil.copyfile(file_out, file_in)
    with open(file_in, "r") as f:
        print(f.read())


def init_pcrf():
    pcrf_ip = __get_own_ip()
    print(f"pcrf_ip {pcrf_ip}")
    __publish_ip('pcrf_ip', pcrf_ip)

    smf_ip = __get_ip('smf_ip')
    print(f"smf_ip {smf_ip}")

    config = bios.read('/5gs/etc/open5gs/pcrf.yaml')
    config['db_uri'] = 'mongodb://mongodb/open5gs'
    bios.write('/5gs/etc/open5gs/pcrf.yaml', config, file_type='yaml')

    file_in = "/5gs/etc/freeDiameter/pcrf.conf"
    file_out = "/5gs/etc/freeDiameter/pcrf.conf.new"
    with open(file_in, "r") as f:
        lines = f.readlines()
    with open(file_out, "w") as f:
        for line in lines:
            if line.startswith('\n'):
                continue
            elif line.startswith('#'):
                continue
            elif line.startswith("ListenOn"):
                f.write('ListenOn = "{pcrf_ip}";\n'.format(pcrf_ip=pcrf_ip))
                continue
            elif line.startswith("ConnectPeer"):
                f.write('ConnectPeer = "smf.localdomain" { ConnectTo = "%s"; No_TLS; };\n' % smf_ip)
                continue
            else:
                f.write(line)
        f.write('\n')
        f.flush()
    shutil.copyfile(file_out, file_in)
    with open(file_in, "r") as f:
        print(f.read())


def init_nrf():
    nrf_ip = __get_own_ip()
    print(f"nrf_ip {nrf_ip}")
    __publish_ip('nrf_ip', nrf_ip)

    config = bios.read('/5gs/etc/open5gs/nrf.yaml')
    config['db_uri'] = 'mongodb://mongodb/open5gs'
    config['nrf']['sbi'] = {'addr': nrf_ip, 'port': 7777}
    bios.write('/5gs/etc/open5gs/nrf.yaml', config, file_type='yaml')


def init_ausf():
    ausf_ip = __get_own_ip()
    print(f"ausf_ip {ausf_ip}")
    __publish_ip('ausf_ip', ausf_ip)
    nrf_ip = __get_ip('nrf_ip')
    print(f"nrf_ip {nrf_ip}")

    config = bios.read('/5gs/etc/open5gs/ausf.yaml')
    config['ausf']['sbi'] = {'addr': ausf_ip, 'port': 7777}
    config['nrf']['sbi'] = {'addr': nrf_ip, 'port': 7777}
    bios.write('/5gs/etc/open5gs/ausf.yaml', config, file_type='yaml')


def init_udm():
    udm_ip = __get_own_ip()
    print(f"udm_ip {udm_ip}")
    __publish_ip('udm_ip', udm_ip)
    nrf_ip = __get_ip('nrf_ip')
    print(f"nrf_ip {nrf_ip}")

    config = bios.read('/5gs/etc/open5gs/udm.yaml')
    config['udm']['sbi'] = {'addr': udm_ip, 'port': 7777}
    config['nrf']['sbi'] = {'addr': nrf_ip, 'port': 7777}
    bios.write('/5gs/etc/open5gs/udm.yaml', config, file_type='yaml')


def init_pcf():
    pcf_ip = __get_own_ip()
    print(f"pcf_ip {pcf_ip}")
    __publish_ip('pcf_ip', pcf_ip)
    nrf_ip = __get_ip('nrf_ip')
    print(f"nrf_ip {nrf_ip}")

    config = bios.read('/5gs/etc/open5gs/pcf.yaml')
    config['db_uri'] = 'mongodb://mongodb/open5gs'
    config['pcf']['sbi'] = {'addr': pcf_ip, 'port': 7777}
    config['nrf']['sbi'] = {'addr': nrf_ip, 'port': 7777}
    bios.write('/5gs/etc/open5gs/pcf.yaml', config, file_type='yaml')


def init_nssf():
    nssf_ip = __get_own_ip()
    print(f"nssf_ip {nssf_ip}")
    __publish_ip('nssf_ip', nssf_ip)
    nrf_ip = __get_ip('nrf_ip')
    print(f"nrf_ip {nrf_ip}")

    config = bios.read('/5gs/etc/open5gs/nssf.yaml')
    config['nssf']['sbi'] = {'addr': nssf_ip, 'port': 7777}
    config['nrf']['sbi'] = {'addr': nrf_ip, 'port': 7777}
    bios.write('/5gs/etc/open5gs/nssf.yaml', config, file_type='yaml')


def init_udr():
    udr_ip = __get_own_ip()
    print(f"udr_ip {udr_ip}")
    __publish_ip('udr_ip', udr_ip)
    nrf_ip = __get_ip('nrf_ip')
    print(f"nrf_ip {nrf_ip}")

    config = bios.read('/5gs/etc/open5gs/udr.yaml')
    config['db_uri'] = 'mongodb://mongodb/open5gs'
    config['udr']['sbi'] = {'addr': udr_ip, 'port': 7777}
    config['nrf']['sbi'] = {'addr': nrf_ip, 'port': 7777}
    bios.write('/5gs/etc/open5gs/udr.yaml', config, file_type='yaml')


def init_gnb():
    gnb_ip = __get_own_ip()
    print(f"gnb_ip {gnb_ip}")
    __publish_ip('gnb_ip', gnb_ip)
    amf_ip = __get_ip('amf_ip')
    print(f"amf_ip {amf_ip}")

    config = bios.read('config/open5gs-gnb.yaml')
    config['linkIp'] = gnb_ip
    config['ngapIp'] = gnb_ip
    config['gtpIp'] = gnb_ip
    config['amfConfigs'][0]['address'] = amf_ip
    bios.write('config/open5gs-gnb.yaml', config, file_type='yaml')


if __name__ == "__main__":
    if sys.argv[1] == "mme":
        init_mme()
    elif sys.argv[1] == "sgwc":
        init_sgwc()
    elif sys.argv[1] == "smf":
        init_smf()
    elif sys.argv[1] == "amf":
        init_amf()
    elif sys.argv[1] == "sgwu":
        init_sgwu()
    elif sys.argv[1] == "upf":
        init_upf()
    elif sys.argv[1] == "hss":
        init_hss()
    elif sys.argv[1] == "pcrf":
        init_pcrf()
    elif sys.argv[1] == "nrf":
        init_nrf()
    elif sys.argv[1] == "ausf":
        init_ausf()
    elif sys.argv[1] == "udm":
        init_udm()
    elif sys.argv[1] == "pcf":
        init_pcf()
    elif sys.argv[1] == "nssf":
        init_nssf()
    elif sys.argv[1] == "udr":
        init_udr()
    elif sys.argv[1] == "gnb":
        init_gnb()
    print("init", sys.argv[1], "done")
