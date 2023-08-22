# OlivPacker

轻量级的OlivOS opk插件打包工具

支持:
- 批量打包opk
- 通过sftp上传到服务器
- 同时打包多个目录下的软件包

## 使用

下载依赖:

```bash
pip install -r requirements.txt
```

第一次使用会创建packing.json文件，用于配置打包信息, 请按照提示填写

- `scan_path`: 打包器扫描的目录
- `output`: 打包器输出的目录
- `upload_method`: 上传到远程服务器的方式, 目前支持`sftp`和`none`, `none`表示不上传
- `upload_info`: 上传到远程服务器的信息字典
  - `sftp`: sftp服务器信息
    - 自定义的服务器profile, 但必须要有一个叫`default`的profile
      - `host`: sftp服务器地址
      - `port`: sftp服务器端口
      - `user`: sftp服务器用户名
      - `passwd`: sftp服务器密码
      - `identity_path`: ssh私钥路径
      - `dest`: 服务器插件目标路径

## 打包为可执行文件

```bash
pyinstaller -F -n OlivPacker OlivPacker.py
```
