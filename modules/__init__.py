"""
AstralModules — official plugin repository for AstralBot.

This package is loaded by AstralBot's plugin loader at startup. Plugins live
in subdirectories by category:

    modules/admin/      group admin: promote, ban, kick, mute, pin, purge, lock
    modules/utils/      utilities:   afk, notes, filters, warns, greetings, snips
    modules/media/      media tools:  download, upload, sticker, songs, telegraph, qr
    modules/ai/         AI/LLM:       llm, tts, asr
    modules/fun/        fun/info:     quote, whois, weather, currency, wikipedia, animate
    modules/privacy/    privacy:      pmpermit, antipin, antichannel, firstmsg, blacklist

Each plugin file declares module-level manifest attributes (__plugin_name__,
__plugin_author__, __plugin_version__, __plugin_license__,
__plugin_description__, __plugin_category__) and registers its commands via
the AstralBot decorator API:

    from astralbot import on_command, help_menu

For more, see https://github.com/AstralBot/AstralBot
"""
