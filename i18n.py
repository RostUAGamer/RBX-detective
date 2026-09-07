"""
Localization service for RBX Detective.
Supported languages: Ukrainian (uk), English (en), German (de), Chinese (zh).
Clean 100% public version without cookies or tokens.
"""
import json
import os

LANGUAGES = {
    "uk": "Українська",
    "en": "English",
    "de": "Deutsch",
    "zh": "中文"
}

TRANSLATIONS = {
    "uk": {
        "app_title": "RBX Detective — Roblox Player Intel & Tracker",
        "search_placeholder": "Введіть нікнейм або User ID гравця Roblox...",
        "search_btn": "Знайти",
        "settings_btn_tooltip": "Налаштування мови",
        "status_initial": "Введіть нікнейм або ID гравця та натисніть «Знайти»",
        "status_searching": "⏳ Отримую дані для «{query}» з серверів Roblox...",
        "status_empty_query": "⚠️ Будь ласка, введіть нікнейм або ID!",
        "status_success": "✅ Успішно завантажено профіль @{username}",
        "status_error": "❌ Помилка: {error}",
        "status_launching_client": "🚀 Запускаю клієнт Roblox (Place ID: {place_id})...",
        "status_opened_browser": "🌐 Відкрито сторінку гри у браузері",
        "status_privacy_restricted": "ℹ️ У гравця вимкнено можливість приєднання або приховано Place ID.",
        "offline": "Offline",
        "online_site": "Online (Сайт)",
        "in_game": "У грі",
        "in_studio": "У Studio",
        "btn_join_game": "🎮 Приєднатися до гри",
        "btn_player_not_ingame": "🎮 Гравець не в грі",
        "in_game_label": "🎮 У грі:\n{game_title}",
        "btn_open_profile": "Відкрити профіль Roblox ↗",
        "tab_profile": "👤 Профіль",
        "tab_game_badges": "🏆 Бейджі ігор (Badges API)",
        "tab_groups": "👥 Групи",
        "tab_past_names": "📜 Нікнейми",
        "tab_roblox_badges": "🏅 Roblox бейджі",
        "stat_userid": "User ID",
        "stat_verification": "Верифікація",
        "stat_created": "Дата реєстрації",
        "stat_age": "Вік акаунта",
        "stat_friends": "Друзів",
        "stat_followers": "Підписників",
        "verified_yes": "✓ Підтверджено",
        "verified_no": "Ні",
        "banned_badge": "⛔ ЗАБАНЕНИЙ",
        "active_badge": "✓ Активний",
        "bio_title": "Опис гравця (About / Bio):",
        "no_description": "(Опис відсутній)",
        "groups_header": "Групи (всього: {count}):",
        "groups_empty": "Користувач не є учасником публічних груп",
        "group_role_rank": "Роль: {role} (Ранг: {rank})  •  Учасників: {members:,}",
        "past_names_header": "Попередні нікнейми ({count}):",
        "past_names_empty": "Історія минулих імен порожня (або гравець ніколи не змінював нік)",
        "roblox_badges_header": "Офіційні нагороди Roblox ({count}):",
        "roblox_badges_empty": "Офіційних бейджів не знайдено",
        "game_badges_header": "🏆 Бейджі ігор користувача ({count}):",
        "game_badges_empty": "У гравця немає публічних ігор зі створеними бейджами (або бейджі приховано).",
        "game_creator_prefix": "Гра: {gameName}\n{desc}",
        "settings_title": "Налаштування мови",
        "select_language": "Оберіть мову інтерфейсу:",
        "btn_save": "Зберегти",
        "years_days_ago": "{years} р. {days} дн. тому",
        "days_ago": "{days} дн. тому"
    },
    "en": {
        "app_title": "RBX Detective — Roblox Player Intel & Tracker",
        "search_placeholder": "Enter Roblox player username or User ID...",
        "search_btn": "Search",
        "settings_btn_tooltip": "Language Settings",
        "status_initial": "Enter player username or ID and press «Search»",
        "status_searching": "⏳ Fetching data for «{query}» from Roblox servers...",
        "status_empty_query": "⚠️ Please enter a username or ID!",
        "status_success": "✅ Successfully loaded profile @{username}",
        "status_error": "❌ Error: {error}",
        "status_launching_client": "🚀 Launching Roblox client (Place ID: {place_id})...",
        "status_opened_browser": "🌐 Opened game webpage in browser",
        "status_privacy_restricted": "ℹ️ Player has joins disabled or Place ID hidden in privacy settings.",
        "offline": "Offline",
        "online_site": "Online (Website)",
        "in_game": "In-Game",
        "in_studio": "In Studio",
        "btn_join_game": "🎮 Join Game",
        "btn_player_not_ingame": "🎮 Player Not In-Game",
        "in_game_label": "🎮 In Game:\n{game_title}",
        "btn_open_profile": "Open Roblox Profile ↗",
        "tab_profile": "👤 Profile",
        "tab_game_badges": "🏆 Game Badges (Badges API)",
        "tab_groups": "👥 Groups",
        "tab_past_names": "📜 Past Usernames",
        "tab_roblox_badges": "🏅 Roblox Badges",
        "stat_userid": "User ID",
        "stat_verification": "Verification",
        "stat_created": "Join Date",
        "stat_age": "Account Age",
        "stat_friends": "Friends",
        "stat_followers": "Followers",
        "verified_yes": "✓ Verified",
        "verified_no": "No",
        "banned_badge": "⛔ BANNED",
        "active_badge": "✓ Active",
        "bio_title": "Player Bio (About):",
        "no_description": "(No bio provided)",
        "groups_header": "Groups (Total: {count}):",
        "groups_empty": "User is not a member of any public group",
        "group_role_rank": "Role: {role} (Rank: {rank})  •  Members: {members:,}",
        "past_names_header": "Past Usernames ({count}):",
        "past_names_empty": "Past username history is empty (never changed name)",
        "roblox_badges_header": "Official Roblox Awards ({count}):",
        "roblox_badges_empty": "No official Roblox badges found",
        "game_badges_header": "🏆 User's Game Badges ({count}):",
        "game_badges_empty": "User has no public games with created badges.",
        "game_creator_prefix": "Game: {gameName}\n{desc}",
        "settings_title": "Language Settings",
        "select_language": "Choose interface language:",
        "btn_save": "Save",
        "years_days_ago": "{years} yrs {days} days ago",
        "days_ago": "{days} days ago"
    },
    "de": {
        "app_title": "RBX Detective — Roblox Spieler-Info & Tracker",
        "search_placeholder": "Roblox-Benutzernamen oder User-ID eingeben...",
        "search_btn": "Suchen",
        "settings_btn_tooltip": "Spracheinstellungen",
        "status_initial": "Geben Sie einen Namen oder eine ID ein und drücken Sie «Suchen»",
        "status_searching": "⏳ Daten für «{query}» werden von Roblox-Servern geladen...",
        "status_empty_query": "⚠️ Bitte geben Sie einen Benutzernamen oder eine ID ein!",
        "status_success": "✅ Profil @{username} erfolgreich geladen",
        "status_error": "❌ Fehler: {error}",
        "status_launching_client": "🚀 Roblox-Client wird gestartet (Place ID: {place_id})...",
        "status_opened_browser": "🌐 Spielseite im Browser geöffnet",
        "status_privacy_restricted": "ℹ️ Spieler hat Beitreten deaktiviert oder Place-ID verborgen.",
        "offline": "Offline",
        "online_site": "Online (Webseite)",
        "in_game": "Im Spiel",
        "in_studio": "Im Studio",
        "btn_join_game": "🎮 Spiel beitreten",
        "btn_player_not_ingame": "🎮 Nicht im Spiel",
        "in_game_label": "🎮 Im Spiel:\n{game_title}",
        "btn_open_profile": "Roblox-Profil öffnen ↗",
        "tab_profile": "👤 Profil",
        "tab_game_badges": "🏆 Spielabzeichen (Badges API)",
        "tab_groups": "👥 Gruppen",
        "tab_past_names": "📜 Frühere Namen",
        "tab_roblox_badges": "🏅 Roblox-Abzeichen",
        "stat_userid": "Benutzer-ID",
        "stat_verification": "Verifizierung",
        "stat_created": "Registrierungsdatum",
        "stat_age": "Konto-Alter",
        "stat_friends": "Freunde",
        "stat_followers": "Follower",
        "verified_yes": "✓ Verifiziert",
        "verified_no": "Nein",
        "banned_badge": "⛔ GESPERRT",
        "active_badge": "✓ Aktiv",
        "bio_title": "Spieler-Biografie (Über mich):",
        "no_description": "(Keine Beschreibung vorhanden)",
        "groups_header": "Gruppen (Gesamt: {count}):",
        "groups_empty": "Benutzer ist in keinen öffentlichen Gruppen",
        "group_role_rank": "Rolle: {role} (Rang: {rank})  •  Mitglieder: {members:,}",
        "past_names_header": "Frühere Namen ({count}):",
        "past_names_empty": "Keine früheren Namen vorhanden (Name nie geändert)",
        "roblox_badges_header": "Offizielle Roblox-Abzeichen ({count}):",
        "roblox_badges_empty": "Keine offiziellen Roblox-Abzeichen gefunden",
        "game_badges_header": "🏆 Spielabzeichen des Benutzers ({count}):",
        "game_badges_empty": "Benutzer hat keine öffentlichen Spiele mit erstellten Abzeichen.",
        "game_creator_prefix": "Spiel: {gameName}\n{desc}",
        "settings_title": "Spracheinstellungen",
        "select_language": "Wählen Sie die Benutzeroberflächensprache:",
        "btn_save": "Speichern",
        "years_days_ago": "vor {years} J. {days} T.",
        "days_ago": "vor {days} T."
    },
    "zh": {
        "app_title": "RBX Detective — Roblox 玩家信息与追踪器",
        "search_placeholder": "输入 Roblox 玩家用户名或用户 ID...",
        "search_btn": "搜索",
        "settings_btn_tooltip": "语言设置",
        "status_initial": "输入玩家用户名或 ID，然后点击“搜索”",
        "status_searching": "⏳ 正在从 Roblox 服务器获取“{query}”的数据...",
        "status_empty_query": "⚠️ 请输入用户名或 ID！",
        "status_success": "✅ 成功加载玩家资料 @{username}",
        "status_error": "❌ 错误: {error}",
        "status_launching_client": "🚀 正在启动 Roblox 客户端 (Place ID: {place_id})...",
        "status_opened_browser": "🌐 已在浏览器中打开游戏页面",
        "status_privacy_restricted": "ℹ️ 玩家已关闭加入功能或在隐私设置中隐藏了 Place ID。",
        "offline": "离线",
        "online_site": "在线 (网页)",
        "in_game": "游戏中",
        "in_studio": "在 Studio 中",
        "btn_join_game": "🎮 加入游戏",
        "btn_player_not_ingame": "🎮 玩家不在游戏中",
        "in_game_label": "🎮 正在玩:\n{game_title}",
        "btn_open_profile": "打开 Roblox 个人主页 ↗",
        "tab_profile": "👤 个人资料",
        "tab_game_badges": "🏆 游戏徽章 (Badges API)",
        "tab_groups": "👥 群组",
        "tab_past_names": "📜 曾用名",
        "tab_roblox_badges": "🏅 Roblox 官方徽章",
        "stat_userid": "用户 ID",
        "stat_verification": "认证状态",
        "stat_created": "注册日期",
        "stat_age": "账号年龄",
        "stat_friends": "好友数",
        "stat_followers": "粉丝数",
        "verified_yes": "✓ 已认证",
        "verified_no": "未认证",
        "banned_badge": "⛔ 已封禁",
        "active_badge": "✓ 正常",
        "bio_title": "玩家简介 (About):",
        "no_description": "(暂无个人简介)",
        "groups_header": "群组 (共计: {count}):",
        "groups_empty": "用户未加入任何公开群组",
        "group_role_rank": "职位: {role} (等级: {rank})  •  成员数: {members:,}",
        "past_names_header": "曾用名历史 ({count}):",
        "past_names_empty": "无曾用名历史 (从未改过名)",
        "roblox_badges_header": "Roblox 官方奖项 ({count}):",
        "roblox_badges_empty": "未找到官方 Roblox 徽章",
        "game_badges_header": "🏆 玩家游戏徽章 ({count}):",
        "game_badges_empty": "用户没有带有公开徽章的游戏。",
        "game_creator_prefix": "游戏: {gameName}\n{desc}",
        "settings_title": "语言设置",
        "select_language": "选择界面语言:",
        "btn_save": "保存",
        "years_days_ago": "{years} 年 {days} 天前",
        "days_ago": "{days} 天前"
    }
}

CONFIG_FILE = "config.json"


class I18n:
    current_lang = "uk"

    @classmethod
    def load_config(cls):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    cls.current_lang = cfg.get("language", "uk")
            except Exception:
                pass
        return cls.current_lang

    @classmethod
    def set_language(cls, lang_code: str):
        if lang_code in TRANSLATIONS:
            cls.current_lang = lang_code
            try:
                cfg = {}
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                cfg["language"] = lang_code
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=4)
            except Exception:
                pass

    @classmethod
    def t(cls, key: str, **kwargs) -> str:
        lang_dict = TRANSLATIONS.get(cls.current_lang, TRANSLATIONS["uk"])
        text = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text
