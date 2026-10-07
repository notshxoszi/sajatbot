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

CAT_NEV_PANASZ_ELBUGGOLT_SZEF = 1013547790770642998
CAT_INTERIOR = 1013705089476726805
LOG_CHANNEL_ID = 1013544907782246500
RANG_ID = 1557077465325768745
VEZETOSEG_ROLE_NAME = "Vezetőség" 

async def send_log(guild, embed):
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        try:
            await log_channel.send(embed=embed)
        except:
            pass

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket zárása 🔒", style=discord.ButtonStyle.red, custom_id="close_ticket_btn_strict")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        vezetoseg_role = discord.utils.get(interaction.guild.roles, name=VEZETOSEG_ROLE_NAME)
        if not (interaction.user.guild_permissions.administrator or (vezetoseg_role and vezetoseg_role in interaction.user.roles)):
            await interaction.response.send_message("Ezt a ticketet csak a Vezetőség zárhatja le!", ephemeral=True)
            return
        await interaction.response.send_message("A ticket 5 másodperc múlva törlésre kerül...")
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass

class RangGombView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Rang igénylése / elvétele 🎯", style=discord.ButtonStyle.blurple, custom_id="rang_oszto_gomb_unique")
    async def rang_gomb_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(RANG_ID)
        if not role:
            await interaction.response.send_message("A rang nem található!", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"Elvéve: {role.name}", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"Megkapva: {role.name}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot elindult: {bot.user}")
    bot.add_view(CloseTicketView())
    bot.add_view(RangGombView())

@bot.command()
@commands.has_permissions(administrator=True)
async def ranglap(ctx):
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(title="Rang igénylése", description="Kattints a gombra!", color=discord.Color.blurple())
    await ctx.send(embed=embed, view=RangGombView())

@bot.command()
@commands.has_permissions(administrator=True)
async def adminszabalyzat(ctx):
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(title="Adminisztrátori Szabályzat", description="[Kattints ide](https://docs.google.com)", color=discord.Color.blue())
    await ctx.send(embed=embed)

bot.run(os.environ.get("DISCORD_TOKEN"))
