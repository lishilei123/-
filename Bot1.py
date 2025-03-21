import os
import subprocess
import time
import asyncio
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import telegram.error


TELEGRAM_TOKEN = 'xxx:xxx'
PASSWORD = '密码'
VERIFY_TIMEOUT_HOURS = 72  # 密码验证有效期（小时）

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('请输入密码以启用视频转发功能：')

async def verify_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text == PASSWORD:
        context.user_data['compress_enabled'] = True
        context.user_data['verify_time'] = time.time()
        await update.message.reply_text(f'密码正确，视频转发功能已启用！（{VERIFY_TIMEOUT_HOURS}小时内有效）')
    else:
        await update.message.reply_text('密码错误，请重试。')


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['compress_enabled'] = False
    await update.message.reply_text('视频转发功能已禁用。')


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    verify_time = context.user_data.get('verify_time', 0)
    if time.time() - verify_time > VERIFY_TIMEOUT_HOURS * 3600:  # 验证超时
        context.user_data['compress_enabled'] = False
        await update.message.reply_text('密码验证已过期，请重新发送 /start 进行验证。')
        return
    
    if context.user_data.get('compress_enabled'):
        input_path = None
        original_path = None  # 保存原始视频文件路径
        thumbnail_path = None
        max_retries = 3
        retry_delay = 2  # 重试等待时间（秒）
        
        for attempt in range(max_retries):
            try:
                video = update.message.video
                try:
                    video_file = await video.get_file()
                except telegram.error.TimedOut:
                    if attempt < max_retries - 1:
                        print(f"获取文件超时，等待{retry_delay}秒后重试...")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        raise
                print(f"处理视频，尝试次数：{attempt + 1}")
                print(f"视频文件路径：{video_file.file_path}")
                parts = video_file.file_path.split('/')
                original_path = f'/var/lib/docker/volumes/telegram-bot-api-data/_data/{TELEGRAM_TOKEN}/videos/{parts[-1]}'
                input_path = original_path
                
                # 等待文件写入完成
                wait_time = 0
                max_wait = 10  # 最大等待时间（秒）
                while not os.path.exists(input_path) and wait_time < max_wait:
                    await asyncio.sleep(1)
                    wait_time += 1
                
                if not os.path.exists(input_path):
                    raise FileNotFoundError(f"视频文件未找到：{input_path}")
                
                if not os.path.getsize(input_path):
                    raise ValueError("视频文件大小为0")

                # 直接从Telegram Video对象获取视频信息
                width = video.width
                height = video.height
                duration = video.duration
                file_name = video.file_name if video.file_name else "未知文件名"
                mime_type = video.mime_type if video.mime_type else "未知类型"
                file_size = video.file_size if video.file_size else 0

                caption = (
                    f"分辨率: {width}x{height}\n"
                )

                # 计算视频大小（MB）与时长（分钟）的比例
                file_size_mb = file_size / (1024 * 1024)  # 转换为MB
                duration_minutes = duration / 60  # 转换为分钟
                size_duration_ratio = file_size_mb / duration_minutes if duration_minutes > 0 else float('inf')

                # 使用ffmpeg提取视频第一帧作为封面
                thumbnail_path = input_path + '_thumb.jpg'
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-i', input_path,
                    '-vf', 'select=eq(n\,0)',
                    '-vframes', '1',
                    '-y',
                    thumbnail_path
                ]
                # 如果比例大于10，进行压缩
                if size_duration_ratio > 15:
                    compressed_path = input_path + '_compressed.mp4'
                    compress_cmd = [
                        'ffmpeg',
                        '-i', input_path,
                        '-c:v', 'libx264',
                        '-preset', 'medium',
                        '-crf', '30',
                        '-c:a', 'copy',
                        '-y',
                        compressed_path
                    ]
                    subprocess.run(compress_cmd, check=True, capture_output=True)
                    
                    if not os.path.exists(compressed_path) or not os.path.getsize(compressed_path):
                        raise ValueError("视频压缩失败")
                    
                    # 使用压缩后的视频文件
                    input_path = compressed_path
                    caption += f"已压缩（原始大小/时长比：{size_duration_ratio:.2f}MB/分钟）\n"


                subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

                # 确保缩略图生成成功
                if not os.path.exists(thumbnail_path) or not os.path.getsize(thumbnail_path):
                    raise ValueError("缩略图生成失败")

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
                    break  # 发送成功，跳出重试循环

            except Exception as e:
                error_msg = f"处理视频时出错 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
                print(error_msg)
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    await update.message.reply_text(error_msg)
            finally:
                # 清理所有临时文件
                if thumbnail_path and os.path.exists(thumbnail_path):
                    print(f"删除缩略图: {thumbnail_path}")
                    os.remove(thumbnail_path)
                if original_path and os.path.exists(original_path):
                    print(f"删除原始视频文件: {original_path}")
                    os.remove(original_path)
                if input_path and input_path != original_path and os.path.exists(input_path):
                    print(f"删除压缩视频文件: {input_path}")
                    os.remove(input_path)

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
