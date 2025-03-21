#为了解决一些视频加载过慢的问题，通过不限流量的服务器下载转发下加速加载
import os
import subprocess
import time
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters


TELEGRAM_TOKEN = 'xxx:xxxx'
PASSWORD = '密码'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('请输入密码以启用视频转发功能：')


async def verify_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text == PASSWORD:
        context.user_data['compress_enabled'] = True
        await update.message.reply_text('密码正确，视频转发功能已启用！')
    else:
        await update.message.reply_text('密码错误，请重试。')


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['compress_enabled'] = False
    await update.message.reply_text('视频转发功能已禁用。')


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('compress_enabled'):
        input_path = None
        try:
            video = update.message.video
            video_file = await video.get_file()
            print(video_file.file_path)
            parts = video_file.file_path.split('/')
            print(parts[-1])
            input_path = f'/var/lib/docker/volumes/telegram-bot-api-data/_data/{TELEGRAM_TOKEN}/videos/{parts[-1]}'

            # 直接从Telegram Video对象获取视频信息
            width = video.width
            height = video.height
            duration = video.duration
            file_name = video.file_name if video.file_name else "未知文件名"
            mime_type = video.mime_type if video.mime_type else "未知类型"
            file_size = video.file_size if video.file_size else 0

            caption = (
                f"文件名: {file_name}\n"
                f"时长: {duration} 秒\n"
                f"分辨率: {width}x{height}\n"
                f"文件类型: {mime_type}\n"
                f"文件大小: {file_size/1024/1024:.2f} MB"
            )

            # 使用ffmpeg提取视频第一帧作为封面
            thumbnail_path = input_path + '_thumb.jpg'
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', 'select=eq(n\,0)',
                '-vframes', '1',
                thumbnail_path
            ]
            subprocess.run(ffmpeg_cmd, check=True)

            # 直接转发视频
            with open(input_path, 'rb') as video_file, open(thumbnail_path, 'rb') as thumb_file:
                await update.message.reply_video(
                    video=InputFile(video_file),
                    duration=duration,
                    width=width,
                    height=height,
                    caption=caption,
                    supports_streaming=True,
                    filename=file_name,
                    thumbnail=InputFile(thumb_file)
                )

            # 删除临时生成的封面
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)

        except Exception as e:
            await update.message.reply_text(f"处理视频时出错: {e}")
        finally:
            if input_path and os.path.exists(input_path):
                print(f"删除文件: {input_path}")
                os.remove(input_path)   # 注释掉删除操作，便于调试

    else:
        await update.message.reply_text('视频转发功能未启用。请发送 /start 启用该功能。')


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).base_url("http://localhost:8081/bot").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("end", end))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify_password))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))

    app.run_polling()


if __name__ == '__main__':
    main()
