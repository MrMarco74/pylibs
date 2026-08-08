# Telegram Module

Das `telegram` Modul bietet einen einfachen und flexiblen Wrapper um die Telegram Bot API. Es eignet sich perfekt für Automatisierungs-Skripte, um sich selbst bei Langläufern über den Status zu informieren oder fertige Medien (Bilder, Videos) an das Handy zu senden.

## Voraussetzungen

1. Einen Telegram Bot über den `@BotFather` erstellen und den API-Token kopieren.
2. Dem eigenen Bot eine Nachricht schicken.
3. Die eigene Chat-ID herausfinden (z.B. über `@userinfobot`).

## Nutzung

Die `TelegramBot` Klasse bietet diverse Methoden zum Versenden von verschiedenen Medientypen an.

```python
from pylibs.telegram import TelegramBot

# Initialisierung mit deinen Zugangsdaten
BOT_TOKEN = "DEIN_BOT_TOKEN"
CHAT_ID = "DEINE_CHAT_ID"

bot = TelegramBot(bot_token=BOT_TOKEN, chat_id=CHAT_ID)

# Textnachricht senden
bot.send_message("🚀 Der Trainingslauf wurde erfolgreich gestartet!")

# Ein generiertes Bild senden
bot.send_photo("/pfad/zum/bild.png", caption="Hier ist das neue Bild!")

# Ein fertiges Video senden
bot.send_video("/pfad/zum/video.mp4", caption="Das Video ist fertig gerendert.")

# Ein beliebiges Dokument (z.B. Log-Datei) senden
bot.send_document("/pfad/zur/log.txt", caption="Fehlerprotokoll")

# Eine Audiodatei senden
bot.send_audio("/pfad/zum/audio.mp3")
```

## Fehlerbehandlung

Die Methoden fangen Verbindungs- und API-Fehler automatisch ab, drucken sie auf der Konsole (`print()`) und geben `False` zurück. Bei erfolgreichem Versand wird `True` zurückgegeben.
