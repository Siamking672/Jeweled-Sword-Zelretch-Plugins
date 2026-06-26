# Jeweled Sword Zelretch Plugins

Plugin source repository for **Jeweled Sword Zelretch**.

The main wrapper repository downloads this repo by default:

```text
Siamking672/Jeweled-Sword-Zelretch-Plugins
```

## Runtime stack

- Python 3.11
- Kurigram installed through `kurigram`
- Pyrogram-compatible import namespace: `from pyrogram ...`
- MongoDB through Motor
- Docker-only deployment

## Required variables

```env
API_HASH=
API_ID=
BOT_TOKEN=
DATABASE_URL=
LOGGER_ID=
OWNER_ID=
```

Optional:

```env
DATABASE_NAME=JeweledSwordZelretch
HANDLERS=. ! ?
PLUGINS_REPO=Siamking672/Jeweled-Sword-Zelretch-Plugins
PLUGINS_BRANCH=main
```

## Docker deployment

```bash
cp example.env .env
nano .env
docker compose up --build -d
```

View logs:

```bash
docker compose logs -f
```

Stop:

```bash
docker compose down
```

## Plugin template

```python
from . import HelpMenu, on_message, zelretch


@on_message("hii")
async def hi(_, message):
    await zelretch.edit(message, "Hello!")


HelpMenu("hii").add(
    "hii", None, "Says hello."
).done()
```

## Notes

- Forced hardcoded channel auto-join remains removed.
- The GPL license file is retained.
