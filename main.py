import os
import time
import telebot
from dotenv import load_dotenv
from commands import register_commands

# 加载环境变量
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# 用来存储已注册用户（暂时存在内存里）
# 格式：{用户ID: {"nickname": "昵称"}}
users = {}

try:
    bot = telebot.TeleBot(TOKEN)
    register_commands(bot)

    @bot.message_handler(commands=['start', 'hello'])
    def send_welcome(message):
        user_id = message.from_user.id

        # 判断用户是否已经注册
        if user_id in users:
            nickname = users[user_id]["nickname"]
            bot.reply_to(message, f"欢迎回来，{nickname}！\n你已经注册过了。")
        else:
            bot.reply_to(message, "你好！请先注册。\n请输入你的昵称：")
            # 等待用户下一步输入昵称
            bot.register_next_step_handler(message, process_nickname)

    def process_nickname(message):
        user_id = message.from_user.id
        nickname = message.text.strip()

        if not nickname:
            bot.reply_to(message, "昵称不能为空，请重新输入你的昵称：")
            bot.register_next_step_handler(message, process_nickname)
            return

        # 保存用户信息
        users[user_id] = {
            "nickname": nickname
        }

        bot.reply_to(message, f"注册成功！\n欢迎你，{nickname}！\n\n以后可以直接发送 /start 进入。")

    # 其他消息先简单回复
    @bot.message_handler(func=lambda msg: True)
    def echo_all(message):
        user_id = message.from_user.id
        if user_id not in users:
            bot.reply_to(message, "请先发送 /start 进行注册。")
        else:
            bot.reply_to(message, f"收到：{message.text}")

    # 启动机器人
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling()

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    while True:
        time.sleep(3600)
