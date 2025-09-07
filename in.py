import os
import logging
import json
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
)
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
import textwrap
import requests
from io import BytesIO
import re
from datetime import datetime
import random
import glob

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    MANGA_NAME, MANGA_PFP, SYNOPSIS, PERCENTAGE, YEAR, AUTHOR, 
    TEMPLATE_STYLE, COLOR_SCHEME, TEXT_STYLE, BRANDING, CONFIRMATION,
    CUSTOM_COLOR, CUSTOM_FONT
) = range(13)

# Available templates
TEMPLATES = {
    "Style 1": "default",
    "Style 2": "minimal",
    "Style 3": "elegant",
    "Style 4": "modern",
    "Style 5": "vintage",
    "Style 6": "neon"
}

# Available colors (add more as needed)
COLORS = {
    "Red": "#FF0000",
    "Blue": "#0000FF",
    "Green": "#00FF00",
    "Purple": "#800080",
    "Orange": "#FFA500",
    "Pink": "#FFC0CB",
    "Teal": "#008080",
    "Black": "#000000",
    "White": "#FFFFFF",
    "Gold": "#FFD700",
    "Silver": "#C0C0C0",
    "Random": "random",
    "Custom": "custom"
}

# Available fonts
FONTS = {
    "Standard": "arial.ttf",
    "Bold": "arialbd.ttf",
    "Italic": "ariali.ttf",
    "Japanese": "msmincho.ttf",
    "Modern": "modern.ttf",
    "Custom": "custom"
}

# Font sizes for different elements
FONT_SIZES = {
    "title": 40,
    "author": 20,
    "details": 18,
    "percentage": 36,
    "synopsis": 16,
    "branding": 20
}

# User session data (in production, use a database)
user_sessions = {}

