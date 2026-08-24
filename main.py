import os
import time
import random
import telebot
from dotenv import load_dotenv
from commands import register_commands

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# ==================== 配置 ====================
ADMIN_ID = 8310964868          # 你的管理员ID

# 数据存储（目前存在内存，机器人重启后会清空）
users = {}                     # 用户信息
tasks = []                     # 任务列表
submissions = []               # 提交记录
user_current_task = {}         # 用户当前抽到的任务

try:
    bot = telebot.TeleBot(TOKEN)
    register_commands(bot)

    # ==================== 注册 ====================
    @bot.message_handler(commands=['start', 'hello'])
    def send_welcome(message):
        user_id = message.from_user.id

        if user_id in users:
            nickname = users[user_id]["nickname"]
            text = f"欢迎回来，{nickname}！\n\n" \
                   f"可用命令：\n" \
                   f"/task - 随机抽取任务\n" \
                   f"（完成任务请直接发送视频）"
            bot.reply_to(message, text)
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

        users[user_id] = {
            "nickname": nickname,
            "register_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        bot.reply_to(message, f"注册成功！欢迎你，{nickname}！\n\n发送 /task 可以随机抽取任务。")

    # ==================== 管理员：添加任务 ====================
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
            bot.reply_to(message, "任务内容不能为空，请重新输入：")
            bot.register_next_step_handler(message, save_task)
            return

        tasks.append({
            "content": task_content,
            "created_time": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        bot.reply_to(message, f"✅ 任务添加成功！\n当前共有 {len(tasks)} 个任务。\n\n任务内容：\n{task_content}")

    # ==================== 管理员：查看所有任务 ====================
    @bot.message_handler(commands=['listtasks'])
    def list_tasks(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "你没有权限。")
            return

        if not tasks:
            bot.reply_to(message, "目前还没有任务。")
            return

        text = f"当前共有 {len(tasks)} 个任务：\n\n"
        for i, t in enumerate(tasks, 1):
            text += f"{i}. {t['content']}\n"
        bot.reply_to(message, text)

    # ==================== 玩家：随机抽取任务 ====================
    @bot.message_handler(commands=['task'])
    def get_task(message):
        user_id = message.from_user.id

        if user_id not in users:
            bot.reply_to(message, "请先发送 /start 进行注册。")
            return

        if not tasks:
            bot.reply_to(message, "目前还没有任务，请等待管理员添加。")
            return

        # 随机抽取
        task = random.choice(tasks)
        user_current_task[user_id] = task["content"]

        bot.reply_to(
            message,
            f"🎯 你抽到的任务是：\n\n"
            f"{task['content']}\n\n"
            f"请直接发送【视频】来完成任务。"
        )

    # ==================== 接收视频并自动通知管理员 ====================
    @bot.message_handler(content_types=['video', 'video_note'])
    def handle_video(message):
        user_id = message.from_user.id

        if user_id not in users:
            bot.reply_to(message, "请先发送 /start 进行注册。")
            return

        if user_id not in user_current_task:
            bot.reply_to(message, "你还没有抽取任务。\n请先发送 /task 随机抽取任务。")
            return

        task = user_current_task[user_id]
        nickname = users[user_id]["nickname"]
        submit_time = time.strftime("%Y-%m-%d %H:%M:%S")

        # 获取视频file_id
        if message.video:
            file_id = message.video.file_id
        else:
            file_id = message.video_note.file_id

        # 保存记录
        submissions.append({
            "user_id": user_id,
            "nickname": nickname,
            "task": task,
            "video_file_id": file_id,
            "time": submit_time
        })

        # 清除当前任务
        del user_current_task[user_id]

        # 回复用户
        bot.reply_to(message, f"✅ 提交成功！\n任务已记录。")

        # ========== 自动把记录 + 视频发给管理员 ==========
        try:
            notify_text = (
                f"📢 新任务提交！\n\n"
                f"用户：{nickname}\n"
                f"任务：{task}\n"
                f"时间：{submit_time}"
            )
            bot.send_message(ADMIN_ID, notify_text)
            bot.send_video(ADMIN_ID, file_id, caption=f"用户【{nickname}】提交的视频")
        except Exception as e:
            print(f"通知管理员失败: {e}")

    # ==================== 管理员：查看提交记录 ====================
    @bot.message_handler(commands=['records'])
    def view_records(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "你没有权限。")
            return

        if not submissions:
            bot.reply_to(message, "目前还没有提交记录。")
            return

        text = f"共有 {len(submissions)} 条提交记录（最近15条）：\n\n"
        for i, s in enumerate(submissions[-15:], 1):
            text += f"{i}. {s['nickname']} | {s['task'][:20]}... | {s['time']}\n"
        bot.reply_to(message, text)

    # ==================== 其他文字消息 ====================
    @bot.message_handler(func=lambda msg: True)
    def other_messages(message):
        user_id = message.from_user.id
        if user_id not in users:
            bot.reply_to(message, "请先发送 /start 进行注册。")
        else:
            bot.reply_to(message, "可用命令：\n/task - 随机抽取任务\n（完成任务请直接发送视频）")

    # 启动
    bot.delete_webhook(drop_pending_updates=True)
    print("Bot is running...")
    bot.polling()

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    while True:
        time.sleep(3600)
