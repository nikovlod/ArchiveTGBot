import csv
import os
import random
import string
from telegram import Update, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# CSV file path - using persistent disk on Render
CSV_FILE = "/opt/render/project/src/data/archiveTG_data.csv"

# Ensure data directory exists
os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)

# Initialize CSV file if it doesn't exist
def initialize_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['numerical_file_id', 'file_id', 'file_name', 'file_type'])
        logger.info("CSV file initialized")

# Load existing data into memory for faster lookups
def load_data():
    data_dict = {}
    try:
        with open(CSV_FILE, 'r') as csvfile:
            csvreader = csv.reader(csvfile)
            next(csvreader, None)  # Skip header
            
            for row in csvreader:
                if len(row) >= 4:
                    numerical_file_id, file_id, file_name, file_type = row
                    data_dict[numerical_file_id] = {
                        'file_id': file_id,
                        'file_name': file_name,
                        'file_type': file_type
                    }
        logger.info(f"Loaded {len(data_dict)} files from CSV")
    except FileNotFoundError:
        logger.info("CSV file not found, starting with empty data")
    
    return data_dict

# Global data dictionary
numerical_file_ids = load_data()

def search_csv(file_path, search_value):
    """Search for file by partial file_id match"""
    try:
        with open(file_path, "r") as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                if len(row) >= 4:
                    f_id = row[1]
                    if (search_value[:15] in f_id[:15] and 
                        search_value[44:68] in f_id[44:68]):
                        return row
    except FileNotFoundError:
        logger.error(f"CSV file not found: {file_path}")
    return False

def generate_numerical_file_id(length=16):
    """Generate random numerical file ID"""
    return ''.join(random.choices(string.digits, k=length))

