import time
from humanize import precisedelta
import random
import os
import json
import shutil
from dotenv import load_dotenv

import discord
from discord.ext import commands
bot = commands.Bot(command_prefix=',', intents=discord.Intents.all(), help_command=None)

@bot.event
async def on_ready():
    print('hiii :3')

# game setup
COUNTDOWN = 20
DECK = 'league'
THEME = 'League of Legends'
COOLDOWN = 600
CARDS = 10

shutil.copyfile(f'./decks/{DECK}.txt', './decks/deck.txt')

with open('./data/scoreboard.json', 'w') as f:
    f.write('{}')

# bot functions
played_cards = []

class Card: 
    def __init__(self, prompt: str, message):
        self.prompt = prompt
        self.message = message
        self.countdown = COUNTDOWN

    def tick(self): 
        self.countdown = max(0, self.countdown - 1)
        print(f'Ticked {self.message.author.name}\'s \'{self.prompt.strip()}\' to {self.countdown}')


def user_file(userid):
    return f'./userdata/{userid}.txt'


def deck_file(deck):
    return f'./decks/{deck}.txt'


async def give_cards(user, count):
    with open(deck_file('deck'), 'r') as f:
        cards = f.readlines()

    drawn = ''
    for _ in range(count):
        if not cards:
            shutil.copyfile(f'./decks/{DECK}.txt', './decks/deck.txt')

            with open(deck_file('deck'), 'r') as f:
                cards = f.readlines()

        drawn += cards.pop(random.randint(0, len(cards) - 1))

    with open(deck_file('deck'), 'w') as f:
        f.writelines(cards)

    with open(user_file(user.id), 'a') as f:
        f.write(drawn)

    if not drawn:
        return
    
    await user.send(embed=discord.Embed(title=f'You drew {'a card' if count == 1 else f'{count} cards'}', description=drawn))


def give_points(user, amount):
    with open('./data/scoreboard.json', 'r') as f:
        scoreboard = json.load(f)

    scoreboard[str(user.id)] += amount

    with open('./data/scoreboard.json', 'w') as f:
        json.dump(scoreboard, f, indent=4)


def reset_cooldown(user):
    with open('./data/cooldowns.json', 'r') as f:
        cooldowns = json.load(f)

    cooldowns[str(user.id)] = int(time.time())

    with open('./data/cooldowns.json', 'w') as f:
        json.dump(cooldowns, f, indent=4)


def get_cooldown(user):
    with open('./data/cooldowns.json', 'r') as f:
        cooldowns = json.load(f)

    return cooldowns[str(user.id)]


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    await bot.process_commands(message)

    if message.channel.id == 1337502693903831061:
        userid = message.author.id

        if str(userid) + '.txt' in os.listdir('./userdata'):
            # tick played cards
            for card in played_cards:
                if card.message.author.id != userid:
                    card.tick()

                if card.countdown == 0:
                    await card.message.reply(f'{card.message.author.name} has slipped in \'{card.prompt.strip()}\'!')
                    give_points(card.message.author, 5)
                    played_cards.remove(card)

            # play cards
            with open(user_file(userid), 'r') as f:
                cards = f.readlines()

            for card in cards:
                if card == '':
                    continue

                if card.strip().lower() in message.content.lower():
                    cooldown = COOLDOWN - (int(time.time()) - get_cooldown(message.author))

                    if cooldown <= 0:
                        played_cards.append(Card(card, message))
                        cards.remove(card)

                        with open(user_file(userid), 'w') as f:
                            f.writelines(cards)

                        await message.author.send(embed=discord.Embed(title='You played a card:', description=card))
                        await give_cards(message.author, 1)
                        reset_cooldown(message.author)

                        print(f'{message.author.name} played {card}')

                    else:
                        await message.author.send(f'You may play another card in {precisedelta(cooldown)}')

                    break


@bot.event
async def on_message_delete(message):
    for card in played_cards:
        if message.id == card.message.id:
            played_cards.remove(card)
            await message.author.send('A card you played seems to have been deleted...')
            return


@bot.event
async def on_message_edit(before, after):
    for card in played_cards:
        if before.id == card.message.id and card.prompt.strip().lower() not in after.content.strip().lower():
            played_cards.remove(card)
            await before.author.send('A card you played was edited out of existence...')
            return
        

# bot commands
@bot.command(name='join')
async def join(ctx):
    if str(ctx.author.id) + '.txt' in os.listdir('./userdata'):
        await ctx.reply(':rage:')
        return

    with open('./data/scoreboard.json', 'r') as f:
        scoreboard = json.load(f)

    with open('./data/cooldowns.json', 'r') as f:
        cooldowns = json.load(f)

    with open('./data/wins.json', 'r') as f:
        wins = json.load(f)

    scoreboard[ctx.author.id] = 0
    cooldowns[ctx.author.id] = 0
    wins[ctx.author.id] = 0 if ctx.author.id not in wins else wins[ctx.author.id]

    with open('./data/scoreboard.json', 'w') as f:
        json.dump(scoreboard, f, indent=4)

    with open('./data/cooldowns.json', 'w') as f:
        json.dump(cooldowns, f, indent=4)

    with open('./data/wins.json', 'w') as f:
        json.dump(wins, f, indent=4)

    await give_cards(ctx.author, CARDS)

    await ctx.reply(f'{ctx.author.name} joined!')
    print(f'{ctx.author.name} joined')


