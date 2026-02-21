# -*- coding: utf-8 -*-
"""
获取设备唯一ID（主板序列号+MAC地址组合）
跨平台实现，支持Windows、Linux和macOS。
"""
import sys
import subprocess

async def get_mainboard_serial():
    """获取设备主板序列号（跨平台实现）"""
    try:
        if sys.platform.startswith('win'):
            # Windows系统通过WMI获取
            cmd = 'wmic baseboard get serialnumber'
            result = subprocess.check_output(cmd, shell=True, text=True)
            # 解析输出（去除标题行和多余空白）
            serial = [line.strip() for line in result.splitlines() if line.strip()][1]
            return serial
        
        elif sys.platform.startswith('linux'):
            # Linux系统读取DMI信息文件
            with open('/sys/class/dmi/id/product_serial', 'r') as f:
                return f.read().strip()
        
        elif sys.platform.startswith('darwin'):
            # macOS通过ioreg获取主板ID
            cmd = "ioreg -l | grep -i 'board-id' | awk -F'=' '{print $2}'"
            result = subprocess.check_output(cmd, shell=True, text=True)
            return result.strip().strip('"')

        else:
            raise NotImplementedError(f"不支持的操作系统: {sys.platform}")
    
    except Exception as e:
        print(f"获取主板序列号失败: {str(e)}")
        return None

async def get_mac_address():
    """获取设备主网卡MAC地址（跨平台实现）"""
    try:
        if sys.platform.startswith('win'):
            # Windows通过ipconfig获取物理地址
            cmd = 'ipconfig /all | findstr /i "物理地址"'
            result = subprocess.check_output(cmd, shell=True, text=True)
            # 解析第一个有效MAC地址（格式：xx-xx-xx-xx-xx-xx）
            mac_line = [line.strip() for line in result.splitlines() if line.strip()][0]
            return mac_line.split(':')[-1].strip().replace('-', ':')
        
        elif sys.platform.startswith('linux'):
            # Linux通过ip命令获取第一个非虚拟网卡的MAC
            cmd = "ip link show | awk '/link\/ether/ && !/lo:/ {print $2; exit}'"
            result = subprocess.check_output(cmd, shell=True, text=True)
            return result.strip()
        
        elif sys.platform.startswith('darwin'):
            # macOS通过ifconfig获取en0接口的MAC
            cmd = "ifconfig en0 | awk '/ether/ {print $2}'"
            result = subprocess.check_output(cmd, shell=True, text=True)
            return result.strip()
        
        else:
            raise NotImplementedError(f"不支持的操作系统: {sys.platform}")
    
    except Exception as e:
        print(f"获取MAC地址失败: {str(e)}")
        return None

async def get_device_unique_id():
    """获取设备唯一ID（主板序列号）"""
    serial = await get_mainboard_serial()
    return f"{serial}_"

if __name__ == "__main__":
    import asyncio
    unique_id = asyncio.run(get_device_unique_id())
    if unique_id:
        print(f"设备唯一ID: {unique_id}")
    else:
        print("无法获取设备唯一ID")