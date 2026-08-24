import os
import time
import random
import telebot
from dotenv import load_dotenv
from commands import register_commands

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# 管理员ID
ADMIN_ID = 8310964868

# 存储数据（暂时存在内存，重启会清空）
users = {}          # 已注册用户
tasks = []          # 任务列表
submissions = []    # 提交记录
user_current_task = {}  # 用户当前抽到的任务

try:
    bot = telebot.TeleBot(TOKEN)
    register_commands(bot)

    # ==================== 注册相关 ====================
    @bot.message_handler(commands=['start', 'hello'])
    def send_welcome(message):
        user_id = message.from_user.id

        if user_id in users:
            nickname = users[user_id]["nickname"]
            bot.reply_to(message, f"欢迎回来，{nickname}！\n\n可用命令：\n/task - 随机抽取任务")
        else:
            msg = bot.reply_to(message, "你好！请先注册。\n请输入你的昵称：")
            bot.register_next_step_handler(msg, process_nickname)

    def process_nickname(message):
        user_id = message.from_user.id
        nickname = message.text.strip()

        if not nickname:
            msg = bot.reply_to(message, "昵称不能为空，请重新输入：")
            bot.register_next_step_handler(msg, process_nickname)
            return

        users[user_id] = {"nickname": nickname}
        bot.reply_to(message, f"注册成功！欢迎你，{nickname}！\n\n发送 /task 可以随机抽取任务。")

    # ==================== 管理员添加任务 ====================
    @bot.message_handler(commands=['addtask'])
    def add_task(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "你没有权限使用此命令。")
            return

        msg = bot.reply_to(message, "请输入任务内容：")
        bot.register_next_step_handler(msg, save_task)

    def save_task(message):
        if message.from_user.id != ADMIN_ID:
            return

        task_content = message.text.strip()
        if not task_content:
            bot.reply_to(message, "任务内容不能为空。")
            return

        tasks.append(task_content)
        bot.reply_to(message, f"任务添加成功！\n当前共有 {len(tasks)} 个任务。\n\n任务内容：\n{task_content}")

    # ==================== 玩家随机抽取任务 ====================
    @bot.message_handler(commands=['task'])
    def get_task(message):
        user_id = message.from_user.id

        if user_id not in users:
            bot.reply_to(message, "请先发送 /start 进行注册。")
            return

        if not tasks:
            bot.reply_to(message, "目前还没有任务，请等待管理员添加。")
            return

        # 随机抽取一个任务
        task = random.choice(tasks)
        user_current_task[user_id] = task

        bot.reply_to(message, f"你抽到的任务是：\n\n{task}\n\n请直接发送视频来完成任务。")

    # ==================== 接收视频提交 ====================
    @bot.message_handler(content_types=['video', 'video_note'])
    def handle_video(message):
        user_id = message.from_user.id

        if user_id not in users:
            bot.reply_to(message, "请先注册。")
            return

        if user_id not in user_current_task:
            bot.reply_to(message, "你还没有抽取任务。\n请先发送 /task 随机抽取任务。")
            return

        task = user_current_task[user_id]
        nickname = users[user_id]["nickname"]

        # 记录提交
        submissions.append({
            "user_id": user_id,
            "nickname": nickname,
            "task": task,
            "video_file_id": message.video.file_id if message.video else message.video_note.file_id,
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        })

        # 清除当前任务
        del user_current_task[user_id]

        bot.reply_to(message, f"提交成功！\n任务「{task}」已记录。\n\n（目前自动通过，后续可审核）")

    # ==================== 管理员查看提交记录 ====================
    @bot.message_handler(commands=['records'])
    def view_records(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "你没有权限。")
            return

        if not submissions:
            bot.reply_to(message, "目前还没有提交记录。")
            return

        text = f"共有 {len(submissions)} 条提交记录：\n\n"
        for i, s in enumerate(submissions[-10:], 1):  # 只显示最近10条
            text += f"{i}. {s['nickname']} - {s['task'][:20]}... - {s['time']}\n"

        bot.reply_to(message, text)

    # 其他文字消息
    @bot.message_handler(func=lambda msg: True)
    def echo_all(message):
        user_id = message.from_user.id
        if user_id not in users:
            bot.reply_to(message, "请先发送 /start 进行注册。")
        else:
            bot.reply_to(message, "可用命令：\n/task - 随机抽取任务\n（完成任务请直接发送视频）")

    bot.delete_webhook(drop_pending_updates=True)
    bot.polling()

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    while True:
        time.sleep(3600)