@bot.command(name='leave', aliases=['quit', 'unjoin', 'exit', 'resign', 'withdraw', 'dropout', 'optout', 'retire'])
async def leave(ctx):
    await ctx.reply('no')


@bot.command(name='report', aliases=['r', 're', 'rep'])
async def report(ctx):
    if str(ctx.author.id) + '.txt' not in os.listdir('./userdata'):
        return

    if ctx.message.reference:
        for card in played_cards:
            if card.message.id == ctx.message.reference.message_id:
                if card.message.author == ctx.message.author:
                    await ctx.reply('hehefunnyxd')
                    return
                
                await card.message.reply(f'{card.message.author.name} has been caught trying to slip in \'{card.prompt.strip()}\'! (-1)')
                give_points(ctx.author, 2)  
                give_points(card.message.author, -1)
                played_cards.remove(card)
                return

        await ctx.reply(f'{ctx.author.name} is schizo! (-1)')
        give_points(ctx.author, -1)

    else:
        await ctx.reply('nice report retard')


'''@bot.command(name='wordsalad', aliases=['spam', 'cringe'])
async def word_salad(ctx, defendant: discord.User=None):
    if ctx.message.reference:
        defendant = ctx.message.reference.author

    if defendant is None:
        with open(deck_file('deck'), 'r') as f:
            cards = f.readlines()
            salad = ' '.join([random.choice(cards) for _ in range(10)])
            await ctx.reply(salad)
            return
        
    elif defendant.id  + '.txt' not in os.listdir('./userdata'):
        await ctx.reply('The accused is not participating in the game.')
        return
        
    prosecutor = ctx.author

    if prosecutor.id == defendant.id:
        await ctx.reply('stfu')
        return
    
    case = await ctx.reply()'''


@bot.command(name='cards', aliases=['viewcards'])
async def cards(ctx):
    if str(ctx.author.id) + '.txt' not in os.listdir('./userdata'):
        return
    
    with open(user_file(ctx.author.id), 'r') as f:
        cards = f.read()

    await ctx.author.send(embed=discord.Embed(title='Your Cards', description=cards))
    await ctx.reply('Sent you your cards')


@bot.command(name='deck', aliases=['viewdeck'])
async def deck(ctx):
    try:
        await ctx.author.send(file=discord.File(deck_file(DECK)))
        await ctx.send('Sent you the current deck')

    except discord.Forbidden:
        await ctx.send('Unable to DM you.')


@bot.command(name='leaderboard', aliases=['lb', 'scoreboard'])
async def leaderboard(ctx):
    if ctx.channel.id == 1337502693903831061:
        await ctx.reply('Please use this command in https://discord.com/channels/1025958887209316422/1313998443827691551 to avoid clutter.')
        return
    
    with open('./data/scoreboard.json', 'r') as f:
        scoreboard = json.load(f)

    sorted_scores = sorted(scoreboard.items(), key=lambda x: x[1], reverse=True)

    description = ''
    for i, (user_id, score) in enumerate(sorted_scores, 1):
        user = await bot.fetch_user(int(user_id))
        description += f'**{i}. {user.name}**{score}\n\n'

    embed = discord.Embed(
        title='LEADERBOARD',
        description=description
    )

    await ctx.send(embed=embed)


@bot.command(name='wins')
async def wins(ctx):
    if ctx.channel.id == 1337502693903831061:
        await ctx.reply('Please use this command in https://discord.com/channels/1025958887209316422/1313998443827691551 to avoid clutter.')
        return
    
    with open('./data/wins.json', 'r') as f:
        wins = json.load(f)

    sorted_scores = sorted(wins.items(), key=lambda x: x[1], reverse=True)

    description = ''
    for i, (user_id, score) in enumerate(sorted_scores, 1):
        user = await bot.fetch_user(int(user_id))
        description += f'**{i}. {user.name}**{score}\n\n'

    embed = discord.Embed(
        title='ALL TIME WINS',
        description=description
    )

    await ctx.send(embed=embed)


@bot.command(name='cooldown', aliases=['cd'])
async def cooldown(ctx):
    if str(ctx.author.id) + '.txt' not in os.listdir('./userdata'):
        return
    
    cooldown = COOLDOWN - (int(time.time()) - get_cooldown(ctx.author))

    if cooldown <= 0:
        await ctx.author.send(f'You are ready to play a card!')

    else:
        await ctx.author.send(f'You may play another card in {precisedelta(cooldown)}')


