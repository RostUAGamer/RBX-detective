"""
Roblox API Service for RBX Detective.
Retrieves 100% public player information from official Roblox APIs.
No .ROBLOSECURITY, tokens, or cookies required.
"""
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List
from i18n import I18n


class RobloxAPI:
    SESSION = requests.Session()
    SESSION.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    })

    @classmethod
    def get_user_by_name(cls, username: str) -> Optional[Dict[str, Any]]:
        """Look up user by exact or requested username."""
        url = "https://users.roblox.com/v1/usernames/users"
        resp = cls.SESSION.post(url, json={"usernames": [username], "excludeBannedUsers": False}, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            if data:
                return data[0]
        return None

    @classmethod
    def get_user_details(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Fetch full user details (description, created date, isBanned, etc.)."""
        url = f"https://users.roblox.com/v1/users/{user_id}"
        resp = cls.SESSION.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return None

    @classmethod
    def get_game_details_by_place(cls, place_id: int) -> Optional[Dict[str, Any]]:
        """Fetches game/experience details by placeId (cross-checked via universeId)."""
        try:
            u_res = cls.SESSION.get(f"https://apis.roblox.com/universes/v1/places/{place_id}/universe", timeout=6)
            if u_res.status_code == 200:
                uid = u_res.json().get("universeId")
                g_res = cls.SESSION.get(f"https://games.roblox.com/v1/games?universeIds={uid}", timeout=6)
                if g_res.status_code == 200:
                    data = g_res.json().get("data", [])
                    if data:
                        return data[0]
        except Exception:
            pass
        return None

    @classmethod
    def get_presence(cls, user_id: int) -> Dict[str, Any]:
        """Fetch presence status (Offline, Online, InGame, InStudio) and game info."""
        url = "https://presence.roblox.com/v1/presence/users"
        try:
            resp = cls.SESSION.post(url, json={"userIds": [user_id]}, timeout=10)
            if resp.status_code == 200:
                presences = resp.json().get("userPresences", [])
                if presences:
                    p = presences[0]
                    type_map = {
                        0: (I18n.t("offline"), "#80848e"),
                        1: (I18n.t("online_site"), "#23a55a"),
                        2: (I18n.t("in_game"), "#5865f2"),
                        3: (I18n.t("in_studio"), "#f0b232")
                    }
                    ptype = p.get("userPresenceType", 0)
                    status_str, color = type_map.get(ptype, (I18n.t("offline"), "#80848e"))
                    
                    place_id = p.get("placeId")
                    game_id = p.get("gameId")
                    game_name = p.get("lastLocation", "")

                    if place_id:
                        g_info = cls.get_game_details_by_place(place_id)
                        if g_info:
                            game_name = g_info.get("name", game_name)

                    return {
                        "presenceType": ptype,
                        "status": status_str,
                        "color": color,
                        "gameName": game_name,
                        "placeId": place_id,
                        "gameId": game_id,
                        "lastLocation": p.get("lastLocation", ""),
                        "lastOnline": p.get("lastOnline")
                    }
        except Exception:
            pass
        return {
            "presenceType": 0,
            "status": I18n.t("offline"),
            "color": "#80848e",
            "gameName": "",
            "placeId": None,
            "gameId": None,
            "lastLocation": "",
            "lastOnline": None
        }

    @classmethod
    def get_avatar_thumbnails(cls, user_id: int) -> Dict[str, Optional[str]]:
        """Fetch avatar headshot and full body thumbnail URLs."""
        headshot_url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png&isCircular=false"
        bust_url = f"https://thumbnails.roblox.com/v1/users/avatar-bust?userIds={user_id}&size=150x150&format=Png&isCircular=false"
        
        result = {"headshot": None, "bust": None}
        try:
            resp = cls.SESSION.get(headshot_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data and data[0].get("state") == "Completed":
                    result["headshot"] = data[0].get("imageUrl")

            resp_bust = cls.SESSION.get(bust_url, timeout=10)
            if resp_bust.status_code == 200:
                data_b = resp_bust.json().get("data", [])
                if data_b and data_b[0].get("state") == "Completed":
                    result["bust"] = data_b[0].get("imageUrl")
        except Exception:
            pass
        return result

    @classmethod
    def get_social_counts(cls, user_id: int) -> Dict[str, int]:
        """Fetch friends, followers, and followings counts."""
        counts = {"friends": 0, "followers": 0, "followings": 0}
        try:
            f_resp = cls.SESSION.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count", timeout=10)
            if f_resp.status_code == 200:
                counts["friends"] = f_resp.json().get("count", 0)

            fol_resp = cls.SESSION.get(f"https://friends.roblox.com/v1/users/{user_id}/followers/count", timeout=10)
            if fol_resp.status_code == 200:
                counts["followers"] = fol_resp.json().get("count", 0)

            folw_resp = cls.SESSION.get(f"https://friends.roblox.com/v1/users/{user_id}/followings/count", timeout=10)
            if folw_resp.status_code == 200:
                counts["followings"] = folw_resp.json().get("count", 0)
        except Exception:
            pass
        return counts

    @classmethod
    def get_past_usernames(cls, user_id: int) -> list:
        """Fetch past usernames history."""
        url = f"https://users.roblox.com/v1/users/{user_id}/username-history?limit=25&sortOrder=Desc"
        try:
            resp = cls.SESSION.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                return [item.get("name") for item in data if item.get("name")]
        except Exception:
            pass
        return []

    @classmethod
    def get_groups(cls, user_id: int) -> list:
        """Fetch public groups and roles for user."""
        url = f"https://groups.roblox.com/v1/users/{user_id}/groups/roles"
        try:
            resp = cls.SESSION.get(url, timeout=10)
            if resp.status_code == 200:
                items = resp.json().get("data", [])
                groups = []
                for item in items:
                    g = item.get("group", {})
                    r = item.get("role", {})
                    groups.append({
                        "id": g.get("id"),
                        "name": g.get("name"),
                        "role": r.get("name"),
                        "rank": r.get("rank"),
                        "memberCount": g.get("memberCount", 0)
                    })
                return groups
        except Exception:
            pass
        return []

    @classmethod
    def get_roblox_badges(cls, user_id: int) -> list:
        """
        Fetch official Roblox badges (Veteran, Homestead, Administrator, etc.)
        100% public, works without any authentication.
        """
        url = f"https://accountinformation.roblox.com/v1/users/{user_id}/roblox-badges"
        try:
            resp = cls.SESSION.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []

    @classmethod
    def get_created_games_badges(cls, user_id: int, max_games: int = 6) -> list:
        """
        Public Badges API integration (badges.roblox.com):
        Fetches public games created by the user and retrieves all badges created for those games
        via https://badges.roblox.com/v1/universes/{universeId}/badges (100% public, no cookie).
        """
        badges_found = []
        try:
            games_url = f"https://games.roblox.com/v2/users/{user_id}/games?accessFilter=Public&limit={max_games}&sortOrder=Desc"
            g_resp = cls.SESSION.get(games_url, timeout=10)
            if g_resp.status_code == 200:
                games = g_resp.json().get("data", [])
                for game in games:
                    universe_id = game.get("id")
                    game_name = game.get("name", "Roblox Experience")
                    if universe_id:
                        b_url = f"https://badges.roblox.com/v1/universes/{universe_id}/badges?limit=25&sortOrder=Desc"
                        b_resp = cls.SESSION.get(b_url, timeout=6)
                        if b_resp.status_code == 200:
                            b_data = b_resp.json().get("data", [])
                            for b in b_data:
                                badges_found.append({
                                    "id": b.get("id"),
                                    "name": b.get("name"),
                                    "description": b.get("description", ""),
                                    "gameName": game_name,
                                    "enabled": b.get("enabled", True)
                                })
        except Exception:
            pass
        return badges_found

    @classmethod
    def find_random_player(cls) -> Optional[Dict[str, Any]]:
        """
        Find a random public Roblox player by sampling user IDs from recent registrations.
        Returns basic user data dict or None.
        """
        import random
        # Roblox has hundreds of millions of user IDs. We sample in a high-traffic range.
        MAX_ATTEMPTS = 20
        for _ in range(MAX_ATTEMPTS):
            try:
                uid = random.randint(1_000_000, 6_000_000_000)
                resp = cls.SESSION.get(f"https://users.roblox.com/v1/users/{uid}", timeout=6)
                if resp.status_code == 200:
                    data = resp.json()
                    # Skip banned or users without name
                    if data.get("name") and not data.get("isBanned", False):
                        return data
            except Exception:
                continue
        return None

    @classmethod
    def find_joinable_player(cls, max_candidates: int = 60) -> Optional[Dict[str, Any]]:
        """
        Find a random Roblox player who is currently in-game AND has a public place ID
        (meaning followers/friends can join them — join is open/not restricted).
        Returns the full profile dict (same format as fetch_full_profile) or None.
        """
        import random
        checked = 0
        while checked < max_candidates:
            checked += 1
            try:
                uid = random.randint(1_000_000, 6_000_000_000)
                user_resp = cls.SESSION.get(f"https://users.roblox.com/v1/users/{uid}", timeout=5)
                if user_resp.status_code != 200:
                    continue
                udata = user_resp.json()
                if not udata.get("name") or udata.get("isBanned", False):
                    continue

                # Check presence
                pres_resp = cls.SESSION.post(
                    "https://presence.roblox.com/v1/presence/users",
                    json={"userIds": [uid]},
                    timeout=6
                )
                if pres_resp.status_code != 200:
                    continue
                presences = pres_resp.json().get("userPresences", [])
                if not presences:
                    continue
                p = presences[0]
                # presenceType == 2 means InGame; placeId must be set for join to work
                if p.get("userPresenceType") != 2:
                    continue
                place_id = p.get("placeId")
                if not place_id:
                    continue

                # Player is in-game with a visible placeId — joinable!
                return cls.fetch_full_profile(str(uid))
            except Exception:
                continue
        return None

    @classmethod
    def fetch_full_profile(cls, query: str) -> Dict[str, Any]:
        """Coordinates 100% public data fetching."""
        user_basic = None
        if query.isdigit():
            user_basic = {"id": int(query)}
        else:
            user_basic = cls.get_user_by_name(query)
            if not user_basic:
                raise ValueError(f"User '{query}' not found.")

        uid = user_basic["id"]
        details = cls.get_user_details(uid)
        if not details:
            raise ValueError(f"Unable to load profile data for ID {uid}.")

        created_str = details.get("created", "")
        formatted_date = created_str
        age_str = ""
        if created_str:
            try:
                dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                formatted_date = dt.strftime("%d.%m.%Y, %H:%M")
                now = datetime.now(dt.tzinfo)
                diff = now - dt
                years = diff.days // 365
                remaining_days = diff.days % 365
                if years > 0:
                    age_str = I18n.t("years_days_ago", years=years, days=remaining_days)
                else:
                    age_str = I18n.t("days_ago", days=diff.days)
            except Exception:
                pass

        presence = cls.get_presence(uid)
        avatars = cls.get_avatar_thumbnails(uid)
        socials = cls.get_social_counts(uid)
        past_names = cls.get_past_usernames(uid)
        groups = cls.get_groups(uid)
        roblox_badges = cls.get_roblox_badges(uid)
        created_games_badges = cls.get_created_games_badges(uid)

        desc = details.get("description")
        if not desc:
            desc = I18n.t("no_description")

        return {
            "id": uid,
            "username": details.get("name"),
            "displayName": details.get("displayName"),
            "description": desc,
            "rawDescription": details.get("description"),
            "rawCreated": created_str,
            "isBanned": details.get("isBanned", False),
            "hasVerifiedBadge": details.get("hasVerifiedBadge", False),
            "createdDate": formatted_date,
            "accountAge": age_str,
            "presence": presence,
            "avatarUrl": avatars.get("headshot") or avatars.get("bust"),
            "socials": socials,
            "pastNames": past_names,
            "groups": groups,
            "robloxBadges": roblox_badges,
            "createdGamesBadges": created_games_badges,
            "profileUrl": f"https://www.roblox.com/users/{uid}/profile"
        }