def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask for the manga name."""
    user_id = update.message.from_user.id
    user_sessions[user_id] = {
        'step': MANGA_NAME,
        'data': {},
        'created_at': datetime.now()
    }
    
    update.message.reply_text(
        "🎌 Welcome to Manga Thumbnail Generator! 🎌\n\n"
        "I'll help you create professional manga thumbnails.\n"
        "Let's start with the manga name:"
    )
    return MANGA_NAME

def manga_name(update: Update, context: CallbackContext) -> int:
    """Store the manga name and ask for the manga profile picture."""
    user_id = update.message.from_user.id
    user_sessions[user_id]['data']['manga_name'] = update.message.text
    
    update.message.reply_text(
        "Great! Now please send me the manga profile picture (send as image):"
    )
    return MANGA_PFP

def manga_pfp(update: Update, context: CallbackContext) -> int:
    """Store the manga profile picture and ask for synopsis."""
    user_id = update.message.from_user.id
    
    # Get the photo file
    photo_file = update.message.photo[-1].get_file()
    img_data = BytesIO()
    photo_file.download(out=img_data)
    user_sessions[user_id]['data']['manga_pfp'] = img_data.getvalue()
    
    update.message.reply_text(
        "Perfect! Now please send the manga synopsis:"
    )
    return SYNOPSIS

def synopsis(update: Update, context: CallbackContext) -> int:
    """Store the synopsis and ask for percentage."""
    user_id = update.message.from_user.id
    user_sessions[user_id]['data']['synopsis'] = update.message.text
    
    update.message.reply_text(
        "Got it! What percentage score would you like to display? (e.g., 86):"
    )
    return PERCENTAGE

def percentage(update: Update, context: CallbackContext) -> int:
    """Store the percentage and ask for year."""
    user_id = update.message.from_user.id
    try:
        percent = int(update.message.text)
        if percent < 0 or percent > 100:
            raise ValueError
        user_sessions[user_id]['data']['percentage'] = percent
    except ValueError:
        update.message.reply_text("Please enter a valid percentage between 0 and 100:")
        return PERCENTAGE
    
    update.message.reply_text(
        "What year was the manga published? (e.g., 2023):"
    )
    return YEAR

def year(update: Update, context: CallbackContext) -> int:
    """Store the year and ask for author."""
    user_id = update.message.from_user.id
    try:
        year = int(update.message.text)
        user_sessions[user_id]['data']['year'] = year
    except ValueError:
        update.message.reply_text("Please enter a valid year:")
        return YEAR
    
    update.message.reply_text(
        "Who is the author of the manga?"
    )
    return AUTHOR

def author(update: Update, context: CallbackContext) -> int:
    """Store the author and ask for template style."""
    user_id = update.message.from_user.id
    user_sessions[user_id]['data']['author'] = update.message.text
    
    # Create keyboard for template selection
    reply_keyboard = [list(TEMPLATES.keys())]
    
    update.message.reply_text(
        "Great! Now choose a template style:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return TEMPLATE_STYLE

def template_style(update: Update, context: CallbackContext) -> int:
    """Store the template style and ask for color scheme."""
    user_id = update.message.from_user.id
    user_sessions[user_id]['data']['template_style'] = TEMPLATES.get(update.message.text, "default")
    
    # Create keyboard for color selection
    reply_keyboard = [list(COLORS.keys())]
    
    update.message.reply_text(
        "Now choose a color scheme:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return COLOR_SCHEME

def color_scheme(update: Update, context: CallbackContext) -> int:
    """Store the color scheme and ask for text style."""
    user_id = update.message.from_user.id
    selected_color = update.message.text
    
    if selected_color == "Custom":
        update.message.reply_text(
            "Please enter your custom color (hex code like #FF5733 or name like 'skyblue'):",
            reply_markup=ReplyKeyboardRemove()
        )
        return CUSTOM_COLOR
    elif selected_color == "Random":
        # Generate a random color
        random_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        user_sessions[user_id]['data']['color_scheme'] = random_color
    else:
        user_sessions[user_id]['data']['color_scheme'] = COLORS[selected_color]
    
    # Create keyboard for font selection
    reply_keyboard = [list(FONTS.keys())]
    
    update.message.reply_text(
        "Now choose a text style:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return TEXT_STYLE

def custom_color(update: Update, context: CallbackContext) -> int:
    """Handle custom color input."""
    user_id = update.message.from_user.id
    color_input = update.message.text
    
    # Validate color input (simple check)
    if color_input.startswith('#') and len(color_input) == 7:
        user_sessions[user_id]['data']['color_scheme'] = color_input
    else:
        # Try to use color name
        user_sessions[user_id]['data']['color_scheme'] = color_input
    
    # Create keyboard for font selection
    reply_keyboard = [list(FONTS.keys())]
    
    update.message.reply_text(
        "Now choose a text style:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return TEXT_STYLE

def text_style(update: Update, context: CallbackContext) -> int:
    """Store the text style and ask for branding."""
    user_id = update.message.from_user.id
    selected_font = update.message.text
    
    if selected_font == "Custom":
        update.message.reply_text(
            "Please send your custom font file (.ttf or .otf format):",
            reply_markup=ReplyKeyboardRemove()
        )
        return CUSTOM_FONT
    
    user_sessions[user_id]['data']['text_style'] = FONTS.get(selected_font, "arial.ttf")
    
    update.message.reply_text(
        "What branding text would you like to display? (e.g., 'waalords'):",
        reply_markup=ReplyKeyboardRemove()
    )
    return BRANDING

def custom_font(update: Update, context: CallbackContext) -> int:
    """Handle custom font upload."""
    user_id = update.message.from_user.id
    
    if update.message.document:
        # Get the font file
        font_file = update.message.document.get_file()
        font_data = BytesIO()
        font_file.download(out=font_data)
        
        # Save the font temporarily
        font_filename = f"temp_font_{user_id}.ttf"
        with open(font_filename, 'wb') as f:
            f.write(font_data.getvalue())
        
        user_sessions[user_id]['data']['text_style'] = font_filename
        user_sessions[user_id]['data']['custom_font'] = True
    else:
        update.message.reply_text("Please send a font file (ttf or otf format):")
        return CUSTOM_FONT
    
    update.message.reply_text(
        "What branding text would you like to display? (e.g., 'waalords'):"
    )
    return BRANDING

def branding(update: Update, context: CallbackContext) -> int:
    """Store the branding and show confirmation."""
    user_id = update.message.from_user.id
    user_sessions[user_id]['data']['branding'] = update.message.text
    
    # Show summary of choices
    summary = f"""
    Here's your manga thumbnail configuration:
    
    Name: {user_sessions[user_id]['data']['manga_name']}
    Author: {user_sessions[user_id]['data']['author']}
    Year: {user_sessions[user_id]['data']['year']}
    Percentage: {user_sessions[user_id]['data']['percentage']}%
    Template: {user_sessions[user_id]['data']['template_style']}
    Color: {user_sessions[user_id]['data']['color_scheme']}
    Font: {user_sessions[user_id]['data']['text_style']}
    Branding: {user_sessions[user_id]['data']['branding']}
    
    Would you like to generate the thumbnail now? (yes/no)
    """
    
    update.message.reply_text(summary)
    return CONFIRMATION

def confirmation(update: Update, context: CallbackContext) -> int:
    """Handle confirmation and generate thumbnail."""
    user_id = update.message.from_user.id
    response = update.message.text.lower()
    
    if response == 'yes':
        update.message.reply_text("Generating your manga thumbnail... Please wait.")
        
        # Generate the thumbnail
        try:
            thumbnail_path = generate_thumbnail(user_id)
            
            # Send the generated image
            with open(thumbnail_path, 'rb') as photo:
                update.message.reply_photo(photo=photo, caption="Here's your manga thumbnail!")
            
            # Clean up
            if user_sessions[user_id]['data'].get('custom_font'):
                os.remove(user_sessions[user_id]['data']['text_style'])
            os.remove(thumbnail_path)
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            update.message.reply_text("Sorry, there was an error generating your thumbnail. Please try again.")
        
        # End conversation
        return ConversationHandler.END
    else:
        update.message.reply_text("Thumbnail generation cancelled.")
        return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel the conversation."""
    user_id = update.message.from_user.id
    if user_id in user_sessions and user_sessions[user_id]['data'].get('custom_font'):
        os.remove(user_sessions[user_id]['data']['text_style'])
    
    update.message.reply_text(
        'Thumbnail generation cancelled.', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def generate_thumbnail(user_id):
    """Generate the manga thumbnail based on user preferences."""
    data = user_sessions[user_id]['data']
    
    # Load template background if exists
    template_path = f"templates/{data['template_style']}.jpg"
    if os.path.exists(template_path):
        img = Image.open(template_path).convert('RGB')
        width, height = img.size
    else:
        # Create a blank image with default size
        width, height = 800, 1000
        img = Image.new('RGB', (width, height), color='white')
    
    draw = ImageDraw.Draw(img)
    
    # Get the primary color
    primary_color = data['color_scheme']
    
    # Load and process the manga profile picture
    pfp_img = Image.open(BytesIO(data['manga_pfp']))
    
    # Resize and make circular
    pfp_size = 300
    pfp_img = pfp_img.resize((pfp_size, pfp_size))
    
    # Create circular mask
    mask = Image.new('L', (pfp_size, pfp_size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, pfp_size, pfp_size), fill=255)
    
    # Apply mask
    pfp_img = ImageOps.fit(pfp_img, mask.size, centering=(0.5, 0.5))
    pfp_img.putalpha(mask)
    
    # Position the profile picture
    img.paste(pfp_img, (width//2 - pfp_size//2, 50), pfp_img)
    
    # Add manga name
    try:
        if data.get('custom_font'):
            font = ImageFont.truetype(data['text_style'], FONT_SIZES['title'])
        else:
            font = ImageFont.truetype(f"fonts/{data['text_style']}", FONT_SIZES['title'])
    except:
        font = ImageFont.load_default()
    
    manga_name = data['manga_name']
    draw.text((width//2, 400), manga_name, fill=primary_color, font=font, anchor="mm")
    
    # Add author and details
    try:
        if data.get('custom_font'):
            details_font = ImageFont.truetype(data['text_style'], FONT_SIZES['details'])
        else:
            details_font = ImageFont.truetype(f"fonts/{data['text_style']}", FONT_SIZES['details'])
    except:
        details_font = ImageFont.load_default()
    
    details = f"AUTHOR\n{data['author']}\n\nCHAPTERS\n128+ Chapters\n\nTYPE\nManga\n\nYEAR\n{data['year']}"
    draw.multiline_text((width//2, 480), details, fill='black', font=details_font, anchor="mm", align="center")
    
    # Add percentage
    percentage = data['percentage']
    try:
        if data.get('custom_font'):
            percent_font = ImageFont.truetype(data['text_style'], FONT_SIZES['percentage'])
        else:
            percent_font = ImageFont.truetype(f"fonts/{data['text_style']}", FONT_SIZES['percentage'])
    except:
        percent_font = ImageFont.load_default()
    
    draw.text((width//2, 650), f"{percentage}%", fill=primary_color, font=percent_font, anchor="mm")
    
    # Add progress bar
    bar_width = 400
    bar_height = 20
    bar_x = width//2 - bar_width//2
    bar_y = 690
    
    # Background bar
    draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], outline=primary_color, width=2)
    
    # Filled bar
    fill_width = int(bar_width * percentage / 100)
    draw.rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + bar_height], fill=primary_color)
    
    # Add synopsis
    synopsis_text = data['synopsis']
    wrapped_text = textwrap.fill(synopsis_text, width=40)
    
    try:
        if data.get('custom_font'):
            synopsis_font = ImageFont.truetype(data['text_style'], FONT_SIZES['synopsis'])
        else:
            synopsis_font = ImageFont.truetype(f"fonts/{data['text_style']}", FONT_SIZES['synopsis'])
    except:
        synopsis_font = ImageFont.load_default()
    
    draw.multiline_text((width//2, 750), wrapped_text, fill='black', font=synopsis_font, anchor="mm", align="center")
    
    # Add branding
    branding_text = data['branding']
    try:
        if data.get('custom_font'):
            branding_font = ImageFont.truetype(data['text_style'], FONT_SIZES['branding'])
        else:
            branding_font = ImageFont.truetype(f"fonts/{data['text_style']}", FONT_SIZES['branding'])
    except:
        branding_font = ImageFont.load_default()
    
    # Position branding in top right
    bbox = draw.textbbox((0, 0), branding_text, font=branding_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text((width - text_width - 20, 20), branding_text, fill=primary_color, font=branding_font)
    
    # Save the image
    filename = f"thumbnail_{user_id}.jpg"
    img.save(filename)
    
    return filename

def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors caused by Updates."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main() -> None:
    """Run the bot."""
    # Get the bot token from environment variable
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("No BOT_TOKEN environment variable found!")
        return
    
    # Create the Updater and pass it your bot's token
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MANGA_NAME: [MessageHandler(Filters.text & ~Filters.command, manga_name)],
            MANGA_PFP: [MessageHandler(Filters.photo, manga_pfp)],
            SYNOPSIS: [MessageHandler(Filters.text & ~Filters.command, synopsis)],
            PERCENTAGE: [MessageHandler(Filters.text & ~Filters.command, percentage)],
            YEAR: [MessageHandler(Filters.text & ~Filters.command, year)],
            AUTHOR: [MessageHandler(Filters.text & ~Filters.command, author)],
            TEMPLATE_STYLE: [MessageHandler(Filters.regex(f'^({"|".join(TEMPLATES.keys())})$'), template_style)],
            COLOR_SCHEME: [
                MessageHandler(Filters.regex(f'^({"|".join(COLORS.keys())})$'), color_scheme),
            ],
            CUSTOM_COLOR: [MessageHandler(Filters.text & ~Filters.command, custom_color)],
            TEXT_STYLE: [
                MessageHandler(Filters.regex(f'^({"|".join(FONTS.keys())})$'), text_style),
            ],
            CUSTOM_FONT: [MessageHandler(Filters.document | Filters.text, custom_font)],
            BRANDING: [MessageHandler(Filters.text & ~Filters.command, branding)],
            CONFIRMATION: [MessageHandler(Filters.text & ~Filters.command, confirmation)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    if os.getenv('WEBHOOK_URL'):
        # Webhook mode for production
        webhook_url = os.getenv('WEBHOOK_URL')
        port = int(os.getenv('PORT', 8443))
        updater.start_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=token,
            webhook_url=f"{webhook_url}/{token}"
        )
    else:
        # Polling mode for development
        updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
