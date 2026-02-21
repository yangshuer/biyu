import os, sys, json, base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
sys.path.insert(0,project_root_dir)
from cryptography.fernet import Fernet
from tools.get_uuid import get_device_unique_id
import os

# 1.判断文件是否加密
def is_encrypted_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        if data.startswith(b"gAAAAAB"):
            return True
        else:  
            return False
    else:
        # 不存在配置文件
        raise Exception("未授权，请联系开发者授权，微信：wxid_aryiah88dd4712")

# 1.1 加密
async def decrypt_file(file_path):
    # 解密文件->校验uuid是否正确
    # 1.1.1 校验正确 -> 启动服务
    # 1.1.2 校验错误 -> 删除核心逻辑文件
    decrypted_data = None
    uuid = await get_device_unique_id()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=uuid.encode(),
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(uuid.encode()))
    fernet = Fernet(key)
    with open(file_path, "rb") as f:
        try:
            decrypted_data = fernet.decrypt(f.read()).decode()
            if json.loads(decrypted_data)['uuid'] == uuid:
                return decrypted_data # 返回模型配置信息
            else:
                # 删除核心配置使项目无法启动
                # os.remove(file_path)
                raise Exception("未授权，请联系开发者授权，微信：wxid_aryiah88dd4712")
        except:
            # 删除核心配置使项目无法启动
            # os.remove(file_path)
            raise Exception("未授权，请联系开发者授权，微信：wxid_aryiah88dd4712")

# 1.2 未加密
async def encrypt_file(file_path):
    # 读取未加密文件 -> 设置uuid -> 加密保存
    with open(file_path, "rb") as f:
        data = json.loads(f.read())
    # 1.2.1 设置uuid
    data['uuid'] = await get_device_unique_id()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=data['uuid'].encode(),
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(data['uuid'].encode()))
    # 1.2.2 重新加密保存
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(json.dumps(data).encode())
    with open(file_path, "wb") as f:
        f.write(encrypted_data)
    return json.dumps(data)

# 加密保存配置
async def encrypt_config(conf):
    try:
        uuid = await get_device_unique_id()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=uuid.encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(uuid.encode()))
        fernet = Fernet(key)
        with open('config/conf', "rb") as f:
            decrypted_data = fernet.decrypt(f.read()).decode()
            decrypted_data = json.loads(decrypted_data)
            decrypted_data['models'] = conf
        encrypted_data = fernet.encrypt(json.dumps(decrypted_data).encode())
        with open('config/conf', "wb") as f:
            f.write(encrypted_data)
    except:
        raise Exception("未授权，请联系开发者授权，微信：wxid_aryiah88dd4712")
    return decrypted_data

async def main():
    if is_encrypted_file('config/conf'):
        return await decrypt_file('config/conf')
    else:
        return await encrypt_file('config/conf')

if __name__ == "__main__":
    import asyncio
    c = json.loads(asyncio.run(main()))
    print(json.dumps(c))
    pass