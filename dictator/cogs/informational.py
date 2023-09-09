import discord
from discord import app_commands
from discord.ext import commands

from db_manager import db_connection as db_conn
from datetime import datetime, timezone
import math
import humanize


class Informational(commands.Cog):
    def __init__(self, dictator: commands.Bot) -> None:
        self.dictator = dictator

    # If importing this into another cog, should I have made another class for the function so that then only that class could be imported?
    def info_embed(self, interaction: discord.Interaction, user: discord.User):
        with db_conn() as db:
            db.execute(
                f"SELECT time_played, blocked, email, last_activity FROM ticketServer_tickets WHERE discord_id = '{user.id}'"
            )
            user_info = db.fetchone()

        # No account found for user
        if not user_info:
            embed = discord.Embed(
                title=f"No results for the user '{user.mention}'.", colour=0xFFBB35
            )
            return embed

        # User hasn't lived any lives
        if user_info[0] == 0:
            embed = discord.Embed(
                title=f"'{user.name}' (or {user_info[2]}) has not lived any lives yet.",
                colour=0xFFBB35,
            )
            return embed

        member = interaction.guild.get_member(user.id)

        # Time formatting
        last_active = user_info[3].replace(tzinfo=timezone.utc)
        now = discord.utils.utcnow()
        difference = humanize.naturaltime(now - last_active)
        joined_guild = humanize.naturaltime(now - member.joined_at)

        # Form embed
        embed = discord.Embed(
            title=f"Results for the user '{user.name}':", colour=0xFFBB35
        )
        embed.add_field(
            name="Time played:",
            value=f"{math.floor(user_info[0]/60)}h {user_info[0]%60}m",
        )
        embed.add_field(name="Blocked:", value="Yes" if user_info[1] else "No")
        embed.add_field(
            name="Joined guild:", value=f"{joined_guild}" if member else "Unknown"
        )
        embed.add_field(name="Username:", value=user_info[2])
        embed.add_field(name="Last activity:", value=f"{difference}")
        embed.set_footer(text="Data range: August 2019 - Current")

        return embed

    @app_commands.command()
    async def rtfm(self, interaction: discord.Interaction) -> None:
        """Sends basic infoamtion about playing for the first time."""

        await interaction.response.send_message(
            f'How do I play?\nHow do I download?\n\nHeres the manual to play for the first time\n<https://twohoursonelife.com/first-time-playing/?ref=rtfm>\n\nCheck your messages from me to find your username and password.\n*Can\'t find the message? Use the "/account" command.*'
        )

    @app_commands.guild_only()
    @app_commands.command()
    async def info(self, interaction: discord.Interaction, user: discord.User) -> None:
        """Private messages you information about the specified user."""
        embed = self.info_embed(user)
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(dictator: commands.Bot) -> None:
    await dictator.add_cog(Informational(dictator))
