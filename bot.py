import telebot
from telebot import types
from web3 import Web3
from db.database import init_db, add_wallet_to_db, remove_wallet_from_db, get_all_wallets
from config import TELEGRAM_API_TOKEN, INFURA_URL

# Initialize the bot and Web3 connection
bot = telebot.TeleBot(TELEGRAM_API_TOKEN)
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Initialize database
init_db()
print("Database initialized successfully.")

# To store user states for wallet input
user_states = {}

# Helper function to create a keyboard with available commands
def generate_main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('/addwallet')
    btn2 = types.KeyboardButton('/removewallet')
    btn3 = types.KeyboardButton('/balance')
    btn4 = types.KeyboardButton('/help')
    markup.add(btn1, btn2, btn3, btn4)
    return markup

# Welcome /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
    *Hello! Welcome to the Ozone Balance Checker Bot* 🌐💰
    Manage and check the balance of your Ozone wallets seamlessly.
    
    Use the menu below to get started, or type a command:
    /addwallet - Add a new wallet address
    /removewallet - Remove an existing wallet
    /balance - Get the total balance of all added wallets
    /help - Show help information
    """
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=generate_main_menu())

# Help command
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
    *Here are the commands you can use*:
    /start - Start the bot and show the menu
    /addwallet - Add a wallet to track
    /removewallet - Remove a wallet from the tracker
    /balance - Display the total balance of all tracked wallets
    /help - Show this help message
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown', reply_markup=generate_main_menu())
# Add wallet command - prompts for wallet address
@bot.message_handler(commands=['addwallet'])
def add_wallet_prompt(message):
    bot.reply_to(message, "Please enter the Ethereum wallet address you want to add:")
    user_states[message.chat.id] = 'awaiting_wallet_address'  # Set user state to await wallet input

# Handle wallet address input
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_wallet_address')
def handle_wallet_input(message):
    wallet_address = message.text.strip()
    
    if wallet_address in get_all_wallets():
        bot.reply_to(message, "❌ Wallet address already exists. Please try adding a different address.")
        # Reset user state
        user_states[message.chat.id] = None
        return
    if Web3.is_address(wallet_address):
        wallet_address = Web3.to_checksum_address(wallet_address);
        add_wallet_to_db(wallet_address)  # Store wallet in the database
        bot.reply_to(message, f"✅ *Wallet {wallet_address} added successfully!*", parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ Invalid Ethereum wallet address. Please try again.")
    
    # Reset user state
    user_states[message.chat.id] = None

# Remove wallet command
@bot.message_handler(commands=['removewallet'])
def remove_wallet_prompt(message):
    bot.reply_to(message, "Please enter the Ethereum wallet address you want to remove:")
    user_states[message.chat.id] = 'awaiting_wallet_removal'

# Handle wallet removal input
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_wallet_removal')
def handle_wallet_removal(message):
    wallet_address = message.text.strip()
    remove_wallet_from_db(wallet_address)  # Remove wallet from database
    bot.reply_to(message, f"✅ *Wallet {wallet_address} removed successfully!*", parse_mode='Markdown')

    # Reset user state
    user_states[message.chat.id] = None

# Display total balance of all wallets with formatting
@bot.message_handler(commands=['balance'])
def total_balance(message):
    wallets = get_all_wallets()  # Get all wallets from the database
    total_balance = 0
    if wallets:
        response_message = "💰 *Wallet Balances*:\n"
        for wallet in wallets:
            balance = web3.eth.get_balance(wallet)
            ether_balance = Web3.from_wei(balance,'ether')
            total_balance += ether_balance
            response_message += f"• `{wallet}`: {ether_balance} OZO\n"
        
        response_message += f"\n🔢 *Total balance of all wallets*: `{total_balance}` ETH"
        bot.send_message(message.chat.id, response_message, parse_mode='Markdown')
    else:
        bot.reply_to(message, "⚠️ No wallets found. Add wallets using /addwallet `<wallet_address>`.")

if __name__ == '__main__':
    bot.polling()
