import discord
from discord.ext import commands
import config
from cogs.registration import KayitBaslatView
from cogs.ticket_system import TicketBaslatView

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} olarak giriş yapıldı! (Cogs Yapısı Yüklendi)")
        
        # 1. Kayıt kanalına mesaj at (Eğer yoksa)
        kayit_kanali = self.bot.get_channel(config.CHANNELS["KAYIT_MESAJ"])
        if kayit_kanali:
            async for msg in kayit_kanali.history(limit=5):
                if msg.author == self.bot.user:
                    break
            else:
                embed = discord.Embed(
                    title="Sunucumuza Hoş Geldin!",
                    description="Aramıza katılmak ve içeriklere erişmek için aşağıdaki **Kayıt Ol** butonuna basarak kısa anketimizi doldurabilirsin 🌸",
                    color=discord.Color.magenta()
                )
                await kayit_kanali.send(embed=embed, view=KayitBaslatView())

        # 2. Ticket kanalına mesaj at (Eğer yoksa)
        ticket_kanali = self.bot.get_channel(config.CHANNELS["TICKET_MESAJ"])
        if ticket_kanali:
            async for msg in ticket_kanali.history(limit=5):
                if msg.author == self.bot.user:
                    break
            else:
                embed = discord.Embed(
                    title="Destek Talebi Oluştur",
                    description="Yetkililerle özel olarak görüşmek, bir sorunu bildirmek veya yardım almak için aşağıdaki **Bilet Aç** butonuna tıklayabilirsin ✨",
                    color=discord.Color.teal()
                )
                await ticket_kanali.send(embed=embed, view=TicketBaslatView())

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Sunucuya katılana Kayıtsız rolü ver
        kayitsiz_role = member.guild.get_role(config.ROLES["KAYITSIZ"])
        if kayitsiz_role:
            await member.add_roles(kayitsiz_role)
            
        await self.update_member_count(member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.update_member_count(member.guild)

    async def update_member_count(self, guild):
        channel = guild.get_channel(config.CHANNELS.get("UYE_SAYISI_KANALI"))
        if channel:
            # Botları saymıyoruz, sadece gerçek üyeler
            human_count = len([m for m in guild.members if not m.bot])
            new_name = f"══▐ {human_count} KATILIMCI▐ ══"
            
            if channel.name != new_name:
                try:
                    await channel.edit(name=new_name)
                except discord.HTTPException:
                    pass # Discord'un isim değiştirme limitine (10 dakikada 2 kez) takılırsak hata vermesin

async def setup(bot):
    await bot.add_cog(Events(bot))
