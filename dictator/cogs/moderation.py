import discord
from discord import app_commands
from discord.ext import commands

from db_manager import db_connection as db_conn
from constants import LOG_CHANNEL_ID, GAME_MOD_ROLE_ID, MOD_ROLE_ID

from datetime import datetime, timezone
import re
import humanize


def here_goes_nothing(user_info):
    embed = discord.Embed(title="Please Work", colour=discord.Colour.dark_purple())
    embed.add_field(name="Name:", value=f"{user_info}", inline=True)
    return embed


class TestButton(discord.ui.Button):
    def __init__(
        self, button_name, member_name
    ):  # you can pass label here, if you are using a for loop to create bunch buttons
        super().__init__(
            style=discord.ButtonStyle.blurple, label=button_name
        )  # , style, row, or anything that could be found in docs
        self.button_name = button_name
        self.member_name = member_name

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=here_goes_nothing(self.member_name)
        )  # What happens when you click the button. Will need to become function call to send user info embed


# Bring it into the view
class TestView(discord.ui.View):
    def __init__(self, member_info):
        super().__init__(
            timeout=180.0,
        )  # same thing here
        for name in member_info:
            self.add_item(
                TestButton(f"Info {name[2]}", name[0])
            )  # This is creating instances of the button based on how many results were returned.


