import os
import asyncio
import discord
from discord.ext import commands
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- ID BEÁLLÍTÁSOK ---
CAT_NEV_PANASZ_ELBUGGOLT_SZEF = 1013547790770642998  # Névváltás, Panasz, Elbuggolt, Széf, UB kategória
CAT_INTERIOR = 1013705089476726805                  # Interior kérelem kategória

LOG_CHANNEL_ID = 1013544907782246500
RANG_ID = 1557077465325768745                       # Gombos rang ID

VEZETOSEG_ROLE_NAME = "Vezetőség" 

async def send_log(guild, embed):
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            print(f"Hiba a log küldésekor: {e}")

# ==========================================
# ZÁRÁS VIEW (Csak Vezetőség zárhatja be)
# ==========================================

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket zárása 🔒", style=discord.ButtonStyle.red, custom_id="close_ticket_btn_strict")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        vezetoseg_role = discord.utils.get(interaction.guild.roles, name=VEZETOSEG_ROLE_NAME)
        has_permission = False
        
        if interaction.user.guild_permissions.administrator:
            has_permission = True
        elif vezetoseg_role and vezetoseg_role in interaction.user.roles:
            has_permission = True

        if not has_permission:
            await interaction.response.send_message("Ezt a ticketet csak a **Vezetőség** zárhatja le!", ephemeral=True)
            return

        await interaction.response.send_message("A ticket 5 másodperc múlva törlésre kerül...")
        
        embed = discord.Embed(title="🔴 Szuperadmin segítségnyújtás - Bezárva", color=discord.Color.red(), timestamp=datetime.now())
        embed.add_field(name="Lezárta:", value=f"{interaction.user.mention} ({interaction.user.name})", inline=True)
        embed.add_field(name="Csatorna neve:", value=interaction.channel.name, inline=True)
        await send_log(interaction.guild, embed)

        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass

# ==========================================
# 1. NÉVVÁLTÁS & UB KÉRELEM PANEL
# ==========================================

class NevValtasSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Név-váltás", emoji="💭", description="In-Game név megváltoztatása", value="nev_valtas"),
            discord.SelectOption(label="UB kérelem", emoji="🔓", description="Kitiltás feloldásának kérelmezése", value="ub_kerelem")
        ]
        super().__init__(placeholder="Válassz...", min_values=1, max_values=1, options=options, custom_id="nev_ub_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        valasztott = self.values[0]

        szuro = "név-váltás" if valasztott == "nev_valtas" else "ub-kérelem"
        letezo = discord.utils.find(lambda c: user.name.lower() in c.name and szuro in c.name, guild.text_channels)
        if letezo:
            await interaction.response.send_message(f"Már van egy nyitott ilyen kérelmed: {letezo.mention}", ephemeral=True)
            return

        category = guild.get_channel(CAT_NEV_PANASZ_ELBUGGOLT_SZEF)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        vezetoseg_role = discord.utils.get(guild.roles, name=VEZETOSEG_ROLE_NAME)
        if vezetoseg_role:
            overwrites[vezetoseg_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        if valasztott == "nev_valtas":
            csatorna_nev = f"💭szuperadmin-név-váltás-{user.name}"
            szoveg = (f"Szia! {user.mention} (Szuperadmin segítségnyújtás)\n\n"
                      "**Mi volt az eddigi neved?**\n"
                      "**Mi legyen az új neved?**\n"
                      "**Miért szeretnél nevet változtatni?**")
        else:
            csatorna_nev = f"🔓szuperadmin-ub-kérelem-{user.name}"
            szoveg = (f"Szia! {user.mention} (Szuperadmin segítségnyújtás)\n\n"
                      "**IC Neved / Serialod:**\n"
                      "**Ki bannolt ki és mikor?**\n"
                      "**Miért kapod a bant és miért érdemelsz esélyt?**")

        await interaction.response.send_message("A Szuperadmin segítségnyújtási kérelem megnyitása folyamatban...", ephemeral=True)
        channel = await guild.create_text_channel(name=csatorna_nev, category=category, overwrites=overwrites, reason="Szuperadmin kérelem")
        await channel.send(szoveg, view=CloseTicketView())

        embed = discord.Embed(title="🟢 Szuperadmin segítségnyújtás Nyitva", color=discord.Color.green(), timestamp=datetime.now())
        embed.add_field(name="Típus:", value="Névváltás" if valasztott == "nev_valtas" else "UB Kérelem", inline=True)
        embed.add_field(name="Nyitó:", value=f"{user.mention} ({user.name})", inline=True)
        embed.add_field(name="Csatorna:", value=channel.mention, inline=False)
        await send_log(guild, embed)

class NevValtasView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(NevValtasSelect())

# ==========================================
# 2. PANASZ PANEL
# ==========================================

class PanaszSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Frakció panasz", emoji="❌", description="Panasz tétele egy frakcióra", value="frakcio_panasz"),
            discord.SelectOption(label="Admin panasz", emoji="❌", description="Panasz tétele egy adminisztrátorra", value="admin_panasz")
        ]
        super().__init__(placeholder="Válassz panasz típust...", min_values=1, max_values=1, options=options, custom_id="panasz_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        valasztott = self.values[0]

        letezo = discord.utils.find(lambda c: user.name.lower() in c.name and "panasz" in c.name, guild.text_channels)
        if letezo:
            await interaction.response.send_message(f"Már van egy nyitott panaszod: {letezo.mention}", ephemeral=True)
            return

        category = guild.get_channel(CAT_NEV_PANASZ_ELBUGGOLT_SZEF)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        vezetoseg_role = discord.utils.get(guild.roles, name=VEZETOSEG_ROLE_NAME)
        if vezetoseg_role:
            overwrites[vezetoseg_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        if valasztott == "frakcio_panasz":
            csatorna_nev = f"❌szuperadmin-frakció-panasz-{user.name}"
            szoveg = (f"Szia! {user.mention} (Szuperadmin segítségnyújtás)\n\n"
                      "**IC neved:**\n"
                      "**Frakció neve:**\n"
                      "**Részletes indok:**\n"
                      "**Bizonyíték:**")
        else:
            csatorna_nev = f"❌szuperadmin-admin-panasz-{user.name}"
            szoveg = (f"Szia! {user.mention} (Szuperadmin segítségnyújtás)\n\n"
                      "**IC Neved:**\n"
                      "**Admin Neve:**\n"
                      "**Részletes indok:**\n"
                      "**Bizonyíték:**")

        await interaction.response.send_message("A panasz csatorna létrehozása folyamatban...", ephemeral=True)
        channel = await guild.create_text_channel(name=csatorna_nev, category=category, overwrites=overwrites, reason="Szuperadmin Panasz")
        await channel.send(szoveg, view=CloseTicketView())

        embed = discord.Embed(title="🟢 Szuperadmin Panasz Nyitva", color=discord.Color.red(), timestamp=datetime.now())
        embed.add_field(name="Benyújtotta:", value=f"{user.mention} ({user.name})", inline=True)
        embed.add_field(name="Csatorna:", value=channel.mention, inline=False)
        await send_log(guild, embed)

class PanaszPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PanaszSelect())

# ==========================================
# 3. INTERIOR KÉRELEM PANEL
# ==========================================

class InteriorSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Interior kérelem", emoji="🏠", description="Ház, garázs interior lerakása", value="interior_igenyles")
        ]
        super().__init__(placeholder="Válassz...", min_values=1, max_values=1, options=options, custom_id="interior_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        letezo = discord.utils.find(lambda c: user.name.lower() in c.name and "interior" in c.name, guild.text_channels)
        if letezo:
            await interaction.response.send_message(f"Már van egy nyitott interior kérelmed: {letezo.mention}", ephemeral=True)
            return

        category = guild.get_channel(CAT_INTERIOR)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        vezetoseg_role = discord.utils.get(guild.roles, name=VEZETOSEG_ROLE_NAME)
        if vezetoseg_role:
            overwrites[vezetoseg_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        csatorna_nev = f"🏠szuperadmin-interior-kérelem-{user.name}"
        szoveg = (f"Szia! {user.mention} (Szuperadmin segítségnyújtás)\n\n"
                  "**IC Neved:**\n"
                  "**Ház vagy garázs interior lerakása:**\n"
                  "**Pontos helyszín (kép / F11 térkép):**")

        await interaction.response.send_message("Az interior kérelem csatorna létrehozása folyamatban...", ephemeral=True)
        channel = await guild.create_text_channel(name=csatorna_nev, category=category, overwrites=overwrites, reason="Szuperadmin Interior")
        await channel.send(szoveg, view=CloseTicketView())

        embed = discord.Embed(title="🟢 Szuperadmin Interior Kérelem Nyitva", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Benyújtotta:", value=f"{user.mention} ({user.name})", inline=True)
        embed.add_field(name="Csatorna:", value=channel.mention, inline=False)
        await send_log(guild, embed)

class InteriorPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(InteriorSelect())

# ==========================================
# 4. ELBUGGOLT TÁRGYAK PANEL
# ==========================================

class ElbuggoltSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="El buggolt tárgyak", emoji="📦", description="El buggolt tárgyak bejelentése", value="elbuggolt_targyak")
        ]
        super().__init__(placeholder="Válassz...", min_values=1, max_values=1, options=options, custom_id="elbuggolt_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        letezo = discord.utils.find(lambda c: user.name.lower() in c.name and "elbuggolt" in c.name, guild.text_channels)
        if letezo:
            await interaction.response.send_message(f"Már van egy nyitott elbuggolt tárgyas ticketed: {letezo.mention}", ephemeral=True)
            return

        category = guild.get_channel(CAT_NEV_PANASZ_ELBUGGOLT_SZEF)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        vezetoseg_role = discord.utils.get(guild.roles, name=VEZETOSEG_ROLE_NAME)
        if vezetoseg_role:
            overwrites[vezetoseg_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        csatorna_nev = f"📦szuperadmin-elbuggolt-tárgyak-{user.name}"
        szoveg = (f"Szia! {user.mention} (Szuperadmin segítségnyújtás)\n\n"
                  "**IC Neved:**\n"
                  "**Mi buggolt el és hogyan?**\n"
                  "**Bizonyíték (Kép / Videó / Log):**")

        await interaction.response.send_message("A csatorna létrehozása folyamatban...", ephemeral=True)
        channel = await guild.create_text_channel(name=csatorna_nev, category=category, overwrites=overwrites, reason="Szuperadmin Elbuggolt")
        await channel.send(szoveg, view=CloseTicketView())

        embed = discord.Embed(title="🟢 Szuperadmin El buggolt tárgyak Nyitva", color=discord.Color.purple(), timestamp=datetime.now())
        embed.add_field(name="Benyújtotta:", value=f"{user.mention} ({user.name})", inline=True)
        embed.add_field(name="Csatorna:", value=channel.mention, inline=False)
        await send_log(guild, embed)

class ElbuggoltPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ElbuggoltSelect())

# ==========================================
# 5. SZÉF KÉRVÉNYEZÉS PANEL
# ==========================================

class SzefSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Széf kérvényezés", emoji="💰", description="Széf igénylése", value="szef_kervenyezes")
        ]
        super().__init__(placeholder="Válassz...", min_values=1, max_values=1, options=options, custom_id="szef_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        letezo = discord.utils.find(lambda c: user.name.lower() in c.name and "széf" in c.name, guild.text_channels)
        if letezo:
            await interaction.response.send_message(f"Már van egy nyitott széf kérvényed: {letezo.mention}", ephemeral=True)
            return

        category = guild.get_channel(CAT_NEV_PANASZ_ELBUGGOLT_SZEF)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        vezetoseg_role = discord.utils.get(guild.roles, name=VEZETOSEG_ROLE_NAME)
        if vezetoseg_role:
            overwrites[vezetoseg_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        csatorna_nev = f"💰szuperadmin-széf-kérvényezés-{user.name}"
        szoveg = (f"Szia! {user.mention} (Szuperadmin segítségnyújtás)\n\n"
                  "**IC Neved:**\n"
                  "**Hova szeretnéd a széfet (Interior ID / Helyszín):**\n"
                  "**Indoklás:**")

        await interaction.response.send_message("A csatorna létrehozása folyamatban...", ephemeral=True)
        channel = await guild.create_text_channel(name=csatorna_nev, category=category, overwrites=overwrites, reason="Szuperadmin Széf")
        await channel.send(szoveg, view=CloseTicketView())

        embed = discord.Embed(title="🟢 Szuperadmin Széf Kérvényezés Nyitva", color=discord.Color.gold(), timestamp=datetime.now())
        embed.add_field(name="Benyújtotta:", value=f"{user.mention} ({user.name})", inline=True)
        embed.add_field(name="Csatorna:", value=channel.mention, inline=False)
        await send_log(guild, embed)

class SzefPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SzefSelect())

# ==========================================
# 6. RANG ADÓS GOMB RENDSZER
# ==========================================

class RangGombView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Rang igénylése / elvétele 🎯", style=discord.ButtonStyle.blurple, custom_id="rang_oszto_gomb_unique")
    async def rang_gomb_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        role = guild.get_role(RANG_ID)
        if not role:
            await interaction.response.send_message("Hiba: A megadott rang nem található a szerveren!", ephemeral=True)
            return

        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(f"Sikeresen elvettem tőled a(z) **{role.name}** rangot!", ephemeral=True)
        else:
            await member.add_roles(role)
            await interaction.response.send_message(f"Sikeresen megkaptad a(z) **{role.name}** rangot!", ephemeral=True)

# ==========================================
# 7. LOGOLÁSI EVENTEK
# ==========================================

@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild:
        return
    embed = discord.Embed(title="🗑️ Üzenet Törölve", color=discord.Color.orange(), timestamp=datetime.now())
    embed.add_field(name="Szerző:", value=f"{message.author.mention} ({message.author.name})", inline=True)
    embed.add_field(name="Csatorna:", value=message.channel.mention, inline=True)
    tartalom = message.content if message.content else "*Nincs szöveges tartalom*"
    embed.add_field(name="Tartalom:", value=tartalom, inline=False)
    await send_log(message.guild, embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or not before.guild or before.content == after.content:
        return
    embed = discord.Embed(title="✏ Üzenet Szerkesztve", color=discord.Color.blue(), timestamp=datetime.now())
    embed.add_field(name="Szerző:", value=f"{before.author.mention} ({before.author.name})", inline=True)
    embed.add_field(name="Csatorna:", value=before.channel.mention, inline=True)
    embed.add_field(name="Előtte:", value=before.content or "*Üres*", inline=False)
    embed.add_field(name="Utána:", value=after.content or "*Üres*", inline=False)
    await send_log(before.guild, embed)

@bot.event
async def on_ready():
    print(f"A bot sikeresen elindult! Bejelentkezve mint: {bot.user}")
    bot.add_view(NevValtasView())
    bot.add_view(PanaszPanelView())
    bot.add_view(InteriorPanelView())
    bot.add_view(ElbuggoltPanelView())
    bot.add_view(SzefPanelView())
    bot.add_view(CloseTicketView())
    bot.add_view(RangGombView())

# ==========================================
# PARANCSOK A PANELEK KIHELYEZÉSÉHEZ
# ==========================================

@bot.command()
@commands.has_permissions(administrator=True)
async def nevpanel(ctx):
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(title="Szuperadmin segítségnyújtás", description="Válassz a Név-váltás vagy UB kérelem között!", color=discord.Color.dark_theme())
    await ctx.send(embed=embed, view=NevValtasView())

@bot.command()
@commands.has_permissions(administrator=True)
async def panaszpanel(ctx):
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(title="Panasztétel", description="Válaszd ki a panasz típusát az alábbi menüből!", color=discord.Color.dark_theme())
    await ctx.send(embed=embed, view=PanaszPanelView())

@bot.command()
@commands.has_permissions(administrator=True)
async def interiorpanel(ctx):
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(title="Interior kérelem", description="Ház, garázs interior lerakása", color=discord.Color.dark_theme())
    await ctx.send(embed=embed, view=InteriorPanelView())

@bot.command()
@commands.has_permissions(administrator=True)
async def elbuggoltpanel(ctx):
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(title="El buggolt tárgyak", description="Kattints a menüre elbuggolt tárgyak bejelentéséhez!", color=discord.Color.dark_theme())
    await ctx.send(embed=embed, view=ElbuggoltPanelView())

@bot.command()
@commands.has_permissions(administrator=True)
async def szefpanel(ctx):
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(title="Széf kérvényezés", description="Kattints a menüre széf igényléséhez!", color=discord.Color.dark_theme())
    await ctx.send(embed=embed, view=SzefPanelView())

@bot.command()
@commands.has_permissions(administrator=True)
async def ranglap(ctx):
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(title="Rang igénylése", description="Kattints a gombra a rang felvételéhez/elvételéhez!", color=discord.Color.blurple())
    await ctx.send(embed=embed, view=RangGombView())

@bot.command()
@commands.has_permissions(administrator=True)
async def adminszabalyzat(ctx):
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(
        title="Adminisztrátori Szabályzat", 
        description="Itt találod a hivatalos adminisztrátori szabályzatot.\n\n👉 [Kattints ide a megtekintéshez](https://docs.google.com/document/d/19Uxmd9DUWrNIVKy2NF14bc7y8sUAyDyBfOaZ7RE8EUM/edit?usp=sharing)",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.