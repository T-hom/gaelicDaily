import json
import os
import requests
from datetime import datetime, timezone


def loadWords(path="words.json"):
    scriptDir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(scriptDir, path)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def getTodaysWord(words):
    today = datetime.now(timezone.utc)  # using utc here so the word always switcehs at the same time, using GMT we would need one for summer one for winter
    dayNumber = (today - datetime(2026, 1, 1, tzinfo=timezone.utc)).days
    return words[dayNumber % len(words)]


def formatMessage(wordEntry):
    parts = wordEntry["example"].split(" — ")
    gaelicExample = parts[0]
    englishExample = parts[1] if len(parts) > 1 else ""

    msg = (
        f"FACAL AN LATHA | Word of the Day\n"
        f"\n"
        f"{wordEntry['word'].upper()}: {wordEntry['meaning']}\n"
        f"Say: /{wordEntry['pronunciation']}/\n"
        f"\n"
        f"Ex: {gaelicExample}\n"
        f"({englishExample})"
    )

    return msg


def getRecipients():
    raw = os.environ["RECIPIENTS"] 
    numbers = [n.strip() for n in raw.split(",") if n.strip()]
    if not numbers:
        raise ValueError("No phone numbers in RECIPIENTS env var")
    return numbers


def sendSms(message, recipients):
    username = os.environ["CLICKSEND_USERNAME"]
    apiKey = os.environ["CLICKSEND_API_KEY"]
    senderId = os.environ.get("CLICKSEND_SENDER_ID", "GaelicWord")

    messages = [
        {
            "source": "gaelic-daily",
            "from": senderId,
            "body": message,
            "to": number,
        }
        for number in recipients
    ]

    response = requests.post(
        "https://rest.clicksend.com/v3/sms/send",
        json={"messages": messages},
        auth=(username, apiKey),
        headers={"Content-Type": "application/json"},
    )

    data = response.json()

    if data.get("http_code") == 200: #200=Success
        for msg in data.get("data", {}).get("messages", []):
            print(f"  -> {msg.get('to')}: {msg.get('status')}")
        print("Done!")
    else:
        print(f"Error: {data}")
        response.raise_for_status()

    return data


def main():
    words = loadWords()
    todaysWord = getTodaysWord(words)
    recipients = getRecipients()

    print(f"Today's word: {todaysWord['word']} ({todaysWord['meaning']})")
    print(f"Sending to {len(recipients)} recipient(s): {recipients}")

    message = formatMessage(todaysWord)
    print(f"\n--- Message Preview ---\n{message}\n-----------------------\n")

    sendSms(message, recipients)


if __name__ == "__main__":
    main()