import discord
from discord.ext import commands
import config

class KayitModal(discord.ui.Modal, title='Kayıt Formu'):
    name = discord.ui.TextInput(
        label='Adın nedir?',
        placeholder='Kendi adını yazmak istemiyorsan takma ad kullanabilirsin.',
        style=discord.TextStyle.short,
        required=True
    )
    reason = discord.ui.TextInput(
        label='Neden bu sunucuyu seçtin?',
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Kayıt talebin yetkililere iletildi. Lütfen bekle...", ephemeral=True)
        
        log_channel = interaction.guild.get_channel(config.CHANNELS["ONAY_RED_LOG"])
        if log_channel:
            embed = discord.Embed(title="Yeni Kayıt Talebi", color=discord.Color.purple())
            embed.add_field(name="Kullanıcı", value=interaction.user.mention, inline=False)
            embed.add_field(name="Ad/Takma Ad", value=self.name.value, inline=False)
            embed.add_field(name="Sunucuyu Seçme Nedeni", value=self.reason.value, inline=False)
            embed.set_footer(text=f"ID: {interaction.user.id}")
            
            await log_channel.send(embed=embed, view=KayitOnayRedView())

class KayitBaslatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Kayıt Ol", style=discord.ButtonStyle.blurple, custom_id="kayit_ol_btn")
    async def kayit_ol(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(KayitModal())


class KayitRedModal(discord.ui.Modal, title='Reddetme Sebebi'):
    reason = discord.ui.TextInput(
        label='Bu insancığı reddetme sebebiniz nedir?',
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = int(interaction.message.embeds[0].footer.text.replace("ID: ", ""))
        user = interaction.guild.get_member(user_id)
        
        if user:
            try:
                await user.send(f"Sunucuya kayıt talebiniz reddedildi.\n**Sebep:** {self.reason.value}")
            except:
                pass 

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(name="Durum", value=f"❌ Reddedildi\n**Reddeden Yetkili:** {interaction.user.mention}\n**Sebep:** {self.reason.value}", inline=False)
        
        for item in self.view.children:
            item.disabled = True
            
        await interaction.response.edit_message(embed=embed, view=self.view)

class KayitOnayRedView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.green, custom_id="kayit_onayla")
    async def onayla(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = int(interaction.message.embeds[0].footer.text.replace("ID: ", ""))
        user = interaction.guild.get_member(user_id)
        
        if user:
            katilimci_role = interaction.guild.get_role(config.ROLES["KATILIMCI"])
            kayitsiz_role = interaction.guild.get_role(config.ROLES["KAYITSIZ"])
            
            if katilimci_role: await user.add_roles(katilimci_role)
            if kayitsiz_role: await user.remove_roles(kayitsiz_role)

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.add_field(name="Durum", value=f"✅ Onaylandı\n**Onaylayan Yetkili:** {interaction.user.mention}", inline=False)
        
        for item in self.children:
            item.disabled = True
            
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.red, custom_id="kayit_reddet")
    async def reddet(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = KayitRedModal()
        modal.view = self 
        await interaction.response.send_modal(modal)

class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # View'ları bota ekleyerek restart atılsa bile çalışmasını sağlıyoruz.
        self.bot.add_view(KayitBaslatView())
        self.bot.add_view(KayitOnayRedView())

async def setup(bot):
    await bot.add_cog(Registration(bot))
