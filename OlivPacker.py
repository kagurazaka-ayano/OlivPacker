# !/usr/bin/python
# -*- coding: utf-8 -*-
"""
@Project	: OlivPacker
@Time		: 8/20/23 3:35 AM
@Author		: ayano
@File		: OlivPacker.py
"""

import zipfile
from pathlib import Path
from json import loads, JSONDecodeError
import paramiko

motd = """


   ███████    ██ ██          ███████                    ██                   
  ██░░░░░██  ░██░░          ░██░░░░██                  ░██                   
 ██     ░░██ ░██ ██ ██    ██░██   ░██  ██████    █████ ░██  ██  █████  ██████
░██      ░██ ░██░██░██   ░██░███████  ░░░░░░██  ██░░░██░██ ██  ██░░░██░░██░░█
░██      ░██ ░██░██░░██ ░██ ░██░░░░    ███████ ░██  ░░ ░████  ░███████ ░██ ░ 
░░██     ██  ░██░██ ░░████  ░██       ██░░░░██ ░██   ██░██░██ ░██░░░░  ░██   
 ░░███████   ███░██  ░░██   ░██      ░░████████░░█████ ░██░░██░░██████░███   
  ░░░░░░░   ░░░ ░░    ░░    ░░        ░░░░░░░░  ░░░░░  ░░  ░░  ░░░░░░ ░░░    

OlivOS插件打包工具
Made by Kagurazaka Ayano"""

supported_protocol = ["sftp", "none"]
root = Path(__file__).parent
config = root / Path("packing.json")


def validate_config():
	global config

	def new_config_file(message: str):
		open(config, "w+", encoding="utf-8").write("""{
						"output": "./output",
						"scan_path": [
							"./"
						],
						"upload_method": "none",
						"upload_info": {
							"ssh": {
								"default": {
									"host": "",
									"user": "",
									"port": 22,
									"passwd": "",
									"identity_path": "",
									"dest": "/absolute/path/to/plugin/folder"
								}
							}
						}
					}""")
		exit(message)

	if not config.exists():
		new_config_file(f"配置文件不存在, 已创建默认配置文件({root}/packing.json), 请修改之后使用")
	try:
		config = loads(open(config, "r", encoding="utf-8").read())
	except JSONDecodeError:
		new_config_file("原配置文件已损坏, 无法读取, 已重新创建配置文件, 请修改之后使用")


def load_package_json(package_json_list: list, scan_path: list):
	"""
	将扫描路径中的app.json文件的路径加载到package_json_list中
	:return:
	"""
	for k in scan_path:
		for i in Path(k).iterdir():
			if i.is_dir():
				if i.name.startswith("."):
					continue
				content = [j.resolve().name for j in i.iterdir()]
				if "app.json" in content:
					package_json_list.append(i)


def construct_plugin_info(package_json_list: list[Path]) -> str:
	"""
	通过给定的扫描包路径来构造提示字符串
	:return: 构造好的字符串
	"""
	plugin_info = ""
	idx = 0
	print("找到这些插件:")
	for i in package_json_list:
		with open(i / Path("app.json"), "r", encoding="utf-8") as f:
			json = loads(f.read())
			plugin_info += \
				f"""
{idx}:
	插件路径: {i}
	插件名称: {json["name"]}
	插件命名空间: {json["namespace"]}
	插件作者: {json["author"]}
	插件版本: {json["version"]}
	插件描述: {json["info"]}
"""
			idx += 1
	plugin_info += f"输入选择打包的项目的编号, 多个编号使用空格隔开, 输入all选择全部打包: "
	return plugin_info