def get_file_id(update: Update, context: CallbackContext) -> None:
    """Handle file uploads and store them"""
    file_id = None
    file_name = "Unknown file name"
    file_type = "Unknown file type"

    user_message = update.message

    if update.message.document:
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name or "Document"
        file_type = "Document"
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_name = "Photo"
        file_type = "Photo"
    elif update.message.video:
        file_id = update.message.video.file_id
        file_name = update.message.video.file_name or "Video"
        file_type = "Video"

    chat_id = update.message.chat_id
    
    if file_id:
        # Schedule message deletion after 60 seconds
        context.job_queue.run_once(
            lambda c: delete_message_safe(c.job.context), 
            60, 
            context=user_message
        )

        # Check if file already exists
        row = search_csv(CSV_FILE, file_id)
        if row:
            numerical_file_id = row[0]
            existing_file_name = row[2]
            response = f"*⚠️ File already exists*\n\n*File Name:* `{existing_file_name}`\n\n*Numerical File ID:* `{numerical_file_id}`"
            context.bot.send_message(
                chat_id=chat_id, 
                text=response, 
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # Generate new ID and store
            numerical_file_id = generate_numerical_file_id()
            
            # Add to memory
            numerical_file_ids[numerical_file_id] = {
                "file_id": file_id, 
                "file_name": file_name, 
                "file_type": file_type
            }

            # Store in CSV file
            try:
                with open(CSV_FILE, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([numerical_file_id, file_id, file_name, file_type])
                
                response = f"*Received {file_type}:*\n\n*File Name:* `{file_name}`\n\n*Numerical File ID:* `{numerical_file_id}`"
                context.bot.send_message(
                    chat_id=chat_id, 
                    text=response, 
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info(f"Stored file: {file_name} with ID: {numerical_file_id}")
                
            except Exception as e:
                logger.error(f"Error saving to CSV: {e}")
                context.bot.send_message(
                    chat_id=chat_id, 
                    text="Error saving file. Please try again."
                )
    else:
        context.bot.send_message(chat_id=chat_id, text="No valid file found.")

def send_file(update: Update, context: CallbackContext) -> None:
    """Handle /get command to retrieve files"""
    chat_id = update.message.chat_id
    
    try:
        # Get numerical file ID from command args or URL
        if context.args:
            numerical_file_id = context.args[0]
        else:
            numerical_file_id = update.message.text.split('/')[-1]
        
        numerical_file_id = str(numerical_file_id)

        # Retrieve file data
        file_data = numerical_file_ids.get(numerical_file_id)
        if file_data:
            file_id = file_data["file_id"]
            file_name = file_data["file_name"]
            file_type = file_data["file_type"]

            caption = f"Sent {file_type}: `{file_name}`\nNumerical File ID: `{numerical_file_id}`\n\n*File will be deleted after 1.5 hours. Forward the file to saved messages to watch/download later.*"

            # Send file based on type
            if file_type == "Photo":
                sent_message = context.bot.send_photo(
                    chat_id=chat_id, 
                    photo=file_id, 
                    caption=caption, 
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                sent_message = context.bot.send_document(
                    chat_id=chat_id, 
                    document=file_id, 
                    caption=caption, 
                    parse_mode=ParseMode.MARKDOWN
                )

            # Schedule message deletion after 1.5 hours
            delay = 5400  # 1.5 hours in seconds
            context.job_queue.run_once(
                lambda c: delete_message_safe(c.job.context), 
                delay, 
                context=sent_message
            )

        else:
            context.bot.send_message(chat_id=chat_id, text="Invalid numerical file ID.")
            
    except (IndexError, ValueError) as e:
        logger.error(f"Error in send_file: {e}")
        context.bot.send_message(
            chat_id=chat_id, 
            text="Invalid command format. Use /get {numerical_file_id} to get a file."
        )

def start(update: Update, context: CallbackContext) -> None:
    """Handle /start command"""
    chat_id = update.message.chat_id
    
    try:
        # Check if there's a file ID in the start command
        if context.args:
            numerical_file_id = context.args[0]
        else:
            parts = update.message.text.split('/')
            numerical_file_id = parts[-1] if len(parts) > 1 else None
        
        if numerical_file_id and numerical_file_id != 'start':
            numerical_file_id = str(numerical_file_id)
            
            # Retrieve and send file
            file_data = numerical_file_ids.get(numerical_file_id)
            if file_data:
                file_id = file_data["file_id"]
                file_name = file_data["file_name"]
                file_type = file_data["file_type"]

                caption = f"*Sent {file_type}:* `{file_name}`\n\n*Numerical File ID:* `{numerical_file_id}`\n\n*File will be deleted after 1.5 hours. Forward the file to saved messages to watch/download later.*"

                if file_type == "Photo":
                    sent_message = context.bot.send_photo(
                        chat_id=chat_id, 
                        photo=file_id, 
                        caption=caption, 
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    sent_message = context.bot.send_document(
                        chat_id=chat_id, 
                        document=file_id, 
                        caption=caption, 
                        parse_mode=ParseMode.MARKDOWN
                    )

                # Schedule deletion
                delay = 5400
                context.job_queue.run_once(
                    lambda c: delete_message_safe(c.job.context), 
                    delay, 
                    context=sent_message
                )
            else:
                welcome_message()
        else:
            welcome_message()
            
    except (IndexError, ValueError) as e:
        logger.error(f"Error in start command: {e}")
        welcome_message()
    
    def welcome_message():
        context.bot.send_message(
            chat_id=chat_id, 
            text="Welcome to ArchiveAnyFileBot. Send me files to archive or use /get {ID} to get the archived files."
        )

def delete_message_safe(message):
    """Safely delete a message with error handling"""
    try:
        message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

def error_handler(update: Update, context: CallbackContext) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    """Main function to run the bot"""
    # Initialize CSV file
    initialize_csv()
    
    # Get bot token from environment variable
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set!")
        return
    
    # Create updater and dispatcher
    updater = Updater(bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Register handlers
    dispatcher.add_handler(MessageHandler(Filters.document, get_file_id))
    dispatcher.add_handler(MessageHandler(Filters.photo, get_file_id))
    dispatcher.add_handler(MessageHandler(Filters.video, get_file_id))
    dispatcher.add_handler(CommandHandler("get", send_file))
    dispatcher.add_handler(CommandHandler("start", start))
    
    # Error handler
    dispatcher.add_error_handler(error_handler)

    # Start the bot
    logger.info("Bot starting...")
    
    # Use webhooks if on Render (production), polling for local development
    if os.getenv('RENDER'):
        # Webhook mode for production
        port = int(os.getenv('PORT', 5000))
        app_name = os.getenv('RENDER_EXTERNAL_URL', '').replace('https://', '')
        
        updater.start_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=bot_token,
            webhook_url=f"https://{app_name}/{bot_token}"
        )
        logger.info(f"Bot started with webhook on port {port}")
    else:
        # Polling mode for development
        updater.start_polling()
        logger.info("Bot started with polling")
    
    updater.idle()

if __name__ == "__main__":
    main()
