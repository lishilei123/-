import os
import subprocess
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

TELEGRAM_TOKEN = '7521450072:AAGghWZrxbg3K_7aRRN-k73CzhMLiDc4DJU'
PASSWORD = '密码'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('请输入密码以启用视频压缩功能：')

async def verify_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text == PASSWORD:
        context.user_data['compress_enabled'] = True
        await update.message.reply_text('密码正确，视频压缩功能已启用！')
    else:
        await update.message.reply_text('密码错误，请重试。')

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['compress_enabled'] = False
    await update.message.reply_text('视频压缩功能已禁用。')


from moviepy.editor import VideoFileClip

def lum_contrast(clip, lum=0, contrast=0.1):
    # 这里你需要实现亮度和对比度调整的逻辑
    # 可以使用其他库或自定义实现
    return clip

def compress_and_rotate_video(input_file, output_file):
    try:
        clip = VideoFileClip(input_file)
        width, height = clip.size

        print(time(),width, height)
        need_resize = width >= 1920 or height >= 1920

        if need_resize:
            # 计算新的分辨率，保持纵横比
            new_width = width // 2
            new_height = height // 2
            new_resolution = (new_width, new_height)
            # 调整视频分辨率
            clip = clip.resize(newsize=new_resolution)
            print(f"Video was resized to: {new_resolution}")

        # 检查是否为横屏
        if width > height:
            # 顺时针旋转90度
            clip = clip.rotate(90)
            print("Video was rotated to portrait mode.")

        # 增加对比度、亮度和饱和度
        clip_with_lum_contrast = lum_contrast(clip, 0, 0.1)  # 增加亮度和对比度

        # 写入文件
        clip_with_lum_contrast.write_videofile(
            output_file,
            codec='libx264',
            preset='medium',
            audio_codec='mp3',
            audio_bitrate="128k",
            ffmpeg_params=["-crf", "25"]
        )
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'clip' in locals():
            clip.close()




async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('compress_enabled'):
        try:
            video_file = await update.message.video.get_file()
            
            print(video_file.file_path)
            parts = video_file.file_path.split('/')
            print(parts[-1])
            input_path = f'/var/lib/docker/volumes/telegram-bot-api-data/_data/{TELEGRAM_TOKEN}/videos/{parts[-1]}'
            print(input_path)               
            output_path = f'/var/lib/docker/volumes/telegram-bot-api-data/_data/{TELEGRAM_TOKEN}/videos/yasuo{parts[-1]}'
            compress_and_rotate_video(input_path, output_path)
            
            with open(output_path, 'rb') as video:
                await update.message.reply_video(video)
        except Exception as e:
            await update.message.reply_text(f"处理视频时出错: {e}")
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)

                
    else:
        await update.message.reply_text('视频压缩功能未启用。请发送 /start 启用该功能。')

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).base_url("http://localhost:8081/bot").build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("end", end))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify_password))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    app.run_polling()

if __name__ == '__main__':
    main()

