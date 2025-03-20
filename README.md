## 1.搭建Telegram Bot API server

为了解除上传和下载文件大小的限制，可以使用本地API服务器，因为官方API限制上传大小为20M，而本地API服务器则没有这个限制。主要有以下俩种方式

#### 1.使用官方提供的方案进行构建

详见[Telegram Bot API server ](https://github.com/tdlib/telegram-bot-api)

#### 2.使用第三方构建的docker镜像直接使用

详见[Docker image of Telegram Bot API Server ](https://github.com/aiogram/telegram-bot-api)

启动 Telegram Bot API命令

```dockerfile
docker run -d \
  -p 8081:8081 \
  --name=telegram-bot-api \
  --restart=always \
  -v telegram-bot-api-data:/var/lib/telegram-bot-api \
  -e TELEGRAM_API_ID=your_api_id \  
  -e TELEGRAM_API_HASH=your_api_hash \ 
  -e TELEGRAM_LOCAL=true \
  aiogram/telegram-bot-api:latest
```


设置 `TELEGRAM_LOCAL=true` 允许 Bot API 服务器处理本地请求，否则上传和下载文件的大小仍将受到限制。

## 2.配置脚本文件，运行Bot脚本

#### 1.安装ffmpeg及相关python库

```bash
sudo apt update 
sudo apt install ffmpeg
pip install python-telegram-bot moviepy time os
```
”根据错误信息，系统建议我们使用虚拟环境。让我们按照以下步骤操作：

1. 首先安装必要的系统包：
2. 创建虚拟环境：
3. 激活虚拟环境：
```bash
source venv/bin/activate
 ```

4. 在虚拟环境中安装依赖：
```bash
pip install python-telegram-bot moviepy
 ```
```

5. 安装 ffmpeg（moviepy 需要它来处理视频）：
```bash
apt install ffmpeg
 ```

6. 运行机器人程序：
```bash
python bot.py
 ```

注意：

- 每次需要运行机器人时，都需要先激活虚拟环境
- 如果关闭终端后重新开始，需要重新激活虚拟环境
- 要退出虚拟环境可以使用 deactivate 命令
当你看到命令提示符前面有 (venv) 时，说明虚拟环境已经成功激活。
“
#### 2.运行Bot脚本

在 `Bot.py` 脚本中，将 `TELEGRAM_TOKEN` 替换为你申请的电报机器人的 TOKEN，并根据需要设置密码等其他配置。

启动

```bash
/Bot.py
```







