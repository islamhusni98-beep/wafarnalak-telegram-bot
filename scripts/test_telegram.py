"""Send a one-time test message when run manually."""
from telegram_api import send_message


def main() -> None:
    send_message(
        "✅ تم ربط بوت وفرنالك عروض بالقناة بنجاح.\n"
        "هذه رسالة اختبار، ويمكن حذفها بعد التأكد."
    )
    print("Telegram test message sent.")


if __name__ == "__main__":
    main()