@bot.command(name='cycle', aliases=['swap', 'reroll', 'rotate', 'draw'])
async def cycle(ctx):
    if str(ctx.author.id) + '.txt' not in os.listdir('./userdata'):
        return

    cooldown = COOLDOWN - (int(time.time()) - get_cooldown(ctx.author))

    if cooldown <= 0:
        reset_cooldown(ctx.author)
        if str(ctx.author.id) + '.txt' not in os.listdir('./userdata'):
            return

        with open(user_file(ctx.author.id), 'r') as f:
            cards = f.readlines()

        to_remove = random.sample(cards, CARDS // 2)
        for card in to_remove:
            cards.remove(card)

        with open(user_file(ctx.author.id), 'w') as f:
            f.writelines(cards)

        await give_cards(ctx.author, CARDS // 2)
        await ctx.author.send(f'Because you cycled cards, you have been placed on cooldown for {precisedelta(COOLDOWN)}')

    else:
        await ctx.author.send(f'You may cycle more cards in {precisedelta(cooldown)}')


@bot.command(name='help', aliases=['rules', 'commands'])
async def help(ctx):
    if ctx.channel.id == 1337502693903831061:
        await ctx.reply('Please use this command in https://discord.com/channels/1025958887209316422/1313998443827691551 to avoid clutter.')
        return
    
    await ctx.reply(embed=discord.Embed(title='DA RULES', 
                                        description=f'Each player holds {CARDS} cards at a time each with a different prompt and the primary objective of the game is to use these prompts in conversation without getting caught (only works in https://discord.com/channels/1025958887209316422/1337502693903831061).\n\nIf you attempt to slip in a prompt and are not caught for 20 messages, then you will be granted +5 points. However, if you are caught before then, then you will lose -1 point.\n\nIf you suspect someone is trying to slip in one of their prompts, you may report them in order to gain +2 points. If you are wrong, however then you will lose -1 point.\n\nTo avoid spam, you may only slip in a card every {precisedelta(COOLDOWN)}. Additionally using multiple prompts in one message will only count one.\n\nAfter a period of time, a new deck with a different theme will be rotated in; at this time, whoever has the most points will win the game and a new game will be started. Good luck!\n\n**Points**\nSlipping in a card: +5\nGetting caught: -1\nCatching someone: +2\nFalse reporting: -1\n\n**Commands**\n`,join` - Join the game\n`,report` - Reply to a message with this command to report it\n`,cards` - View your cards\n`,deck` - Be sent a copy of the deck in play\n`,cooldown` - Check your remaining cooldown\n`,swap` - Swap out half of your cards for new ones\n`,leaderboard` - View the current points leaderboard\n`,wins` - View the all time wins leaderboard\n\n*Reminder that commands work in bot DMs*\n\nCurrent Theme:\n**{THEME}**'))


# admin commands
def dooe():
    def predicate(ctx):
        return ctx.author.id == 326435590666977280
    return commands.check(predicate)


@bot.command(name='reset', aliases=['newgame', 'resetgame'])
@dooe()
async def reset(ctx):
    global played_cards
    played_cards = []
    
    with open('./data/scoreboard.json', 'r') as f:
        scores = json.load(f)
    
    if scores:
        max_score = max(scores.values())
        top_players = [uid for uid, score in scores.items() if score == max_score]

        with open('./data/wins.json', 'r') as f:
            wins = json.load(f)

        for uid in top_players:
            wins[uid] = wins.get(uid, 0) + 1

        with open('./data/wins.json', 'w') as f:
            json.dump(wins, f, indent=4)

    with open('./data/scoreboard.json', 'w') as f:
        f.write('{}')

    for file in os.listdir('./userdata'):
        os.remove(f'./userdata/{file}')

    shutil.copyfile(f'./decks/{DECK}.txt', './decks/deck.txt')

    with open('./data/scoreboard.json', 'w') as f:
        f.write('{}')

    await ctx.send(f'Game has been reset!')


@bot.command(name='adddeck')
@dooe()
async def add_deck(ctx):
    if not ctx.message.attachments:
        await ctx.send('No attachments found.')
        return

    os.makedirs('decks', exist_ok=True)

    for attachment in ctx.message.attachments:
        if attachment.filename.endswith('.txt'):
            data = await attachment.read()
            path = os.path.join('decks', attachment.filename)

            with open(path, 'wb') as f:
                f.write(data)

            await ctx.send(f'Saved: {attachment.filename}')

        else:
            await ctx.send(f'Skipped non-txt file: {attachment.filename}')


@bot.command(name='changedeck')
@dooe()
async def change_deck(ctx, deck: str):
    if deck + '.txt' not in os.listdir('./decks'):
        await ctx.reply('No such deck')
        return

    global played_cards
    played_cards = []

    global DECK
    DECK = deck

    shutil.copyfile(f'./decks/{DECK}.txt', './decks/deck.txt')

    await ctx.reply(f'Changed the deck to {DECK}, remember to also reset the game')


@bot.command(name='changetheme')
@dooe()
async def change_theme(ctx, *, theme: str):
    global THEME
    THEME = theme

    await ctx.reply(f'Changed the theme to {THEME}')


@bot.command(name='givepoints')
@dooe()
async def give_points(ctx, user: discord.User, amount: float):
    if str(user.id) + '.txt' in os.listdir('./userdata'):
        give_points(user, amount)


# run bot
load_dotenv()
TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)