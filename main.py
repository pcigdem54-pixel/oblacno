import discord
from discord.ext import commands
import config
from datetime import datetime

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
        # Embed'den kullanıcı ID'sini al
        user_id = int(interaction.message.embeds[0].footer.text.replace("ID: ", ""))
        user = interaction.guild.get_member(user_id)
        
        # Kullanıcıya DM at
        if user:
            try:
                await user.send(f"Sunucuya kayıt talebiniz reddedildi.\n**Sebep:** {self.reason.value}")
            except:
                pass # DM kapalıysa yoksay

        # Mesajı güncelle
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(name="Durum", value=f"❌ Reddedildi\n**Reddeden Yetkili:** {interaction.user.mention}\n**Sebep:** {self.reason.value}", inline=False)
        
        # Butonları devre dışı bırak
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
            # Rolleri düzenle
            katilimci_role = interaction.guild.get_role(config.ROLES["KATILIMCI"])
            kayitsiz_role = interaction.guild.get_role(config.ROLES["KAYITSIZ"])
            
            if katilimci_role: await user.add_roles(katilimci_role)
            if kayitsiz_role: await user.remove_roles(kayitsiz_role)

        # Mesajı güncelle
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.add_field(name="Durum", value=f"✅ Onaylandı\n**Onaylayan Yetkili:** {interaction.user.mention}", inline=False)
        
        for item in self.children:
            item.disabled = True
            
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.red, custom_id="kayit_reddet")
    async def reddet(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = KayitRedModal()
        modal.view = self # Modal kapandığında view'ı güncellemek için referans veriyoruz
        await interaction.response.send_modal(modal)


# ---------------- YARDIM SİSTEMİ ----------------

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
        
        # Yetkiliyi ve kullanıcıyı odaya çek
        try:
            if interaction.user.voice:
                await interaction.user.move_to(yardim_odasi)
            await user.move_to(yardim_odasi)
            await user.edit(mute=False) # Susturmayı kaldır
        except Exception as e:
            await interaction.response.send_message("Üyeler taşınırken bir hata oluştu.", ephemeral=True)
            return

        # Orijinal mesajı güncelle
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.description = f"✅ {interaction.user.mention} tarafından devralındı."
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

        # Yardım bitirme kontrol mesajı gönder
        yeni_embed = discord.Embed(title="Destek Görüşmesi Aktif", description=f"Yetkili: {interaction.user.mention}\nKullanıcı: {user.mention}", color=discord.Color.blue())
        yeni_embed.set_footer(text=f"ID: {user_id}")
        await interaction.channel.send(content=interaction.user.mention, embed=yeni_embed, view=YardimBitirView())


    @discord.ui.button(label="Beklemeden Çıkar", style=discord.ButtonStyle.red, custom_id="yardim_cikar")
    async def cikar(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = int(interaction.message.embeds[0].footer.text.replace("ID: ", ""))
        user = interaction.guild.get_member(user_id)
        
        if user and user.voice:
            await user.move_to(None) # Sesten at
            
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
        
        # Kullanıcıyı sesten at
        if user and user.voice:
            await user.move_to(None)
            
        # Modlog'a logla
        modlog = interaction.guild.get_channel(config.CHANNELS["MODLOG"])
        if modlog:
            log_embed = discord.Embed(title="Yardım Talebi Sonuçlandı", color=discord.Color.green())
            log_embed.add_field(name="Yetkili", value=interaction.user.mention)
            log_embed.add_field(name="Kullanıcı", value=user.mention if user else f"<@{user_id}>")
            log_embed.add_field(name="Çözüm/Açıklama", value=self.reason.value, inline=False)
            await modlog.send(embed=log_embed)

        # Mesajı kilitle
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


# ---------------- TICKET SİSTEMİ ----------------

class TicketKapatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Bileti Kapat", style=discord.ButtonStyle.red, custom_id="ticket_kapat")
    async def bilet_kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Bilet kapatılıyor...", ephemeral=True)
        
        # Kanalın açıklamasından (topic) kullanıcı id'sini çekiyoruz
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
        
        # İzinleri ayarla
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        # Yetkilileri ekle
        for role_id in [config.ROLES["ADMIN"], config.ROLES["MODERATOR"], config.ROLES["MEKAN_SAHIBI"]]:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                
        # Kanal oluştur
        ticket_channel = await interaction.guild.create_text_channel(
            name=f"bilet-{interaction.user.name}",
            category=category,
            overwrites=overwrites,
            topic=str(interaction.user.id) # Kapatırken ID'yi bulmak için topic'e yazıyoruz
        )
        
        # Ticket kanalına mesaj gönder
        etiketler = f"<@&{config.ROLES['ADMIN']}> <@&{config.ROLES['MODERATOR']}>"
        embed = discord.Embed(title="Yeni Bilet", description=f"Hoş geldin {interaction.user.mention}, sorununuzu buraya yazabilirsiniz. Yetkililer en kısa sürede ilgilenecektir.", color=discord.Color.blue())
        await ticket_channel.send(content=etiketler, embed=embed, view=TicketKapatView())
        
        await interaction.response.send_message(f"Biletin oluşturuldu: {ticket_channel.mention}", ephemeral=True)


# ---------------- BOT ANA KURULUM ----------------

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Butonların bot yeniden başladığında çalışmaya devam etmesi için view'ları ekliyoruz.
        self.add_view(KayitBaslatView())
        self.add_view(KayitOnayRedView())
        self.add_view(YardimBeklemeView())
        self.add_view(YardimBitirView())
        self.add_view(TicketBaslatView())
        self.add_view(TicketKapatView())

bot = MyBot()

@bot.event
async def on_ready():
    print(f"{bot.user} olarak giriş yapıldı!")
    
    # 1. Kayıt kanalına mesaj at (Eğer yoksa)
    kayit_kanali = bot.get_channel(config.CHANNELS["KAYIT_MESAJ"])
    if kayit_kanali:
        async for msg in kayit_kanali.history(limit=5):
            if msg.author == bot.user:
                break
        else:
            embed = discord.Embed(
                title="Sunucumuza Hoş Geldin!",
                description="Aramıza katılmak ve içeriklere erişmek için aşağıdaki **Kayıt Ol** butonuna basarak kısa anketimizi doldurabilirsin 🌸",
                color=discord.Color.magenta() # Pembe-mor arası bir renk
            )
            await kayit_kanali.send(embed=embed, view=KayitBaslatView())

    # 2. Ticket kanalına mesaj at (Eğer yoksa)
    ticket_kanali = bot.get_channel(config.CHANNELS["TICKET_MESAJ"])
    if ticket_kanali:
        async for msg in ticket_kanali.history(limit=5):
            if msg.author == bot.user:
                break
        else:
            embed = discord.Embed(
                title="Destek Talebi Oluştur",
                description="Yetkililerle özel olarak görüşmek, bir sorunu bildirmek veya yardım almak için aşağıdaki **Bilet Aç** butonuna tıklayabilirsin ✨",
                color=discord.Color.teal()
            )
            await ticket_kanali.send(embed=embed, view=TicketBaslatView())


@bot.event
async def on_member_join(member):
    # Sunucuya katılana Kayıtsız rolü ver
    kayitsiz_role = member.guild.get_role(config.ROLES["KAYITSIZ"])
    if kayitsiz_role:
        await member.add_roles(kayitsiz_role)

@bot.event
async def on_voice_state_update(member, before, after):
    # Kullanıcı yardım bekleme odasına girdiyse
    if after.channel and after.channel.id == config.CHANNELS["YARDIM_BEKLEME_SES"]:
        # Kullanıcıyı sustur
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

if __name__ == "__main__":
    bot.run(config.TOKEN)