def make_opk(output: Path, plugin_list: list[Path]) -> list[str]:
	"""
	制作opk文件
	:param output:
	:param plugin_list:
	:return:
	"""
	output.mkdir(exist_ok=True, parents=True)
	package_list = []
	package_count = {}

	for i in plugin_list:
		if str(output / i.name) + ".opk" in package_list:
			if str(output / i.name) + ".opk" not in package_count.keys():
				package_count.update({str(output / i.name) + ".opk": 1})
			else:
				package_count[str(output / i.name) + ".opk"] += 1
		name = str(output / i.name) + (f"-{str(package_count[str(output / i.name) + '.opk'])}.opk" if (
																											  str(output / i.name) + ".opk") in package_count.keys() else ".opk")
		with zipfile.ZipFile(name, "w") as z:
			for j in i.iterdir():
				print(j)
				z.write(i / j.name, arcname=str(j.name))
		package_list.append(name)
	return package_list


def get_ssh_client(conf: dict[str, dict], profile="default") -> tuple:
	"""
	获取ssh客户端链接
	:param conf: ssh配置
	:param profile: 使用的配置
	:return: 元祖(ssh客户端, 目标路径)
	"""
	info = conf[profile]
	client = paramiko.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	try:
		client.connect(
			hostname=info["host"],
			username=info["user"],
			password=info["passwd"],
			port=info["port"],
			key_filename=info["identity_path"]
		)
	except paramiko.SSHException as e:
		if e is paramiko.BadHostKeyException:
			print("无法验证host")
		elif e is paramiko.AuthenticationException:
			print("登录凭据错误")
		else:
			print("未知错误")
		print("开始尝试下一配置...")
		for i in conf:
			if i == profile:
				continue
			info = conf[i]
			try:
				client.connect(
					hostname=info["host"],
					username=info["user"],
					password=info["passwd"],
					port=info["port"],
					key_filename=info["identity_path"]
				)
			except paramiko.SSHException as e:
				if e is paramiko.BadHostKeyException:
					print("无法验证host")
				elif e is paramiko.AuthenticationException:
					print("登录凭据错误")
				else:
					print("未知错误")
				print("开始尝试下一配置...")
			else:
				return client, info["dest"]
	else:
		return client, info["dest"]
	return None, None


def sftp_upload(dest: str, package_list: list[str], ssh_client: paramiko.SSHClient):
	"""
	使用sftp上传文件
	:param dest: 远程目标文件夹
	:param package_list: 需要上传的文件路径列表
	:param ssh_client: 配置好的ssh客户端
	:return:
	"""
	sftp = ssh_client.open_sftp()
	dest += "/" if not dest.endswith("/") else ""
	for i in package_list:
		try:
			sftp.put(i, dest + Path(i).name)
		except FileNotFoundError:
			print(f"远程路径{dest}不存在, 上传取消")
		else:
			print(f"文件'{i}'上传成功")
	ssh_client.close()
	sftp.close()


if __name__ == '__main__':
	print(motd)
	validate_config()
	output = root / Path(config["output"])
	package_json_list = []
	load_package_json(package_json_list, config["scan_path"])
	ops = input(construct_plugin_info(package_json_list)).split(" ")
	packed_opk = []
	if "all" in ops:
		packed_opk = make_opk(output, package_json_list)
	else:
		plugin_list = []
		for i in ops:
			try:
				pos = int(i)
			except ValueError:
				print(f"{i}不是数字, 跳过")
				continue
			if pos >= len(package_json_list) or pos < 0:
				print(f"输入的编号{i}超出范围, 跳过")
				continue
			plugin_list.append(package_json_list[pos])
		package_opk = make_opk(plugin_list)
	match config["upload_method"]:
		case "none":
			print(f"已选择不上传")
		case "ssh":
			print("已选择sftp上传")
			print("配置文件中拥有这些profile:")
			info = config["upload_info"]
			for i in info["ssh"]:
				print("\t" + i)
			prof = ""
			while prof not in info["ssh"].keys():
				prof = input("选择profile: ")
			print(f"使用{prof}建立连接...")
			client, dest = get_ssh_client(info["ssh"], prof)
			if client is None:
				print("无法建立链接")
			else:
				print("上传中...")
				sftp_upload(dest, packed_opk, client)

	print(f"可以在本地的{root}/output文件夹中找到打包好的opk文件")
