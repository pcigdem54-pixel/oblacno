import discord
from discord.ext import commands
import config

class TicketKapatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Bileti Kapat", style=discord.ButtonStyle.red, custom_id="ticket_kapat")
    async def bilet_kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Bilet kapatılıyor...", ephemeral=True)
        
        user_id = int(interaction.channel.topic)
        
        modlog = interaction.guild.get_channel(config.CHANNELS["MODLOG"])
        if modlog:
            embed = discord.Embed(title="Bilet Kapatıldı", color=discord.Color.red())
            embed.add_field(name="Kapatan Yetkili", value=interaction.user.mention)
            embed.add_field(name="Bilet Sahibi", value=f"<@{user_id}>")
            embed.add_field(name="Kanal", value=interaction.channel.name)
            await modlog.send(embed=embed)
            
        await interaction.channel.delete()

class TicketBaslatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Bilet Aç", style=discord.ButtonStyle.primary, custom_id="bilet_ac")
    async def bilet_ac(self, interaction: discord.Interaction, button: discord.ui.Button):
        category = interaction.channel.category
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        for role_id in [config.ROLES["ADMIN"], config.ROLES["MODERATOR"], config.ROLES["MEKAN_SAHIBI"]]:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                
        ticket_channel = await interaction.guild.create_text_channel(
            name=f"bilet-{interaction.user.name}",
            category=category,
            overwrites=overwrites,
            topic=str(interaction.user.id) 
        )
        
        etiketler = f"<@&{config.ROLES['ADMIN']}> <@&{config.ROLES['MODERATOR']}>"
        embed = discord.Embed(title="Yeni Bilet", description=f"Hoş geldin {interaction.user.mention}, sorununuzu buraya yazabilirsiniz. Yetkililer en kısa sürede ilgilenecektir.", color=discord.Color.blue())
        await ticket_channel.send(content=etiketler, embed=embed, view=TicketKapatView())
        
        await interaction.response.send_message(f"Biletin oluşturuldu: {ticket_channel.mention}", ephemeral=True)

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(TicketBaslatView())
        self.bot.add_view(TicketKapatView())

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
