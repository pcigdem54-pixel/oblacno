import discord
from discord.ext import commands
import config
import os
import sys

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Cogs klasöründeki tüm dosyaları yükle
        cogs_dir = os.path.join(os.path.dirname(__file__), 'cogs')
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                extension_name = f'cogs.{filename[:-3]}'
                try:
                    await self.load_extension(extension_name)
                    print(f"Yüklendi: {extension_name}")
                except Exception as e:
                    print(f"Hata! {extension_name} yüklenemedi: {e}")

bot = MyBot()

if __name__ == "__main__":
    bot.run(config.TOKEN)
