from telebot import TeleBot
from telebot.types import BotCommand

def register_commands(bot: TeleBot):
    commands = [
        BotCommand("start", "开始 / 注册"),
        BotCommand("task", "随机抽取任务"),
        BotCommand("addtask", "添加任务（管理员）"),
        BotCommand("listtasks", "查看所有任务（管理员）"),
        BotCommand("records", "查看提交记录（管理员）"),
    ]
    bot.set_my_commands(commands)