class Admin(commands.Cog):
    def __init__(self, dictator: commands.Bot) -> None:
        self.dictator = dictator

    @app_commands.checks.has_role(GAME_MOD_ROLE_ID)
    @app_commands.command()
    async def ban(
        self,
        interaction: discord.Interaction,
        username: str,
        reason: str = "The ban hammer has spoken.",
    ) -> None:
        """Bans a user from the game."""
        await interaction.response.send_message(
            f"Banning `{username}` for `{reason}`...", ephemeral=True, delete_after=15
        )

        log_channel = self.dictator.get_channel(LOG_CHANNEL_ID)

        username = self.username_is_player_id(username)

        # if not self.valid_username_format(username):
        #     await interaction.user.send(f"Invalid username format: `{username}`")
        #     raise commands.UserInputError

        # Is user already banned?
        with db_conn() as db:
            db.execute(
                f"SELECT blocked, discord_id FROM ticketServer_tickets WHERE email = '{username}'"
            )
            row = db.fetchone()

        if row == None:
            await interaction.edit_original_response(
                content=f"Could not find an account with the username: `{username}`"
            )
            return

        if row[0] == 1:
            print(
                f"{interaction.user} tried to ban {username} but they're already banned."
            )
            await interaction.edit_original_response(
                content=f"`{username}` is already banned."
            )
            return

        # Ban the user
        with db_conn() as db:
            db.execute(
                f"UPDATE ticketServer_tickets SET blocked = 1 WHERE email = '{username}'"
            )

        print(f"{interaction.user} banned {username} for: {reason}")

        discord_user = interaction.guild.get_member(int(row[1]))

        # Notify the user
        try:
            embed = discord.Embed(
                title="You were banned from 2HOL", colour=discord.Colour.red()
            )
            embed.add_field(name="Reason:", value=f"{reason}", inline=True)
            await discord_user.send(embed=embed)

        except:
            # Message can fail if the user does not allow messages from anyone
            notify_user = False

        else:
            notify_user = True

        # Embed log
        embed = discord.Embed(
            title="Banned a user from the game", colour=discord.Colour.red()
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)
        embed.add_field(name="Member:", value=f"{discord_user.name}", inline=True)
        embed.add_field(name="Username:", value=f"{username}", inline=True)
        embed.add_field(name="Reason:", value=f"{reason}", inline=True)
        embed.add_field(
            name="Notification:",
            value="Successful" if notify_user else "Failed",
            inline=True,
        )
        embed.set_footer(
            text=f"Member ID: {discord_user.id}", icon_url=discord_user.avatar
        )
        await log_channel.send(embed=embed)

    @app_commands.checks.has_role(GAME_MOD_ROLE_ID)
    @app_commands.command()
    async def unban(
        self,
        interaction: discord.Interaction,
        username: str,
        reason: str = "It's your lucky day!",
    ) -> None:
        """Unbans a user from the game."""
        await interaction.response.send_message(
            f"Unbanning `{username}` for `{reason}`...", ephemeral=True, delete_after=15
        )

        log_channel = self.dictator.get_channel(LOG_CHANNEL_ID)

        username = self.username_is_player_id(username)

        # if not self.valid_username_format(username):
        #     await interaction.user.send(f"Invalid username format: `{username}`")
        #     raise commands.UserInputError

        # Check that user is banned
        with db_conn() as db:
            db.execute(
                f"SELECT blocked, discord_id FROM ticketServer_tickets WHERE email = '{username}'"
            )
            row = db.fetchone()

        if row == None:
            await interaction.edit_original_response(
                content=f"Could not find an account with the username: `{username}`"
            )
            return

        if row[0] == 0:
            print(
                f"{interaction.user} tried to unban {username} but they're not already banned."
            )
            await interaction.edit_original_response(
                f"`{username}` is not already banned."
            )
            return

        # Unban the user
        with db_conn() as db:
            db.execute(
                f"UPDATE ticketServer_tickets SET blocked = 0 WHERE email = '{username}'"
            )

        print(f"{interaction.user} unbanned {username} for: {reason}")

        discord_user = interaction.guild.get_member(int(row[1]))

        # Notify the user
        try:
            embed = discord.Embed(
                title="You were unbanned from 2HOL", colour=discord.Colour.green()
            )
            embed.add_field(name="Reason:", value=f"{reason}", inline=True)
            await discord_user.send(embed=embed)

        except:
            # Message can fail if the user does not allow messages from anyone
            notify_user = False

        else:
            notify_user = True

        # Embed log
        embed = discord.Embed(
            title="Unbanned a user from the game", colour=discord.Colour.green()
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)
        embed.add_field(name="Member:", value=f"{discord_user.name}", inline=True)
        embed.add_field(name="Username:", value=f"{username}", inline=True)
        embed.add_field(name="Reason:", value=f"{reason}", inline=True)
        embed.add_field(
            name="Notification:",
            value="Successful" if notify_user else "Failed",
            inline=True,
        )
        embed.set_footer(
            text=f"Member ID: {discord_user.id}", icon_url=discord_user.avatar
        )
        await log_channel.send(embed=embed)

    @app_commands.checks.has_role(MOD_ROLE_ID)
    @app_commands.command()
    async def regenerate(
        self, interaction: discord.Interaction, user: discord.User
    ) -> None:
        """Regenerates a users key."""
        await interaction.response.send_message(
            f"Regenerating key for {user.mention}.", ephemeral=True, delete_after=15
        )

        log_channel = self.dictator.get_channel(LOG_CHANNEL_ID)

        key = await self.dictator.get_cog("User").create_key()

        with db_conn() as db:
            db.execute(
                f"UPDATE ticketServer_tickets SET login_key = '{key}' WHERE discord_id = '{user.id}'"
            )

        # Notify the user
        try:
            embed = discord.Embed(
                title="Your key to access 2HOL has been regenerated.",
                colour=discord.Colour.green(),
            )
            await user.send(embed=embed)

        except:
            notify_user = False

        else:
            notify_user = True

        # Embed log
        embed = discord.Embed(
            title="Member key regenerated", colour=discord.Colour.green()
        )
        embed.add_field(name="Member:", value=f"{user.mention}", inline=True)
        embed.add_field(
            name="Moderator:", value=f"{interaction.user.mention}", inline=True
        )
        embed.add_field(
            name="User notification:",
            value="Successful" if notify_user else "Failed",
            inline=True,
        )
        await log_channel.send(embed=embed)

    @app_commands.checks.has_role(GAME_MOD_ROLE_ID)
    @app_commands.command()
    async def whowas(
        self, interaction: discord.Interaction, character_name: str
    ) -> None:
        """Look up who a player was in the game."""
        await interaction.response.defer()

        # Result limt, due to embed length limitations, the maxium is 8.
        history = 5

        player_id = None

        # Safe characters only
        character_name = re.sub(("[^a-zA-Z0-9 ]"), "", character_name)

        if self.is_int(character_name):
            # character_name is a player life ID, retrieve the associated character name.
            player_id = character_name
            with db_conn() as db:
                """
                A player life ID can be repeated between different servers.
                We have made use of a single server for four years and do not intend to change this in the short term, so are largely unaffected by this.
                To resolve this, we assume we're only interested in the most recent player who lived with this ID.
                This is achieved with 'ORDER BY death_time DESC LIMIT 1'
                """
                db.execute(
                    f"SELECT lineageServer_lives.name FROM lineageServer_lives WHERE player_id = {character_name} ORDER BY death_time DESC LIMIT 1"
                )
                character_name = db.fetchone()

            if not character_name:
                embed = discord.Embed(
                    title=f"No results for that player ID.", colour=0xFFBB35
                )
                await interaction.followup.send(embed=embed)
                return
            else:
                # We really only want the first result of the tuple
                character_name = character_name[0]

        with db_conn() as db:
            # I don't understand why I need to use %s instead of F strings. But it doesn't work otherwise.
            db.execute(
                "SELECT ticketServer_tickets.discord_id, lineageServer_lives.death_time, lineageServer_users.email, lineageServer_lives.id, ticketServer_tickets.time_played FROM lineageServer_lives INNER JOIN lineageServer_users ON lineageServer_lives.user_id = lineageServer_users.id INNER JOIN ticketServer_tickets ON lineageServer_users.email = ticketServer_tickets.email WHERE name = %s ORDER BY death_time DESC LIMIT %s",
                (character_name, history),
            )
            users = db.fetchall()

        if not users:
            embed = discord.Embed(
                title=f"No results for the character '{character_name}'.",
                description=f"Found name '{character_name}' from Player ID '{player_id}'"
                if player_id
                else "",
                colour=0xFFBB35,
            )
            await interaction.followup.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"Latest {history} results for the name '{character_name}':",
            description=f"Found name '{character_name}' from Player ID '{player_id}'"
            if player_id
            else "",
            colour=0xFFBB35,
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)

        for u in users:
            try:
                found_user = await self.dictator.fetch_user(u[0])

            except:
                raise commands.CommandError

            else:
                # Format death time as timezone aware
                death_time = u[1].replace(tzinfo=timezone.utc)
                difference = humanize.naturaltime(discord.utils.utcnow() - death_time)
                embed.add_field(name="Username:", value=f"{u[2]}", inline=True)
                embed.add_field(name="Member:", value=f"{found_user}", inline=True)
                embed.add_field(name="Died:", value=f"{difference}", inline=True)

        if len(users) < history:
            embed.add_field(name="\u200b", value="End of results")

        view = TestView(
            users
        )  # Pass username to this for the label. u[2] is username. It also needs Member to give to the info code (found_user)

        await interaction.followup.send(embed=embed, view=view)

    @app_commands.checks.has_role(GAME_MOD_ROLE_ID)
    @app_commands.command()
    async def getuser(
        self, interaction: discord.Interaction, game_username: str
    ) -> None:
        """
        Return the Discord ID and or Discord Object
        associated with a game username (2HOL username)
        """
        await interaction.response.defer()

        # Safe characters only
        game_username = re.sub(("[^a-zA-Z0-9 -]"), "", game_username)

        with db_conn() as db:
            db.execute(
                f"SELECT ticketServer_tickets.discord_id FROM ticketServer_tickets WHERE email = '{game_username}'"
            )
            result = db.fetchone()

        if not result:
            embed = discord.Embed(
                title=f"No result for the Game Username '{game_username}'",
                colour=0xFFBB35,
            )
            return await interaction.followup.send(embed=embed)

        id = int(result[0])
        user = await self.dictator.fetch_user(id)

        embed = discord.Embed(
            title=f"Result for the Game Username '{game_username}'", colour=0xFFBB35
        )

        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)
        embed.add_field(name="User mention:", value=f"{user.mention}", inline=True)
        embed.add_field(name="User name:", value=f"{user.name}", inline=True)
        embed.add_field(name="User ID:", value=f"{user.id}", inline=True)

        await interaction.followup.send(embed=embed)

    def username_from_player_id(self, player_id: int) -> str:
        """Takes an int as a players life ID and returns the associated username."""
        with db_conn() as db:
            """
            A player life ID can be repeated between different servers.
            We have made use of a single server for four years and do not intend to change this in the short term, so are largely unaffected by this.
            To resolve this, we assume we're only interested in the most recent player who lived with this ID.
            This is achieved with 'ORDER BY death_time DESC LIMIT 1'
            """
            db.execute(
                f"SELECT lineageServer_users.email FROM lineageServer_lives INNER JOIN lineageServer_users ON lineageServer_lives.user_id = lineageServer_users.id WHERE player_id = {player_id} ORDER BY death_time DESC LIMIT 1"
            )
            username = db.fetchone()

        if not username:
            return
        else:
            # We really only want the first result of the tuple
            username = username[0]

        return username

    def is_int(self, string: str) -> bool:
        """Takes a string and returns a True if it only contains numbers, else False."""
        return bool(re.search("^[0-9]*$", string))

    def username_is_player_id(self, username: str) -> str:
        """Handles if entered username is instead a players life ID and returns the associated username else retuns the username passed in."""
        if not self.is_int(username):
            return username

        retrieved_username = self.username_from_player_id(username)

        # ID may not exist or be correct
        if retrieved_username == None:
            raise commands.UserInputError

        return retrieved_username

    def valid_username_format(self, username: str) -> bool:
        """
        Validates format of the entered username.

        A username has two sections and is made up of a users Discord name seperated by a hyphen, followed by their Discord discriminator at the time of account creation.
        - A username must be 3-45 valid characters which include a-z, A-Z and 0-9
        - If a users name at the time of account creation is outside the length requirement (after invalid characters are removed), the user may enter their own username.
        - A Discord discriminator must be four digits.

        Valid username formats:
        - 'Colin13-9391'
        - '12345-6789'
        - 'Abc-9275'

        Invalid username formats:
        - 'Colin13-939'
        - '12345-Abcd'
        - 'Ab-9275'
        """
        username = re.search("[a-zA-Z0-9]{3,45}-[0-9]{4}", username)

        if username == None:
            return False

        return True


async def setup(dictator: commands.Bot) -> None:
    await dictator.add_cog(Admin(dictator))
