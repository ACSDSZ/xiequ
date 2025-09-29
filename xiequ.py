# -*- coding: utf-8 -*-
'''
脚本用于携趣的自动添加公网ip白名单
添加变量名=xiequ_uid_ukey    变量值=备注#uid#ukey
多账户换行
需要安装依赖requests
cron: */30 * * * *
new Env('携趣白名单');
'''

import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retries = Retry(total=5,
                backoff_factor=0.2,
                status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))


def get_public_ip():
    print('开始获取当前公网IP...')
    ip_services = [
        'https://ddns.oray.com/checkip', # 返回 "Current IP Address: X.X.X.X"
        'https://ip.sb',                 # 返回纯文本
        'https://cip.cc',                # 返回纯文本
        'http://ipinfo.io/ip',           # 备用，纯文本
        'https://ip.user-agent.cn/json', # 备用，JSON格式
        'https://api.ipify.org'          # 备用，纯文本
    ]

    for service_url in ip_services:
        try:
            print(f"尝试从 {service_url} 获取IP...")
            response = session.get(service_url, timeout=5)
            response.raise_for_status()
            ip_text = response.text.strip()
            
            if "Current IP Address:" in ip_text:
                ip = ip_text.split(':')[-1].strip()
                print(f"成功从Oray响应中解析到IP: {ip}")
                return ip
            
            try:
                data = response.json()
                ip = data.get('ip')
                if ip and isinstance(ip, str):
                    print(f"成功从JSON响应中解析到IP: {ip}")
                    return ip
            except requests.exceptions.JSONDecodeError:
                if '.' in ip_text and len(ip_text) > 6:
                    print(f"成功从纯文本响应中获取到IP: {ip_text}")
                    return ip_text

        except requests.exceptions.RequestException as e:
            print(f"从 {service_url} 获取IP失败: {e}")
            continue

    print("尝试了所有IP服务，均无法获取公网IP。")
    return None

def env_init(ip):
    uid_ukey_envs = os.environ.get("xiequ_uid_ukey")
    if uid_ukey_envs:
        uid_ukeys = uid_ukey_envs.splitlines()
        print(f"检测到 {len(uid_ukeys)} 个账户，准备开始处理...")
        for uid_ukey in uid_ukeys:
            if not uid_ukey: continue
            try:
                username, uid, ukey = uid_ukey.split("#")
                del_all_ip(username, uid, ukey)
                add_ip(ip, username, uid, ukey)
            except ValueError:
                print(f"环境变量格式错误，跳过此行: {uid_ukey}")
    else:
        print("没有找到环境变量 xiequ_uid_ukey")

def del_all_ip(username, uid, ukey):
    url = f"http://op.xiequ.cn/IpWhiteList.aspx?uid={uid}&ukey={ukey}&act=del&ip=all"
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        print(f"账户[{username}] 清空白名单成功")
    except requests.exceptions.RequestException as e:
        print(f"账户[{username}] 清空白名单失败: {e}")

def add_ip(ip, username, uid, ukey):
    url_with_ip = f"http://op.xiequ.cn/IpWhiteList.aspx?uid={uid}&ukey={ukey}&act=add&ip={ip}"
    try:
        response_with_ip = session.get(url_with_ip, timeout=10)
        response_with_ip.raise_for_status()
        print(f"账户[{username}] 白名单添加成功，IP: {ip}")
    except requests.exceptions.RequestException as e:
        print(f"账户[{username}] 白名单添加失败: {e}")

def main():
    ip = get_public_ip()
    if ip:
        env_init(ip)
    else:
        print("无法获取公网IP，脚本执行中止。")

if __name__ == "__main__":
    main()
