# TODO: Implementation
# IDEA: Track which invite a user joined off of

import discord
import json
import os
from datetime import datetime
from discord.ext import commands


def module_perms(ctx):
	return ctx.message.author.guild_permissions.administrator


def parse_id(arg):
	"""
	Parses an ID from a discord mention
	:param arg: mention or ID passed
	:return: ID
	"""
	if "<" in arg:
		for i, c in enumerate(arg):
			if c.isdigit():
				return int(arg[i:-1])
	# Using ID
	else:
		return int(arg)


class Logging(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.embed = discord.Embed()
		self.logs = None

	async def update_guilds(self):
		savedGuilds = []
		for guildID in self.logs:
			savedGuilds.append(guildID)

		guilds = []
		for guild in self.bot.guilds:
			guilds.append(str(guild.id))

		addGuilds = [x for x in guilds if x not in savedGuilds]
		removeGuilds = [x for x in savedGuilds if x not in guilds]

		# Add new guilds
		for guildID in addGuilds:
			self.logs[str(guildID)] = {"channel": None}

		# Remove disconnected guilds
		for guildID in removeGuilds:
			self.logs.pop(str(guildID))

		await self.update_state()

	@commands.Cog.listener()
	async def on_ready(self):
		await self.load_state()
		await self.update_guilds()

	@commands.command(pass_context=True, name="logging")
	@commands.check(module_perms)
	async def change_logging(self, ctx, arg1):
		"""
		Changes the channel that the bot sends logging messages in
		:param arg1: channel ID or mention
		"""
		channel = ctx.guild.get_channel(parse_id(arg1))
		print(parse_id(arg1))

		if self.logs[str(ctx.message.guild.id)]["channel"] != channel.id:
			self.logs[str(ctx.message.guild.id)]["channel"] = channel.id

			print("Updating guild " + str(ctx.message.guild.id) + " to use logging channel " + str(channel.id))

			await self.update_state()
			print("Finished updating logging channel")
			await ctx.send("Successfully updated logging channel to <#" + str(channel.id) + ">")

	@change_logging.error
	async def change_logging_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			print("!ERROR! " + str(ctx.author.id) + " did not have permissions for change logging command")
		elif isinstance(error, commands.MissingRequiredArgument):
			await ctx.send("Command is missing arguments")
		else:
			print(error)

	async def load_state(self):
		with open(os.path.join("config", "logging.json"), "r+") as loggingFile:
			logs = loggingFile.read()
			self.logs = json.loads(logs)

	async def update_state(self):
		with open(os.path.join("config", "logging.json"), "r+") as loggingFile:
			loggingFile.truncate(0)
			loggingFile.seek(0)
			json.dump(self.logs, loggingFile, indent=4)

	@commands.Cog.listener()
	async def on_message_delete(self, message):
		"""
		Sends a logging message containing
		author, channel, content, and time of the deleted message
		:param message: message object deleted
		"""
		if not message.author.bot:
			if self.logs[str(message.guild.id)]["channel"] is not None:
				loggingChannel = message.guild.get_channel(int(self.logs[str(message.guild.id)]["channel"]))
				channel = message.channel

				self.embed = discord.Embed()
				self.embed.colour = discord.Colour(0xbe4041)
				self.embed.set_author(name=message.author.name + "#" + message.author.discriminator, icon_url=message.author.avatar_url)
				self.embed.title = "Message deleted in " + "#" + channel.name
				self.embed.description = message.content
				self.embed.set_footer(text="ID: " + str(message.author.id))
				self.embed.timestamp = datetime.utcnow()

				await loggingChannel.send(embed=self.embed)

	@commands.Cog.listener()
	async def on_raw_message_delete(self, payload):
		"""
		Sends a logging message containing
		location (channel), and ID of the message deleted
		:param payload:
		:return:
		"""
		guild = self.bot.get_guild(payload.guild_id)

		if self.logs[str(guild.id)]["channel"] is not None and payload.cached_message is None:
			loggingChannel = guild.get_channel(int(self.logs[str(guild.id)]["channel"]))
			channel = guild.get_channel(payload.channel_id)

			self.embed = discord.Embed()
			self.embed.colour = discord.Colour(0xbe4041)
			self.embed.title = "Message deleted in " + "#" + channel.name
			self.embed.set_footer(text="Uncached message: " + str(payload.message_id))
			self.embed.timestamp = datetime.utcnow()

			await loggingChannel.send(embed=self.embed)

	@commands.Cog.listener()
	async def on_raw_bulk_message_delete(self, payload):
		"""
		Sends a logging message containing
		author, location (channel and placement), content, and time of the deleted messages
		May be limited if message is not in the cache
		:param payload:
		"""
		guild = self.bot.get_guild(payload.guild_id)

		if self.logs[str(guild.id)]["channel"] is not None:

			loggingChannel = guild.get_channel(int(self.logs[str(guild.id)]["channel"]))
			channel = guild.get_channel(payload.channel_id)
			content = ""
			count = 0

			for message in payload.cached_messages:
				count += 1
				content += "[" + message.author.name + "#" + message.author.discriminator + "]: " + message.content + "\n"

			self.embed = discord.Embed()
			self.embed.colour = discord.Colour(0xbe4041)
			self.embed.title = str(count) + " Messages bulk deleted in " + "#" + channel.name
			self.embed.description = content
			self.embed.timestamp = datetime.utcnow()

			await loggingChannel.send(embed=self.embed)

	@commands.Cog.listener()
	async def on_message_edit(self, before, after):
		"""
		Sends a logging message containing
		the content of the message before and after the edit
		:param before: message object before
		:param after: message object after
		"""
		if not before.author.bot:
			if self.logs[str(before.guild.id)]["channel"] is not None:

				if before.content is after.content:
					return

				loggingChannel = before.guild.get_channel(int(self.logs[str(before.guild.id)]["channel"]))
				channel = before.channel

				self.embed = discord.Embed(url=before.jump_url)
				self.embed.colour = discord.Colour(0x8899d4)
				self.embed.set_author(name=before.author.name + "#" + before.author.discriminator, icon_url=before.author.avatar_url)
				self.embed.title = "Message edited in #" + channel.name
				self.embed.description = "**Before:** " + before.content + "\n**+After:** " + after.content
				self.embed.set_footer(text="ID: " + str(before.author.id))
				self.embed.timestamp = datetime.utcnow()

				await loggingChannel.send(embed=self.embed)

	@commands.Cog.listener()
	async def on_raw_message_edit(self, payload):
		"""
		Sends a logging message containing
		the content of the message after the edit
		:param payload:
		:return:
		"""

	# FIXME: Cannot get guild from payload
	# guild = self.bot.get_guild(payload.guild_id)
	#
	# if self.logs[str(guild.id)]["channel"] is not None and payload.cached_message is None:
	# 	loggingChannel = guild.get_channel(int(self.logs[str(guild.id)]["channel"]))
	# 	channel = guild.get_channel(payload.channel_id)
	# 	message = channel.fetch_message(payload.message_id)
	#
	# 	self.embed = discord.Embed()
	# 	self.embed.colour = discord.Colour(0x8899d4)
	# 	self.embed.set_author(name=message.author.name + "#" + message.author.discriminator, icon_url=message.author.avatar_url)
	# 	self.embed.title = "Message edited in " + "#" + channel.name
	# 	self.embed.description = "\n**+After:** " + message.content
	# 	self.embed.set_footer(text="ID: " + str(message.author.id))
	# 	self.embed.timestamp = datetime.utcnow()
	#
	# 	await loggingChannel.send(embed=self.embed)

	@commands.Cog.listener()
	async def on_guild_channel_create(self, channel):
		"""
		Sends a logging message containing
		the name, category, and permissions of the channel
		:param channel:
		"""
		if self.logs[str(channel.guild.id)]["channel"] is not None:
			loggingChannel = channel.guild.get_channel(int(self.logs[str(channel.guild.id)]["channel"]))
			self.embed = discord.Embed()
			self.embed.colour = discord.Colour(0x43b581)
			permissions = ""

			# If a Category
			if channel.type is discord.ChannelType.category:
				self.embed.title = "Category created"
				description = "**Name:** " + channel.name + "\n**Position:** " + str(channel.position)

				if len(channel.overwrites) > 0:
					for role in channel.overwrites:

						# If you have permission to read messages
						if channel.overwrites[role].pair()[0].read_messages is True:
							permissions += "**Read Text Channels & See Voice Channels:** :white_check_mark:\n"
							permissions += "**Connect:** :white_check_mark:"
						else:
							permissions += "**Read Text Channels & See Voice Channels:** :x:\n"
							permissions += "**Connect:** :x:"

			else:
				description = "**Name:** " + channel.name + "\n**Position:** " + str(
					channel.position) + "\n**Category:** "
				if channel.category is not None:
					description += channel.category.name
				else:
					description += "None"

				# If a text channel
				if channel.type is discord.ChannelType.text:
					self.embed.title = "Text channel created"

					if len(channel.overwrites) > 0:
						for role in channel.overwrites:
							if channel.overwrites[role].pair()[0].read_messages is True:
								permissions += "**Read messages:** :white_check_mark:"
							else:
								permissions += "**Read messages:** :x:"

				# If a VoiceChannel
				else:
					self.embed.title = "Voice channel created"

					if len(channel.overwrites) > 0:
						for role in channel.overwrites:
							permissions = ""
							if channel.overwrites[role].pair()[0].connect is True:
								permissions += "**Connect:** :white_check_mark:"
							else:
								permissions += "**Connect:** :x:"

			self.embed.add_field(name="Overwrites for " + str(role.name), value=permissions, inline=False)
			self.embed.description = description
			self.embed.set_footer(text="ID: " + str(channel.id))
			self.embed.timestamp = datetime.utcnow()

			await loggingChannel.send(embed=self.embed)

	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel):
		"""
		Sends a logging message containing
		the name, category, and permissions of the channel
		"""
		if self.logs[str(channel.guild.id)]["channel"] is not None:
			loggingChannel = channel.guild.get_channel(int(self.logs[str(channel.guild.id)]["channel"]))
			self.embed = discord.Embed()
			self.embed.colour = discord.Colour(0xbe4041)

			if channel.type is discord.ChannelType.category:
				self.embed.title = "Category deleted"
				description = "**Name:** " + channel.name

			else:
				if channel.type is discord.ChannelType.text:
					self.embed.title = "Text channel deleted"
				else:
					self.embed.title = "Voice channel deleted"

				description = "**Name:** " + channel.name + "\n**Category:** "

				if channel.category is not None:
					description += channel.category.name
				else:
					description += "None"

			self.embed.description = description
			await loggingChannel.send(embed=self.embed)

	@commands.Cog.listener()
	async def on_guild_channel_update(self, before, after):
		"""
		Sends a logging message containing
		the updated properties of the channel
		"""
		# Check name update
		if before.name != after.name:
			if before.type is discord.ChannelType.category:
				self.embed.title
		# Check position update
		# Check permission update
		# Slow mode
		# NSFW

		return

	@commands.Cog.listener()
	async def on_guild_channel_pins_update(self, channel, last_pin):
		"""
		Sends a logging message containing
		the name of the channel, the content of the pinned message, and a link to the message
		"""
		return

	@commands.Cog.listener()
	async def on_guild_integrations_update(self, guild):
		"""
		WTF are guild integrations???
		"""
		return

	@commands.Cog.listener()
	async def on_webhooks_update(self, channel):
		"""
		WTF are webhooks???
		"""
		return

	@commands.Cog.listener()
	async def on_member_join(self, member):
		"""
		Sends a logging message containing
		the name, avatar, id, join position, account age
		"""
		if self.logs[str(member.guild.id)]["channel"] is not None:
			loggingChannel = member.guild.get_channel(int(self.logs[str(member.guild.id)]["channel"]))
			ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])

			self.embed = discord.Embed()
			self.embed.colour = discord.Colour(0x43b581)
			self.embed.set_author(name=member.name + "#" + member.discriminator, icon_url=member.avatar_url)
			self.embed.title = "Member joined"

			creationDelta = datetime.now() - member.created_at
			count = 0

			self.embed.description = "<@" + str(member.id) + "> " + ordinal(member.guild.member_count) + " to join\ncreated "
			self.embed.set_footer(text="ID: " + str(member.id))
			self.embed.timestamp = datetime.utcnow()

			await loggingChannel.send(embed=self.embed)

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		"""
		Sends a logging message containing
		the name, avatar, id, time spent on the server
		"""
		return

	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		"""
		Sends a logging message containing
		the property of the member updated before and after
		"""
		return

	@commands.Cog.listener()
	async def on_user_update(self, before, after):
		"""
		Sends a logging message containing
		the property of the user updated before and after
		"""
		return

	@commands.Cog.listener()
	async def on_guild_update(self, before, after):
		"""
		Sends a logging message containing
		the property of the guild updated before and after
		"""
		return

	@commands.Cog.listener()
	async def on_guild_role_create(self, role):
		"""
		Sends a logging message containing
		the id, name, color, mentionable, and hoisted properties of the role
		"""
		return

	@commands.Cog.listener()
	async def on_guild_role_delete(self, role):
		"""
		Sends a logging message containing
		the id, name, color, mentionable, and hoisted properties of the role
		"""
		return

	@commands.Cog.listener()
	async def on_guild_role_update(self, before, after):
		"""
		Sends a logging message containing
		the property of the role updated before and after
		"""
		return

	@commands.Cog.listener()
	async def on_guild_emojis_update(self, guild, before, after):
		"""
		Sends a logging message containing
		the id, name, and picture of the emoji
		"""
		return

	@commands.Cog.listener()
	async def on_voice_state_update(self, member, before, after):
		"""
		Sends a logging message containing
		the id, name, and updated voice properties of the member
		"""
		return

	@commands.Cog.listener()
	async def on_member_ban(self, guild, user):
		"""
		Sends a logging message containing
		the id, name, and join date of the member
		"""
		return

	@commands.Cog.listener()
	async def on_member_unban(self, guild, user):
		"""
		Sends a logging message containing
		the id and name of the member
		"""
		return

	@commands.Cog.listener()
	async def on_invite_create(self, invite):
		"""
		Sends a logging message containing
		the invite code, inviter name, inviter id, expiration time
		"""

		return

	@commands.Cog.listener()
	async def on_invite_delete(self, invite):
		"""
		Sends a logging message containing
		the invite code, inviter name, and expiration time
		"""
		return
