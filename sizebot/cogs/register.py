import asyncio

from discord.ext import commands
from discord.utils import get

from sizebot import digilogger as logger
from sizebot.conf import conf
from sizebot import userdb
from sizebot import digiSV
from sizebot import digisize


async def addUserRole(member):
    sizebotuserroleid = conf.getId("sizebotuserrole")
    role = get(member.guild.roles, id = sizebotuserroleid)
    if role is None:
        logger.warn(f"Sizebot user role {sizebotuserroleid} not found in guild {member.guild.id}")
        return
    await member.add_roles(role, reason = "Registered as sizebot user")


async def removeUserRole(member):
    sizebotuserroleid = conf.getId("sizebotuserrole")
    role = get(member.guild.roles, id = sizebotuserroleid)
    if role is None:
        logger.warn(f"Sizebot user role {sizebotuserroleid} not found in guild {member.guild.id}")
        return
    await member.remove_roles(role, reason = "Unregistered as sizebot user")


class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Registers a user for SizeBot
    @commands.command()
    async def register(self, ctx, nick: str, display: str = "y", currentheight: str = "5ft10in", baseheight: str = "5ft10in", baseweight: str = "180lb", unitsystem: str = "m", species: str = None):
        readable = f"CH {currentheight}, BH {baseheight}, BW {baseweight}"
        logger.warn(f"New user attempt! Nickname: {nick}, Display: {display}")
        logger.info(readable)

        currentheightSV = digiSV.toSV(currentheight)
        baseheightSV = digiSV.toSV(baseheight)
        baseweightWV = digiSV.toWV(baseweight)

        # Already registered
        if userdb.exists(ctx.message.author.id):
            await ctx.send("Sorry! You already registered with SizeBot.\n"
                           "To unregister, use the `&unregister` command.",
                           delete_after = 10)
            logger.warn(f"User already registered on user registration: {ctx.message.author}.")
            return

        # Invalid size value
        if (currentheightSV <= 0 or baseheightSV <= 0 or baseweightWV <= 0):
            logger.warn("Invalid size value.")
            await ctx.send("All values must be an integer greater than zero.", delete_after = 5)
            return

        # Invalid display value
        if display.lower() not in ["y", "n"]:
            logger.warn(f"display was {display}, must be Y or N.")
            return

        # Invalid unit value
        if unitsystem.lower() not in ["m", "u"]:
            logger.warn(f"unitsystem was {unitsystem}, must be M or U.")
            await ctx.send("Unitsystem must be `M` or `U`.", delete_after = 5)
            return

        userdata = userdb.User()
        userdata.id = ctx.message.author.id
        userdata.nickname = nick
        userdata.display = display == "y"
        userdata.height = currentheightSV
        userdata.baseheight = baseheightSV
        userdata.baseweight = baseweightWV
        userdata.unitsystem = unitsystem
        userdata.species = species

        userdb.save(userdata)

        await addUserRole(ctx.message.author)

        logger.warn(f"Made a new user: {ctx.message.author}!")
        logger.info(userdata)
        await ctx.send(f"Registered <@{ctx.message.author.id}>. {readable}.", delete_after = 5)

        # user has display == "y" and is server owner
        if userdata.display and userdata.id == ctx.message.author.guild.owner.id:
            await ctx.send("I can't update a server owner's nick. You'll have to manage it manually.", delete_after = 5)
            return

    @register.error
    async def register_handler(self, ctx, error):
        # Check if required argument is missing
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Not enough variables for `register`.\n"
                           "Use `&register [nick] [display (Y/N)] [currentheight] [baseheight] [baseweight] [M/U]`.",
                           delete_after = 30)
            return
        raise error

    @commands.command()
    async def unregister(self, ctx):
        user = ctx.message.author
        # User is not registered
        if not userdb.exists(user.id):
            logger.warn(f"User {user.id} not registered with SizeBot, but tried to unregister anyway.")
            await ctx.send("Sorry! You aren't registered with SizeBot.\n"
                           "To register, use the `&register` command.",
                           delete_after = 5)
            return

        # Send a confirmation request
        unregisterEmoji = "❌"
        sentMsg = await ctx.send(f"To unregister, react with {unregisterEmoji}.")
        await sentMsg.add_reaction(unregisterEmoji)

        # Wait for requesting user to react to sent message with unregisterEmoji
        def check(reaction, reacter):
            return reaction.message.id == sentMsg.id \
                and reacter.id == user.id \
                and str(reaction.emoji) == unregisterEmoji

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            # User took too long to respond
            return
        finally:
            # User took too long OR User clicked the emoji
            await sentMsg.delete()

        # remove the sizetag, delete the user file, and remove the user role
        digisize.nickReset(user)
        userdb.delete(user.id)
        await removeUserRole(user)

        logger.warn(f"User {user.id} successfully unregistered.")
        await ctx.send(f"Unregistered {user.name}.", delete_after = 5)

    @commands.Cog.listener()
    async def on_message(self, m):
        await digisize.nickUpdate(m.author)


# Necessary
def setup(bot):
    bot.add_cog(RegisterCog(bot))
