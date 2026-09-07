"""
Roblox API Service for RBX Detective.
Retrieves comprehensive player information from official Roblox APIs.
Supports custom Roblox Cookie (.ROBLOSECURITY) for game badges & private queries.
"""
import os
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List


class RobloxAPI:
    COOKIE_FILE = "roblox_cookie.txt"
    SESSION = requests.Session()
    SESSION.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    })

    @classmethod
    def load_saved_cookie(cls) -> Optional[str]:
        """Loads saved .ROBLOSECURITY cookie if available."""
        if os.path.exists(cls.COOKIE_FILE):
            try:
                with open(cls.COOKIE_FILE, "r", encoding="utf-8") as f:
                    cookie = f.read().strip()
                    if cookie:
                        cls.set_cookie(cookie)
                        return cookie
            except Exception:
                pass
        return None

    @classmethod
    def set_cookie(cls, cookie: str):
        """Sets the .ROBLOSECURITY cookie in the session and saves to file."""
        clean_cookie = cookie.strip()
        if clean_cookie.startswith(".ROBLOSECURITY="):
            clean_cookie = clean_cookie.replace(".ROBLOSECURITY=", "", 1).strip()
        
        cls.SESSION.cookies.set(".ROBLOSECURITY", clean_cookie, domain=".roblox.com")
        try:
            with open(cls.COOKIE_FILE, "w", encoding="utf-8") as f:
                f.write(clean_cookie)
        except Exception:
            pass

    @classmethod
    def clear_cookie(cls):
        """Removes the stored cookie."""
        cls.SESSION.cookies.clear()
        if os.path.exists(cls.COOKIE_FILE):
            try:
                os.remove(cls.COOKIE_FILE)
            except Exception:
                pass

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
                    # 0: Offline, 1: Online, 2: InGame, 3: InStudio
                    type_map = {
                        0: ("Offline", "#80848e"),
                        1: ("Online (Website)", "#23a55a"),
                        2: ("In-Game", "#5865f2"),
                        3: ("In Studio", "#f0b232")
                    }
                    ptype = p.get("userPresenceType", 0)
                    status_str, color = type_map.get(ptype, ("Unknown", "#80848e"))
                    
                    place_id = p.get("placeId")
                    game_id = p.get("gameId") # Job ID / Server instance
                    game_name = p.get("lastLocation", "")

                    # If in game and we have a placeId, get rich game information
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
            "status": "Offline",
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
        """Fetch official Roblox badges (Veteran, Homestead, Administrator, etc.)."""
        url = f"https://accountinformation.roblox.com/v1/users/{user_id}/roblox-badges"
        try:
            resp = cls.SESSION.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []

    @classmethod
    def get_game_badges(cls, user_id: int, limit: int = 50) -> Dict[str, Any]:
        """
        Fetches user badges won from all Roblox games/experiences.
        Requires authentication cookie (.ROBLOSECURITY) according to Roblox Badges API v1.
        Returns {'success': bool, 'badges': list, 'needs_auth': bool, 'error': str}
        """
        url = f"https://badges.roblox.com/v1/users/{user_id}/badges?limit={limit}&sortOrder=Desc"
        try:
            resp = cls.SESSION.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                formatted_badges = []
                for b in data:
                    formatted_badges.append({
                        "id": b.get("id"),
                        "name": b.get("name"),
                        "description": b.get("description", ""),
                        "awarder": b.get("awarder", {}).get("name", "Гра Roblox"),
                        "created": b.get("created")
                    })
                return {"success": True, "badges": formatted_badges, "needs_auth": False, "error": None}
            elif resp.status_code == 401:
                return {
                    "success": False,
                    "badges": [],
                    "needs_auth": True,
                    "error": "Roblox API вимагає авторизації (.ROBLOSECURITY cookie) для перегляду бейджів з ігор."
                }
            elif resp.status_code == 403:
                return {
                    "success": False,
                    "badges": [],
                    "needs_auth": False,
                    "error": "Інвентар або бейджі цього гравця приховані налаштуваннями приватності."
                }
            else:
                return {
                    "success": False,
                    "badges": [],
                    "needs_auth": False,
                    "error": f"Сервер повернув код {resp.status_code}."
                }
        except Exception as e:
            return {"success": False, "badges": [], "needs_auth": False, "error": str(e)}

    @classmethod
    def fetch_full_profile(cls, query: str) -> Dict[str, Any]:
        """
        Coordinates full data fetching.
        query can be a numeric user_id or a username string.
        """
        # Ensure saved cookie is active
        cls.load_saved_cookie()

        user_basic = None
        if query.isdigit():
            user_basic = {"id": int(query)}
        else:
            user_basic = cls.get_user_by_name(query)
            if not user_basic:
                raise ValueError(f"Користувача '{query}' не знайдено на Roblox.")

        uid = user_basic["id"]
        details = cls.get_user_details(uid)
        if not details:
            raise ValueError(f"Не вдалося завантажити інформацію про гравця з ID {uid}.")

        # Parse date and age
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
                    age_str = f"{years} р. {remaining_days} дн. тому"
                else:
                    age_str = f"{diff.days} дн. тому"
            except Exception:
                pass

        presence = cls.get_presence(uid)
        avatars = cls.get_avatar_thumbnails(uid)
        socials = cls.get_social_counts(uid)
        past_names = cls.get_past_usernames(uid)
        groups = cls.get_groups(uid)
        roblox_badges = cls.get_roblox_badges(uid)
        game_badges_result = cls.get_game_badges(uid)

        return {
            "id": uid,
            "username": details.get("name"),
            "displayName": details.get("displayName"),
            "description": details.get("description") or "(Опис відсутній)",
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
            "gameBadgesResult": game_badges_result,
            "profileUrl": f"https://www.roblox.com/users/{uid}/profile"
        }
