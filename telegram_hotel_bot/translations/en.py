"""
English UI strings and FAQ questions (fill FAQ_ANSWERS when your copy is ready).
"""

from __future__ import annotations

LANG = "en"

MESSAGES: dict[str, str] = {
    "choose_language": "👋 Welcome! Please choose a language / Выберите язык:",
    "welcome": (
        "Hello, {name}! This is the hotel guest bot.\n"
        "Use the menu below for rooms, FAQs, reviews, and support."
    ),
    "main_menu_hint": "Tap a button below 👇",
    "btn_rooms": "🏨 Rooms",
    "btn_all_rooms": "📋 All listings",
    "btn_faq": "❓ FAQ",
    "btn_reviews": "⭐ Reviews",
    "btn_support": "🛎 Support",
    "btn_language": "🌐 Language",
    "btn_useful_links": "🔗 Useful links",
    "useful_links_intro": (
        "📍 <b>Useful links</b> (Google Maps)\n\n"
        "🏨 Hotel location\n"
        "🛒 Nearby supermarkets: Nikora, Carrefour, GoodWill\n"
        "🏬 Nearby malls: Metro City, Grand Mall\n\n"
        "Tap a button below to open the map."
    ),
    "useful_hotel_location": "🏨 Hotel location",
    "rooms_title": (
        "Apartment catalog. «Back» / «Next» switch listings; if a listing has several photos, "
        "use the buttons below the image to browse them."
    ),
    "all_rooms_heading": (
        "<b>All listings ({count})</b>\n\n"
        "Photo cards with descriptions are below."
    ),
    "btn_room_prev": "⬅️ Back",
    "btn_room_next": "Next ➡️",
    "btn_room_photo_prev": "◀️ Photo",
    "btn_room_photo_next": "Photo ▶️",
    "btn_check_dates": "📅 Check dates on Airbnb",
    "btn_ask_manager_dates": "✍️ Ask manager about dates",
    "room_caption": (
        "<b>{title}</b>\n\n"
        "{description}"
    ),
    "ask_dates_prompt": (
        "Send one message with your check-in / check-out dates (or date range) — "
        "a manager will check availability for this listing."
    ),
    "ask_dates_sent": (
        "Your message was forwarded to the manager — @homeybatumi. She will reply as soon as she is available."
    ),
    "room_nav_end": "You’re at the first or last room card already.",
    "room_gallery_caption": "\n\n📷 <i>Photo {cur} of {total}</i>",
    "faq_title": "Frequently asked questions. Tap a question to see the answer.",
    "faq_back": "⬅️ Back to questions",
    "faq_placeholder": (
        "📝 The full answer from our hotel guide will be added soon. "
        "Meanwhile, please contact support — we’ll reply manually."
    ),
    "review_menu_prompt": "Choose: leave a review or read what other guests wrote.",
    "btn_review_write": "✍️ Leave a review",
    "btn_review_browse": "👀 Browse reviews",
    "reviews_list_title": "<b>Recent guest reviews</b>",
    "reviews_empty": "No reviews yet — you can be the first!",
    "review_author_guest": "Guest",
    "review_start": "Rate your stay from 1 to 5 (tap the stars).",
    "review_ask_text": "Please send a short review text in one message.",
    "review_thanks": "Thank you! Your review has been saved.",
    "review_thanks_pending": (
        "Thank you! Your review was sent for review. After a manager approves it, it will appear under "
        "«Browse reviews»."
    ),
    "admin_review_pending": (
        "<b>New review pending moderation</b> #{review_id}\n"
        "user_id: <code>{user_id}</code>\n"
        "Rating: {stars}\n\n"
        "{text}"
    ),
    "btn_review_approve": "✅ Approve",
    "review_approve_ok": "Review approved — guests can see it now.",
    "review_approve_fail": "Could not approve (already approved or not found).",
    "review_not_admin": "You don’t have permission to do that.",
    "review_cancelled": "Review flow cancelled. You can open the menu again.",
    "support_intro": "Describe your issue in one message — we’ll escalate it to the manager.",
    "support_sent": (
        "Your message was forwarded to the manager — @homeybatumi. She will reply as soon as she is available."
    ),
    "support_no_admins": (
        "Admin is not configured yet (ADMIN_IDS missing in .env). "
        "Please email the hotel or try again later."
    ),
    "support_text_only": "Please send your message as plain text (no photos or stickers).",
    "language_changed": "Language updated.",
    "use_start": "Tap /start to choose a language and open the menu.",
    "loyalty_soon": "The loyalty program will appear in this bot soon. Stay tuned!",
    "cmd_cancel": "Cancel anytime with /cancel",
    "flow_cancelled": "The current action was cancelled. The main menu is available again.",
    "cmd_menu": "Main menu. Any unfinished flow (review, support, date request) was reset.",
    "rate_limit_review": "You’re posting reviews too often. Try again in about {minutes} min.",
    "rate_limit_support": "Too many support messages. Please try again in about {minutes} min.",
    "support_send_failed": (
        "Your message could not be delivered. Please ask an admin to open the bot and tap /start."
    ),
}

FAQ_ITEMS: list[dict[str, str]] = [
    {"key": "hours", "question": "What are check-in and check-out times?"},
    {"key": "parking", "question": "Is parking available and how much does it cost?"},
    {"key": "pets", "question": "Are pets allowed?"},
    {"key": "breakfast", "question": "Is breakfast included? What are restaurant hours?"},
    {"key": "cancel", "question": "How can I cancel or modify a booking?"},
    {"key": "transfer", "question": "Do you offer airport / train station transfers?"},
    {"key": "reception", "question": "How do I reach reception after hours?"},
    {"key": "payment", "question": "Which payment methods do you accept?"},
    {"key": "ac", "question": "Is there A/C?"},
    {"key": "smoking", "question": "What is your smoking policy?"},
]

FAQ_ANSWERS: dict[str, str] = {
    "hours": "Check-in: from 3:00 PM (15:00).\nCheck-out: by 11:00 AM (11:00).",
    "parking": "Yes. Cost: 15 GEL per day.",
    "pets": "No, pets are not allowed.",
    "breakfast": (
        "Breakfast is charged separately.\n"
        "Price: 45 GEL per person.\n"
        "Hours: 8:00 AM – 11:00 AM."
    ),
    "cancel": "Please contact us.",
    "transfer": "We can arrange a taxi for you.",
    "reception": (
        "Use the phone in your apartment.\n"
        "Dial 01."
    ),
    "payment": "Cash, bank transfer, cryptocurrency.",
    "ac": "Yes — A/C is available and you can adjust the temperature.",
    "smoking": (
        "Smoking in the apartment is not allowed.\n"
        "Fine: $200."
    ),
}
