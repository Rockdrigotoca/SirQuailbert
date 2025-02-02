import discord
from discord.ext import commands, tasks
import random
from collections import defaultdict
import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment variables (for local testing)
load_dotenv()

# Fetch bot token from environment variables (GitHub Secrets or .env file)
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Set up the bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Define a whimsical NPC name and introduction
NPC_NAME = "Sir Quailbert the Wanderer"
INTRO_MESSAGE = (
    "Greetings, travelers! I am Sir Quailbert the Wanderer, a humble quail of lore and legend. "
    "Step forth, and mayhap you shall receive wisdom, trivia, or even a Shrubbery Cent!"
)

# Leaderboard and tracking activity
leaderboard = defaultdict(int)
recent_active_users = set()

# Load JSON files
TRIVIA_FILE = "trivia.json"
RESPONSES_FILE = "response.json"
QUESTIONS_FILE = "questions.json"

def load_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_json(data, file_path):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

trivia_questions = load_json(TRIVIA_FILE)
whimsical_responses = load_json(RESPONSES_FILE)
questions_and_answers = load_json(QUESTIONS_FILE)

# Command to introduce the NPC
@bot.command(name="introduce")
async def introduce(ctx):
    await ctx.send(INTRO_MESSAGE)

# Command to give trivia
@bot.command(name="trivia")
async def trivia(ctx):
    if not trivia_questions:
        await ctx.send("Sir Quailbert has run out of trivia questions! Please add more using the !addtrivia command.")
        return

    selected_question = random.choice(trivia_questions)
    await ctx.send(f"Trivia from Sir Quailbert: {selected_question['question']}")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        user_response = await bot.wait_for("message", check=check, timeout=90)
        if user_response.content.lower() == selected_question["answer"].lower():
            reward = random.randint(1, 5)
            leaderboard[ctx.author.id] += reward
            await ctx.send(
                f"All right Quail! You are correct, {ctx.author.display_name}! {selected_question['fun_fact']} "
                f"Sir Quailbert grants you {reward} Shrubbery Cent{'s' if reward > 1 else ''} as a reward!"
            )
        else:
            await ctx.send(
                f"Alas, that is incorrect. The correct answer was '{selected_question['answer']}'. "
                f"Better luck next time, brave traveler!"
            )
    except asyncio.TimeoutError:
        await ctx.send(
            "Time's up! Sir Quailbert grows weary of waiting. The correct answer was "
            f"'{selected_question['answer']}'."
        )

# Command to add new trivia
@bot.command(name="addtrivia")
async def add_trivia(ctx, question: str, answer: str, *, fun_fact: str):
    new_trivia = {"question": question, "answer": answer, "fun_fact": fun_fact}
    trivia_questions.append(new_trivia)
    save_json(trivia_questions, TRIVIA_FILE)
    await ctx.send(f"New trivia added: '{question}' with answer '{answer}'. Thank you, {ctx.author.display_name}!")

# Command to view the leaderboard
@bot.command(name="leaderboard")
async def show_leaderboard(ctx):
    if not leaderboard:
        await ctx.send("The leaderboard is empty. Earn Shrubbery Cents to take your place in the legendary leaderboard!")
        return

    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    leaderboard_message = "**Legendary Quail Laderboard**\n"
    for i, (user_id, points) in enumerate(sorted_leaderboard, start=1):
        user = await bot.fetch_user(user_id)
        leaderboard_message += f"{i}. {user.display_name} - {points} Shrubbery Cent{'s' if points > 1 else ''}\n"

    await ctx.send(leaderboard_message)

# Whimsical response to greetings
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    greetings = ["hello", "hi", "greetings", "hail", "hola", "bonjour", "salut", "ni hao", "hai", "namaste", "namaskar", "marhaban", "ahlan", "ola", "oi", "privet", "zdravstvuyte", "hallo", "ciao", "salve", "habari", "jambo", "merhaba", "selam", "hoi", "yia sas", "yia sou", "sawasdee", "xin chao", "chao", "kumusta", "shalom", "salam", "halo", "apa kabar", "cheers", "prost", "salud", "skol", "santé", "cin cin", "na zdravi", "kanpai", "kampai", "sláinte", "proost", "egészségedre", "chin chin", "za zdorovye", "skal", "kippis", "prozit", "a votre sante", "le chaim", "yamas", "good morning", "buenos días", "bonjour", "guten morgen", "buongiorno", "dobroye utro", "ohayou", "selamat pagi", "sabah el kheir", "dobré ráno", "boker tov", "suprabhat", "bom dia", "magandang umaga", "good night", "buenas noches", "bonne nuit", "gute nacht", "buona notte", "spokoynoy nochi", "oyasumi", "selamat malam", "layla tov", "shubh raatri", "boa noite", "Hallo zusammen", "magandang gabi"]
    if any(greet in message.content.lower() for greet in greetings):
        if whimsical_responses:
            response = random.choice(whimsical_responses)
            await message.channel.send(response.replace("{user}", message.author.display_name))
        else:
            await message.channel.send(
                f"Well met, {message.author.display_name}! Sir Quailbert tips his feather to you."
            )

    # Check if the message contains a question
    if "?" in message.content:
        keywords = message.content.lower().split()
        for qa in questions_and_answers:
            if any(keyword in qa["keywords"] for keyword in keywords):
                if isinstance(qa["answer"], list):  # Handle multiple sentences in the answer
                    for sentence in qa["answer"]:
                        await message.channel.send(sentence.replace("{user}", message.author.display_name))
                else:
                    await message.channel.send(qa["answer"].replace("{user}", message.author.display_name))
                break


    # Track active users
    recent_active_users.add(message.author.id)

    await bot.process_commands(message)

# Task to randomly award points to active users
@tasks.loop(hours=168)  # Roughly once a week
async def award_active_players():
    if recent_active_users:
        awarded_user_id = random.choice(list(recent_active_users))
        leaderboard[awarded_user_id] += 5
        user = await bot.fetch_user(awarded_user_id)
        recent_active_users.clear()

        channel = discord.utils.get(bot.get_all_channels(), name="quail-general-chat")  # Replace "general" with your channel name
        if channel:
            await channel.send(
                f"Hear ye, hear ye! Sir Quailbert has awarded {user.display_name} 5 Shrubbery Cent for their recent deeds in Quailwood, cannot thank you enough!"
            )

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    award_active_players.start()

# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
