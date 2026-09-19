import discord
from discord.ext import commands
import config

class YardimBeklemeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Katılımcıyı Devral", style=discord.ButtonStyle.green, custom_id="yardim_devral")
    async def devral(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = int(interaction.message.embeds[0].footer.text.replace("ID: ", ""))
        user = interaction.guild.get_member(user_id)
        
        if not user or not user.voice:
            await interaction.response.send_message("Kullanıcı artık seste değil.", ephemeral=True)
            return

        yardim_odasi = interaction.guild.get_channel(config.CHANNELS["YARDIM_ODASI_SES"])
        
        try:
            if interaction.user.voice:
                await interaction.user.move_to(yardim_odasi)
            await user.move_to(yardim_odasi)
            await user.edit(mute=False) 
        except Exception as e:
            await interaction.response.send_message("Üyeler taşınırken bir hata oluştu.", ephemeral=True)
            return

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.description = f"✅ {interaction.user.mention} tarafından devralındı."
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

        yeni_embed = discord.Embed(title="Destek Görüşmesi Aktif", description=f"Yetkili: {interaction.user.mention}\nKullanıcı: {user.mention}", color=discord.Color.blue())
        yeni_embed.set_footer(text=f"ID: {user_id}")
        await interaction.channel.send(content=interaction.user.mention, embed=yeni_embed, view=YardimBitirView())


    @discord.ui.button(label="Beklemeden Çıkar", style=discord.ButtonStyle.red, custom_id="yardim_cikar")
    async def cikar(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = int(interaction.message.embeds[0].footer.text.replace("ID: ", ""))
        user = interaction.guild.get_member(user_id)
        
        if user and user.voice:
            await user.move_to(None)
            
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.description = f"❌ {interaction.user.mention} tarafından sesten atıldı."
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

class YardimBitirModal(discord.ui.Modal, title='Desteği Sonlandır'):
    reason = discord.ui.TextInput(
        label='Sorun nasıl çözüldü?',
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = int(interaction.message.embeds[0].footer.text.replace("ID: ", ""))
        user = interaction.guild.get_member(user_id)
        
        if user and user.voice:
            await user.move_to(None)
            
        modlog = interaction.guild.get_channel(config.CHANNELS["MODLOG"])
        if modlog:
            log_embed = discord.Embed(title="Yardım Talebi Sonuçlandı", color=discord.Color.green())
            log_embed.add_field(name="Yetkili", value=interaction.user.mention)
            log_embed.add_field(name="Kullanıcı", value=user.mention if user else f"<@{user_id}>")
            log_embed.add_field(name="Çözüm/Açıklama", value=self.reason.value, inline=False)
            await modlog.send(embed=log_embed)

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.dark_grey()
        embed.title = "Destek Görüşmesi Bitti"
        for item in self.view.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self.view)

class YardimBitirView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Desteği Bitir", style=discord.ButtonStyle.green, custom_id="yardim_bitir")
    async def bitir(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = YardimBitirModal()
        modal.view = self
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Boş", style=discord.ButtonStyle.grey, custom_id="yardim_bos")
    async def bos(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = int(interaction.message.embeds[0].footer.text.replace("ID: ", ""))
        user = interaction.guild.get_member(user_id)
        
        if user and user.voice:
            await user.move_to(None)

        modlog = interaction.guild.get_channel(config.CHANNELS["MODLOG"])
        if modlog:
            log_embed = discord.Embed(title="Yardım Talebi Sonuçlandı (BOŞ)", color=discord.Color.light_grey())
            log_embed.add_field(name="Yetkili", value=interaction.user.mention)
            log_embed.add_field(name="Kullanıcı", value=user.mention if user else f"<@{user_id}>")
            log_embed.add_field(name="Durum", value="Kullanıcı ses vermedi veya troll olarak işaretlendi.", inline=False)
            await modlog.send(embed=log_embed)

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.dark_grey()
        embed.title = "Destek Görüşmesi Bitti (BOŞ)"
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

class HelpSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(YardimBeklemeView())
        self.bot.add_view(YardimBitirView())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Kullanıcı yardım bekleme odasına girdiyse
        if after.channel and after.channel.id == config.CHANNELS["YARDIM_BEKLEME_SES"]:
            try:
                await member.edit(mute=True)
            except:
                pass
                
            yardim_log = member.guild.get_channel(config.CHANNELS["YARDIM_LOG"])
            if yardim_log:
                etiketler = f"<@&{config.ROLES['ADMIN']}> <@&{config.ROLES['MODERATOR']}>"
                embed = discord.Embed(
                    title="Yeni Yardım Talebi (Sesli)",
                    description=f"{member.mention} yardım bekleme odasına katıldı ve susturuldu. İlgilenmek için aşağıdaki butonları kullanabilirsiniz.",
                    color=discord.Color.orange()
                )
                embed.set_footer(text=f"ID: {member.id}")
                
                await yardim_log.send(content=etiketler, embed=embed, view=YardimBeklemeView())

async def setup(bot):
    await bot.add_cog(HelpSystem(bot))
