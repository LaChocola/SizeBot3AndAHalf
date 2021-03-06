import logging

import discord
from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot.lib.eval import runEval
from sizebot.lib import utils

logger = logging.getLogger("sizebot")


class EvalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(
        hidden = True
    )
    @commands.is_owner()
    async def eval(self, ctx, *, evalStr):
        """Evaluate a Python expression."""
        evalStr = utils.removeCodeBlock(evalStr)

        logger.info(f"{ctx.message.author.display_name} tried to eval {evalStr!r}.")

        # Show user that bot is busy doing something
        waitMsg = None
        if isinstance(ctx.channel, discord.TextChannel):
            waitMsg = await ctx.send(f"<a:loading:663876493771800603>")

        async with ctx.typing():
            try:
                result = await runEval(ctx, evalStr)
            except Exception as err:
                logger.error("eval error:\n" + utils.formatTraceback(err))
                await ctx.send(f"⚠️ ` {utils.formatError(err)} `")
                return
            finally:
                # Remove wait message when done
                if waitMsg:
                    await waitMsg.delete(delay=0)

        if isinstance(result, discord.Embed):
            await ctx.send(embed=result)
        else:
            strResult = str(result).replace("```", r"\`\`\`")
            for m in utils.chunkMsg(strResult):
                await ctx.send(m)

    @commandsplus.command(
        hidden = True
    )
    @commands.is_owner()
    async def evil(self, ctx, *, evalStr):
        """Evaluate a Python expression, but evilly."""
        await ctx.message.delete(delay = 0)

        evalStr = utils.removeCodeBlock(evalStr)

        logger.info(f"{ctx.message.author.display_name} tried to quietly eval {evalStr!r}.")

        async with ctx.typing():
            try:
                await runEval(ctx, evalStr, returnValue = False)
            except Exception as err:
                logger.error("eval error:\n" + utils.formatTraceback(err))
                await ctx.message.author.send(f"⚠️ ` {utils.formatError(err)} `")


def setup(bot):
    bot.add_cog(EvalCog(bot))
