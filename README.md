Telegram Bot for German Dialog Creation
========================================

This is a Telegram Bot that uses the OpenAI API to create German Dialogs.


Deploy to GCP with:

```bash
gcloud functions deploy germandialogcreatorbot --region=europe-west1 --gen2 --allow-unauthenticated --set-env-vars "OPENAI_API_KEY=<OpenAi API Token> ,BOT_TOKEN=<Telegram Bot Token>"  --runtime python39 --trigger-http --memory 512MB
```
