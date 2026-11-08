# Job scan bot

Every 2 hours GitHub Actions runs a full sweep of Israeli student and intern postings and sends the new ones to Telegram. No LLM is involved, so it costs no tokens.

## Setup

1. Create a Telegram bot: message @BotFather, send `/newbot`, copy the token. Send any message to your new bot, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `chat` then `id`.
2. In the repo go to Settings, Secrets and variables, Actions, and add two repository secrets: `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID`. Never commit them or paste them into a chat.
3. In the Actions tab, open "Job scan" and press "Run workflow" once to check it works. After that it runs by itself every 2 hours.

## How it works

- `.github/workflows/scan.yml` is the schedule. `scan/run_scan.sh` runs every scanner and writes `new_candidates.json`, the postings not seen before.
- `notify.py` keeps the ones with technical titles and sends them to Telegram.
- `scan/seen.json` remembers what was already sent. It is committed back to the repo only after Telegram accepted the message, so a failed send is retried on the next run.

## Tuning

- What counts as a student role and which titles are dropped: `scan/merge.py` (`STU`, `BAD`, `T`).
- Extra title filter before Telegram: `TECH` in `notify.py`.
- Sources and companies: `scan/*.py`, `scan/extra_companies.json`.
- Interval: the `cron` line in `.github/workflows/scan.yml`. A full sweep takes about 30 minutes.

## Notes

- The sweep takes about 30 minutes, so a private repo on the free plan (2,000 minutes a month) would run out in about a week. Keep the repo public, where Actions minutes are free, or run `scan/run_scan.sh` from cron on your own machine.
- GitHub pauses scheduled workflows in a public repo after 60 days without repository activity. The commit of `seen.json` normally counts, but if alerts stop, open the Actions tab and press "Enable workflow".
- Some sites may block GitHub's servers. Check the first run's log for sources that returned errors.
