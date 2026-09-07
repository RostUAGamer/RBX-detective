"""
RBX Detective - Головний застосунок (CustomTkinter GUI)
Зручний та сучасний інтерфейс для аналізу гравців Roblox.
Підтримує локалізацію (Українська, English, Deutsch, 中文),
приєднання до гри та перегляд ігрових досягнень із cookie-авторизацією.
"""
import os
import threading
import webbrowser
from io import BytesIO
import customtkinter as ctk
from PIL import Image
import requests

from roblox_api import RobloxAPI
from i18n import I18n, LANGUAGES


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class RBXDetectiveApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Завантажуємо налаштування мови та cookie
        I18n.load_config()
        RobloxAPI.load_saved_cookie()

        self.title(I18n.t("app_title"))
        self.geometry("1020x760")
        self.minsize(920, 660)

        self.current_avatar_image = None
        self.current_profile_data = None

        self._init_ui()

    def _init_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Верхня панель пошуку + Налаштування
        search_frame = ctk.CTkFrame(self, corner_radius=14, fg_color="#181b22", border_width=1, border_color="#272d38")
        search_frame.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")
        search_frame.grid_columnconfigure(1, weight=1)

        title_lbl = ctk.CTkLabel(
            search_frame,
            text="🔍 RBX Detective",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#38bdf8"
        )
        title_lbl.grid(row=0, column=0, padx=(18, 14), pady=12)

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text=I18n.t("search_placeholder"),
            font=ctk.CTkFont(size=14),
            height=40,
            corner_radius=10,
            border_color="#334155",
            fg_color="#0f172a"
        )
        self.search_entry.grid(row=0, column=1, padx=(0, 10), pady=12, sticky="ew")
        self.search_entry.bind("<Return>", lambda event: self.start_search())

        self.search_btn = ctk.CTkButton(
            search_frame,
            text=I18n.t("search_btn"),
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=110,
            corner_radius=10,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self.start_search
        )
        self.search_btn.grid(row=0, column=2, padx=(0, 10), pady=12)

        self.settings_btn = ctk.CTkButton(
            search_frame,
            text="⚙️",
            font=ctk.CTkFont(size=16),
            height=40,
            width=40,
            corner_radius=10,
            fg_color="#334155",
            hover_color="#475569",
            command=self._open_settings_dialog
        )
        self.settings_btn.grid(row=0, column=3, padx=(0, 16), pady=12)

        # 2. Статус-бар
        self.status_lbl = ctk.CTkLabel(
            self,
            text=I18n.t("status_initial"),
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8"
        )
        self.status_lbl.grid(row=2, column=0, padx=20, pady=(2, 10), sticky="w")

        # 3. Основна область вмісту
        self.main_content = ctk.CTkFrame(self, corner_radius=16, fg_color="#13161c")
        self.main_content.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        self.main_content.grid_columnconfigure(0, weight=1, minsize=300)
        self.main_content.grid_columnconfigure(1, weight=3)
        self.main_content.grid_rowconfigure(0, weight=1)

        self._build_left_profile_panel()
        self._build_right_tabview()

    def _build_left_profile_panel(self):
        self.left_card = ctk.CTkFrame(self.main_content, corner_radius=14, fg_color="#1c212b", border_width=1, border_color="#2b3240")
        self.left_card.grid(row=0, column=0, padx=(14, 8), pady=14, sticky="nsew")
        self.left_card.grid_columnconfigure(0, weight=1)

        # Аватар
        self.avatar_canvas = ctk.CTkLabel(self.left_card, text="", width=140, height=140)
        self.avatar_canvas.grid(row=0, column=0, pady=(16, 8))

        # Нікнейм та Display Name
        self.display_name_lbl = ctk.CTkLabel(
            self.left_card,
            text="—",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#f8fafc"
        )
        self.display_name_lbl.grid(row=1, column=0, padx=12, pady=(0, 2))

        self.username_lbl = ctk.CTkLabel(
            self.left_card,
            text="@—",
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8"
        )
        self.username_lbl.grid(row=2, column=0, padx=12, pady=(0, 8))

        # Бейдж статусу онлайн
        self.presence_badge = ctk.CTkLabel(
            self.left_card,
            text=f"● {I18n.t('offline')}",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#334155",
            text_color="#e2e8f0",
            corner_radius=8,
            padx=12,
            pady=4
        )
        self.presence_badge.grid(row=3, column=0, pady=(0, 8))

        # Інформація про гру
        self.game_info_lbl = ctk.CTkLabel(
            self.left_card,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#a5b4fc",
            wraplength=260
        )
        self.game_info_lbl.grid(row=4, column=0, padx=10, pady=(0, 6))

        # Кнопка приєднання до гри
        self.join_game_btn = ctk.CTkButton(
            self.left_card,
            text=I18n.t("btn_player_not_ingame"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            corner_radius=8,
            state="disabled",
            command=self._join_player_game
        )
        self.join_game_btn.grid(row=5, column=0, padx=20, pady=(4, 6), sticky="ew")

        # Відкрити профіль
        self.open_profile_btn = ctk.CTkButton(
            self.left_card,
            text=I18n.t("btn_open_profile"),
            font=ctk.CTkFont(size=12),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            corner_radius=8,
            command=self._open_roblox_profile
        )
        self.open_profile_btn.grid(row=6, column=0, padx=20, pady=(4, 16), sticky="ew")

    def _build_right_tabview(self):
        self.tabview = ctk.CTkTabview(
            self.main_content,
            corner_radius=14,
            fg_color="#1c212b",
            segmented_button_selected_color="#0284c7",
            segmented_button_selected_hover_color="#0369a1",
            segmented_button_unselected_color="#0f172a"
        )
        self.tabview.grid(row=0, column=1, padx=(8, 14), pady=14, sticky="nsew")

        self.tab_info = self.tabview.add(I18n.t("tab_profile"))
        self.tab_game_badges = self.tabview.add(I18n.t("tab_game_badges"))
        self.tab_groups = self.tabview.add(I18n.t("tab_groups"))
        self.tab_past_names = self.tabview.add(I18n.t("tab_past_names"))
        self.tab_roblox_badges = self.tabview.add(I18n.t("tab_roblox_badges"))

        self._setup_info_tab()
        self._setup_game_badges_tab()
        self._setup_groups_tab()
        self._setup_past_names_tab()
        self._setup_roblox_badges_tab()

    def _setup_info_tab(self):
        self.tab_info.grid_columnconfigure(0, weight=1)
        self.tab_info.grid_columnconfigure(1, weight=1)

        self.stat_cards = {}
        self.stat_title_labels = {}
        fields = [
            ("stat_userid", "0", 0, 0),
            ("stat_verification", "—", 0, 1),
            ("stat_created", "—", 1, 0),
            ("stat_age", "—", 1, 1),
            ("stat_friends", "0", 2, 0),
            ("stat_followers", "0", 2, 1),
        ]

        for key, val, r, c in fields:
            card = ctk.CTkFrame(self.tab_info, corner_radius=10, fg_color="#111620", border_width=1, border_color="#272f3d")
            card.grid(row=r, column=c, padx=6, pady=5, sticky="ew")
            
            lbl_title = ctk.CTkLabel(card, text=I18n.t(key), font=ctk.CTkFont(size=11), text_color="#94a3b8")
            lbl_title.pack(anchor="w", padx=12, pady=(6, 0))
            self.stat_title_labels[key] = lbl_title

            lbl_val = ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=14, weight="bold"), text_color="#38bdf8")
            lbl_val.pack(anchor="w", padx=12, pady=(0, 8))
            self.stat_cards[key] = lbl_val

        desc_frame = ctk.CTkFrame(self.tab_info, corner_radius=10, fg_color="#111620", border_width=1, border_color="#272f3d")
        desc_frame.grid(row=3, column=0, columnspan=2, padx=6, pady=10, sticky="nsew")
        self.tab_info.grid_rowconfigure(3, weight=1)

        self.desc_title = ctk.CTkLabel(desc_frame, text=I18n.t("bio_title"), font=ctk.CTkFont(size=12, weight="bold"), text_color="#cbd5e1")
        self.desc_title.pack(anchor="w", padx=12, pady=(8, 2))

        self.desc_textbox = ctk.CTkTextbox(
            desc_frame,
            wrap="word",
            font=ctk.CTkFont(size=13),
            fg_color="#0b0f17",
            text_color="#e2e8f0",
            corner_radius=8
        )
        self.desc_textbox.pack(fill="both", expand=True, padx=10, pady=(2, 10))

    def _setup_game_badges_tab(self):
        self.game_badges_scroll = ctk.CTkScrollableFrame(self.tab_game_badges, corner_radius=10, fg_color="#111620")
        self.game_badges_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self.game_badges_placeholder = ctk.CTkLabel(
            self.game_badges_scroll,
            text=I18n.t("game_badges_empty"),
            text_color="#64748b",
            justify="center"
        )
        self.game_badges_placeholder.pack(pady=40)

    def _setup_groups_tab(self):
        self.groups_scroll = ctk.CTkScrollableFrame(self.tab_groups, corner_radius=10, fg_color="#111620")
        self.groups_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self.groups_placeholder = ctk.CTkLabel(self.groups_scroll, text=I18n.t("groups_empty"), text_color="#64748b")
        self.groups_placeholder.pack(pady=40)

    def _setup_past_names_tab(self):
        self.past_names_scroll = ctk.CTkScrollableFrame(self.tab_past_names, corner_radius=10, fg_color="#111620")
        self.past_names_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self.past_names_placeholder = ctk.CTkLabel(self.past_names_scroll, text=I18n.t("past_names_empty"), text_color="#64748b")
        self.past_names_placeholder.pack(pady=40)

    def _setup_roblox_badges_tab(self):
        self.roblox_badges_scroll = ctk.CTkScrollableFrame(self.tab_roblox_badges, corner_radius=10, fg_color="#111620")
        self.roblox_badges_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self.roblox_badges_placeholder = ctk.CTkLabel(self.roblox_badges_scroll, text=I18n.t("roblox_badges_empty"), text_color="#64748b")
        self.roblox_badges_placeholder.pack(pady=40)

    def _open_settings_dialog(self):
        """Settings modal dialog with Language Selection and Roblox Cookie tabs."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(I18n.t("settings_title"))
        dialog.geometry("560x420")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)

        settings_tabs = ctk.CTkTabview(
            dialog,
            corner_radius=12,
            segmented_button_selected_color="#0284c7",
            segmented_button_selected_hover_color="#0369a1"
        )
        settings_tabs.pack(fill="both", expand=True, padx=16, pady=16)

        tab_lang = settings_tabs.add(I18n.t("settings_tab_lang"))
        tab_cookie = settings_tabs.add(I18n.t("settings_tab_cookie"))

        # --- Вкладка 1: Мова (Language) ---
        lang_title = ctk.CTkLabel(
            tab_lang,
            text=I18n.t("select_language"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38bdf8"
        )
        lang_title.pack(anchor="w", padx=16, pady=(16, 12))

        lang_options = [f"{name} ({code})" for code, name in LANGUAGES.items()]
        curr_code = I18n.current_lang
        curr_display = f"{LANGUAGES.get(curr_code, 'English')} ({curr_code})"

        lang_combo = ctk.CTkComboBox(
            tab_lang,
            values=lang_options,
            width=280,
            height=38,
            font=ctk.CTkFont(size=14),
            state="readonly"
        )
        lang_combo.set(curr_display)
        lang_combo.pack(anchor="w", padx=16, pady=(0, 20))

        def on_lang_change():
            selected = lang_combo.get()
            # Extract code from parentheses
            code = selected.split("(")[-1].replace(")", "").strip()
            if code in LANGUAGES:
                I18n.set_language(code)
                dialog.destroy()
                self._apply_language_change()

        lang_save_btn = ctk.CTkButton(
            tab_lang,
            text=I18n.t("btn_save"),
            fg_color="#10b981",
            hover_color="#059669",
            width=140,
            command=on_lang_change
        )
        lang_save_btn.pack(anchor="w", padx=16)

        # --- Вкладка 2: Roblox Cookie (.ROBLOSECURITY) ---
        cookie_title = ctk.CTkLabel(
            tab_cookie,
            text=I18n.t("cookie_title"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38bdf8"
        )
        cookie_title.pack(anchor="w", padx=16, pady=(16, 6))

        cookie_desc = ctk.CTkLabel(
            tab_cookie,
            text=I18n.t("cookie_desc"),
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
            justify="left"
        )
        cookie_desc.pack(anchor="w", padx=16, pady=(0, 10))

        cookie_entry = ctk.CTkEntry(
            tab_cookie,
            placeholder_text=I18n.t("cookie_placeholder"),
            width=480,
            show="•"
        )
        cookie_entry.pack(padx=16, pady=10)

        saved = RobloxAPI.load_saved_cookie()
        if saved:
            cookie_entry.insert(0, saved)

        btn_box = ctk.CTkFrame(tab_cookie, fg_color="transparent")
        btn_box.pack(padx=16, pady=15, anchor="w")

        def save_cookie():
            c_val = cookie_entry.get().strip()
            if c_val:
                RobloxAPI.set_cookie(c_val)
                self.status_lbl.configure(text=I18n.t("status_cookie_saved"), text_color="#10b981")
            dialog.destroy()

        def clear_cookie():
            RobloxAPI.clear_cookie()
            cookie_entry.delete(0, "end")
            self.status_lbl.configure(text=I18n.t("status_cookie_cleared"), text_color="#94a3b8")
            dialog.destroy()

        save_btn = ctk.CTkButton(btn_box, text=I18n.t("btn_save"), fg_color="#10b981", hover_color="#059669", width=120, command=save_cookie)
        save_btn.pack(side="left", padx=(0, 10))

        clear_btn = ctk.CTkButton(btn_box, text=I18n.t("btn_clear"), fg_color="#ef4444", hover_color="#dc2626", width=120, command=clear_cookie)
        clear_btn.pack(side="left")

    def _apply_language_change(self):
        """Refreshes all static text and re-renders current profile in the newly selected language."""
        self.title(I18n.t("app_title"))
        self.search_entry.configure(placeholder_text=I18n.t("search_placeholder"))
        self.search_btn.configure(text=I18n.t("search_btn"))
        self.open_profile_btn.configure(text=I18n.t("btn_open_profile"))
        self.desc_title.configure(text=I18n.t("bio_title"))

        for key, lbl in self.stat_title_labels.items():
            lbl.configure(text=I18n.t(key))

        if self.current_profile_data:
            # Re-fetch or update existing profile UI
            self._update_ui_with_profile(self.current_profile_data, self.current_avatar_image)
        else:
            self.status_lbl.configure(text=I18n.t("status_initial"))

    def start_search(self):
        query = self.search_entry.get().strip()
        if not query:
            self.status_lbl.configure(text=I18n.t("status_empty_query"), text_color="#f59e0b")
            return

        self.status_lbl.configure(text=I18n.t("status_searching", query=query), text_color="#38bdf8")
        self.search_btn.configure(state="disabled")

        thread = threading.Thread(target=self._search_worker, args=(query,), daemon=True)
        thread.start()

    def _search_worker(self, query: str):
        try:
            profile = RobloxAPI.fetch_full_profile(query)
            
            avatar_image = None
            if profile.get("avatarUrl"):
                try:
                    img_resp = requests.get(profile["avatarUrl"], timeout=6)
                    if img_resp.status_code == 200:
                        pil_img = Image.open(BytesIO(img_resp.content)).convert("RGBA")
                        avatar_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(130, 130))
                except Exception:
                    pass

            self.after(0, self._update_ui_with_profile, profile, avatar_image)
        except Exception as e:
            self.after(0, self._show_error, str(e))

    def _update_ui_with_profile(self, profile: dict, avatar_img):
        self.current_profile_data = profile
        self.search_btn.configure(state="normal")
        self.status_lbl.configure(text=I18n.t("status_success", username=profile["username"]), text_color="#10b981")

        self.display_name_lbl.configure(text=profile["displayName"])
        self.username_lbl.configure(text=f"@{profile['username']}")

        if avatar_img:
            self.avatar_canvas.configure(image=avatar_img, text="")
            self.current_avatar_image = avatar_img
        else:
            self.avatar_canvas.configure(image="", text="👤")

        # Онлайн статус та кнопка Join Game
        pres = profile["presence"]
        self.presence_badge.configure(text=f"● {pres['status']}", fg_color=pres["color"])

        if pres["presenceType"] == 2:  # In-Game
            game_title = pres.get("gameName") or "Roblox Experience"
            self.game_info_lbl.configure(text=I18n.t("in_game_label", game_title=game_title))
            self.join_game_btn.configure(state="normal", text=I18n.t("btn_join_game"))
        else:
            self.game_info_lbl.configure(text="")
            self.join_game_btn.configure(state="disabled", text=I18n.t("btn_player_not_ingame"))

        # Статистичні поля
        self.stat_cards["stat_userid"].configure(text=str(profile["id"]))
        self.stat_cards["stat_verification"].configure(
            text=I18n.t("verified_yes") if profile["hasVerifiedBadge"] else I18n.t("verified_no"),
            text_color="#38bdf8" if profile["hasVerifiedBadge"] else "#94a3b8"
        )
        self.stat_cards["stat_created"].configure(text=profile["createdDate"])
        self.stat_cards["stat_age"].configure(text=profile["accountAge"])
        self.stat_cards["stat_friends"].configure(text=f"{profile['socials']['friends']:,}")
        self.stat_cards["stat_followers"].configure(text=f"{profile['socials']['followers']:,}")

        # Опис
        self.desc_textbox.delete("1.0", "end")
        desc_text = profile.get("rawDescription") or I18n.t("no_description")
        self.desc_textbox.insert("1.0", desc_text)

        # Рендер вкладок
        self._render_game_badges(profile["gameBadgesResult"])
        self._render_groups(profile["groups"])
        self._render_past_names(profile["pastNames"])
        self._render_roblox_badges(profile["robloxBadges"])

    def _join_player_game(self):
        if not self.current_profile_data:
            return

        pres = self.current_profile_data.get("presence", {})
        place_id = pres.get("placeId")
        game_id = pres.get("gameId")

        if place_id:
            if game_id:
                protocol_url = f"roblox://experiences/start?placeId={place_id}&gameInstanceId={game_id}"
            else:
                protocol_url = f"roblox://placeId={place_id}"

            try:
                os.startfile(protocol_url)
                self.status_lbl.configure(text=I18n.t("status_launching_client", place_id=place_id), text_color="#10b981")
            except Exception:
                web_url = f"https://www.roblox.com/games/{place_id}"
                webbrowser.open(web_url)
                self.status_lbl.configure(text=I18n.t("status_opened_browser"), text_color="#38bdf8")
        else:
            self.status_lbl.configure(
                text=I18n.t("status_privacy_restricted"),
                text_color="#f59e0b"
            )

    def _render_game_badges(self, result: dict):
        for widget in self.game_badges_scroll.winfo_children():
            widget.destroy()

        if not result.get("success"):
            err_box = ctk.CTkFrame(self.game_badges_scroll, corner_radius=10, fg_color="#261b1b", border_width=1, border_color="#7f1d1d")
            err_box.pack(fill="x", padx=10, pady=20)

            ctk.CTkLabel(
                err_box,
                text=I18n.t("game_badges_auth_title"),
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#f87171"
            ).pack(anchor="w", padx=14, pady=(12, 4))

            error_msg = result.get("error", "")
            ctk.CTkLabel(
                err_box,
                text=I18n.t("game_badges_auth_desc", error=error_msg),
                font=ctk.CTkFont(size=12),
                text_color="#cbd5e1",
                justify="left"
            ).pack(anchor="w", padx=14, pady=(0, 12))
            return

        badges = result.get("badges", [])
        if not badges:
            lbl = ctk.CTkLabel(self.game_badges_scroll, text=I18n.t("game_badges_empty"), text_color="#64748b")
            lbl.pack(pady=30)
            return

        header = ctk.CTkLabel(
            self.game_badges_scroll,
            text=I18n.t("game_badges_header", count=len(badges)),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38bdf8"
        )
        header.pack(anchor="w", padx=10, pady=(6, 8))

        for b in badges:
            card = ctk.CTkFrame(self.game_badges_scroll, corner_radius=8, fg_color="#1e293b", border_width=1, border_color="#334155")
            card.pack(fill="x", padx=6, pady=4)
            card.grid_columnconfigure(0, weight=1)

            b_name = ctk.CTkLabel(card, text=f"🏆 {b.get('name')}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8", anchor="w")
            b_name.grid(row=0, column=0, padx=12, pady=(6, 2), sticky="w")

            awarder = b.get("awarder", "Roblox")
            desc = b.get("description") or ""
            info_text = I18n.t("game_creator_prefix", awarder=awarder, desc=desc)

            b_desc = ctk.CTkLabel(card, text=info_text, font=ctk.CTkFont(size=11), text_color="#94a3b8", wraplength=560, justify="left", anchor="w")
            b_desc.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="w")

    def _render_groups(self, groups: list):
        for widget in self.groups_scroll.winfo_children():
            widget.destroy()

        if not groups:
            lbl = ctk.CTkLabel(self.groups_scroll, text=I18n.t("groups_empty"), text_color="#64748b")
            lbl.pack(pady=30)
            return

        header = ctk.CTkLabel(self.groups_scroll, text=I18n.t("groups_header", count=len(groups)), font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8")
        header.pack(anchor="w", padx=10, pady=(6, 8))

        for g in groups:
            card = ctk.CTkFrame(self.groups_scroll, corner_radius=8, fg_color="#1e293b", border_width=1, border_color="#334155")
            card.pack(fill="x", padx=6, pady=4)
            card.grid_columnconfigure(0, weight=1)

            name_lbl = ctk.CTkLabel(card, text=g["name"], font=ctk.CTkFont(size=13, weight="bold"), text_color="#f8fafc", anchor="w")
            name_lbl.grid(row=0, column=0, padx=12, pady=(6, 2), sticky="w")

            role_str = I18n.t("group_role_rank", role=g["role"], rank=g["rank"], members=g["memberCount"])
            role_lbl = ctk.CTkLabel(card, text=role_str, font=ctk.CTkFont(size=11), text_color="#94a3b8", anchor="w")
            role_lbl.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="w")

    def _render_past_names(self, past_names: list):
        for widget in self.past_names_scroll.winfo_children():
            widget.destroy()

        if not past_names:
            lbl = ctk.CTkLabel(self.past_names_scroll, text=I18n.t("past_names_empty"), text_color="#64748b")
            lbl.pack(pady=30)
            return

        header = ctk.CTkLabel(self.past_names_scroll, text=I18n.t("past_names_header", count=len(past_names)), font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8")
        header.pack(anchor="w", padx=10, pady=(6, 8))

        for idx, name in enumerate(past_names, 1):
            row_frame = ctk.CTkFrame(self.past_names_scroll, corner_radius=8, fg_color="#1e293b")
            row_frame.pack(fill="x", padx=6, pady=3)

            lbl = ctk.CTkLabel(row_frame, text=f"#{idx}  {name}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#e2e8f0")
            lbl.pack(anchor="w", padx=12, pady=6)

    def _render_roblox_badges(self, badges: list):
        for widget in self.roblox_badges_scroll.winfo_children():
            widget.destroy()

        if not badges:
            lbl = ctk.CTkLabel(self.roblox_badges_scroll, text=I18n.t("roblox_badges_empty"), text_color="#64748b")
            lbl.pack(pady=30)
            return

        header = ctk.CTkLabel(self.roblox_badges_scroll, text=I18n.t("roblox_badges_header", count=len(badges)), font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8")
        header.pack(anchor="w", padx=10, pady=(6, 8))

        for b in badges:
            card = ctk.CTkFrame(self.roblox_badges_scroll, corner_radius=8, fg_color="#1e293b", border_width=1, border_color="#334155")
            card.pack(fill="x", padx=6, pady=4)
            card.grid_columnconfigure(0, weight=1)

            b_name = ctk.CTkLabel(card, text=f"🏅 {b.get('name')}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#f59e0b", anchor="w")
            b_name.grid(row=0, column=0, padx=12, pady=(6, 2), sticky="w")

            b_desc = ctk.CTkLabel(card, text=b.get("description", ""), font=ctk.CTkFont(size=11), text_color="#94a3b8", wraplength=550, justify="left", anchor="w")
            b_desc.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="w")

    def _show_error(self, error_message: str):
        self.search_btn.configure(state="normal")
        self.status_lbl.configure(text=I18n.t("status_error", error=error_message), text_color="#ef4444")

    def _open_roblox_profile(self):
        if self.current_profile_data and self.current_profile_data.get("profileUrl"):
            webbrowser.open(self.current_profile_data["profileUrl"])


if __name__ == "__main__":
    app = RBXDetectiveApp()
    app.mainloop()
