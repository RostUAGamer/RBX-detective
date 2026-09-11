"""
RBX Detective - Головний застосунок (CustomTkinter GUI)
- 100% публічні відкриті API Roblox
- Красива фірмова іконка вікна та панелі завдань Windows (Taskbar icon)
- Приємні плавні переходи (Smooth transitions) між усіма вкладками
- Приємний аудіо-зворотний зв'язок (Sound feedback) при натисканні кнопок
- Налаштування мови та повзунок регулювання гучності звуку
"""
import os
import ctypes
import threading
import webbrowser
from io import BytesIO
import customtkinter as ctk
from PIL import Image
import requests

from roblox_api import RobloxAPI
from i18n import I18n, LANGUAGES
from sound_manager import SoundManager


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Встановлюємо AppUserModelID для Windows, щоб панель завдань показувала саме нашу іконку програми
try:
    myappid = 'roblox.detective.app.v1.4'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass


class RBXDetectiveApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Завантажуємо налаштування мови та звуку
        lang, vol = I18n.load_config()
        SoundManager.set_volume(vol)

        self.title(I18n.t("app_title"))
        self.geometry("1020x760")
        self.minsize(920, 660)

        # Встановлюємо гарну іконку для вікна та панелі завдань
        self._setup_window_icon()

        self.current_avatar_image = None
        self.current_profile_data = None

        # Керування плавними переходами між вкладками
        self.is_animating_tab = False

        self._init_ui()

    def _setup_window_icon(self):
        """Sets window and taskbar icons using icon.ico and icon.png."""
        try:
            if os.path.exists("icon.ico"):
                self.iconbitmap("icon.ico")
            elif os.path.exists("icon.png"):
                icon_img = Image.open("icon.png")
                self.wm_iconphoto(True, ImageTk.PhotoImage(icon_img))
        except Exception:
            pass

    def _play_click(self):
        """Helper to trigger soft button sound feedback."""
        SoundManager.play_click()

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
        self.search_entry.bind("<Return>", lambda event: (self._play_click(), self.start_search()))

        self.search_btn = ctk.CTkButton(
            search_frame,
            text=I18n.t("search_btn"),
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=110,
            corner_radius=10,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self._on_search_clicked
        )
        self.search_btn.grid(row=0, column=2, padx=(0, 10), pady=12)

        self.settings_btn = ctk.CTkButton(
            search_frame,
            text="⚙️",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40,
            width=45,
            corner_radius=10,
            fg_color="#334155",
            hover_color="#475569",
            command=self._on_settings_clicked
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

    def _on_search_clicked(self):
        self._play_click()
        self.start_search()

    def _on_settings_clicked(self):
        self._play_click()
        self._open_settings_dialog()

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
            command=self._on_join_game_clicked
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
            command=self._on_open_profile_clicked
        )
        self.open_profile_btn.grid(row=6, column=0, padx=20, pady=(4, 8), sticky="ew")

        # --- Кнопка: Випадковий гравець ---
        self.random_player_btn = ctk.CTkButton(
            self.left_card,
            text=I18n.t("btn_random_player"),
            font=ctk.CTkFont(size=12),
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            corner_radius=8,
            command=self._on_random_player_clicked
        )
        self.random_player_btn.grid(row=7, column=0, padx=20, pady=(0, 6), sticky="ew")

        # --- Кнопка: Знайти гравця з Joinable ---
        self.joinable_player_btn = ctk.CTkButton(
            self.left_card,
            text=I18n.t("btn_random_joinable"),
            font=ctk.CTkFont(size=12),
            fg_color="#059669",
            hover_color="#047857",
            corner_radius=8,
            command=self._on_joinable_player_clicked
        )
        self.joinable_player_btn.grid(row=8, column=0, padx=20, pady=(0, 16), sticky="ew")

    def _on_join_game_clicked(self):
        self._play_click()
        self._join_player_game()

    def _on_open_profile_clicked(self):
        self._play_click()
        self._open_roblox_profile()

    def _on_random_player_clicked(self):
        self._play_click()
        self.status_lbl.configure(text=I18n.t("status_searching_random"), text_color="#a78bfa")
        self.random_player_btn.configure(state="disabled")
        self.joinable_player_btn.configure(state="disabled")
        self.search_btn.configure(state="disabled")
        threading.Thread(target=self._random_player_worker, daemon=True).start()

    def _on_joinable_player_clicked(self):
        self._play_click()
        self.status_lbl.configure(text=I18n.t("status_searching_joinable"), text_color="#34d399")
        self.random_player_btn.configure(state="disabled")
        self.joinable_player_btn.configure(state="disabled")
        self.search_btn.configure(state="disabled")
        threading.Thread(target=self._joinable_player_worker, daemon=True).start()

    def _random_player_worker(self):
        try:
            user_data = RobloxAPI.find_random_player()
            if user_data:
                username = user_data.get("name", str(user_data.get("id", "")))
                self.after(0, lambda: self._load_player_by_id(user_data["id"]))
            else:
                self.after(0, self._re_enable_buttons)
        except Exception as e:
            self.after(0, self._re_enable_buttons)

    def _joinable_player_worker(self):
        try:
            profile = RobloxAPI.find_joinable_player(max_candidates=60)
            if profile:
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
                self.after(0, self._re_enable_buttons)
            else:
                self.after(0, lambda: self.status_lbl.configure(
                    text=I18n.t("status_no_joinable"), text_color="#f59e0b"
                ))
                self.after(0, self._re_enable_buttons)
        except Exception as e:
            self.after(0, self._re_enable_buttons)

    def _load_player_by_id(self, user_id: int):
        """Load full profile for a given user ID (used after random player search)."""
        self.search_btn.configure(state="disabled")
        threading.Thread(
            target=self._search_worker_by_id,
            args=(user_id,),
            daemon=True
        ).start()

    def _search_worker_by_id(self, user_id: int):
        try:
            profile = RobloxAPI.fetch_full_profile(str(user_id))
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
            self.after(0, self._re_enable_buttons)
        except Exception as e:
            self.after(0, self._show_error, str(e))
            self.after(0, self._re_enable_buttons)

    def _re_enable_buttons(self):
        """Re-enables all action buttons after an async operation completes."""
        self.search_btn.configure(state="normal")
        self.random_player_btn.configure(state="normal")
        self.joinable_player_btn.configure(state="normal")

    def _build_right_tabview(self):
        self.tabview = ctk.CTkTabview(
            self.main_content,
            corner_radius=14,
            fg_color="#1c212b",
            segmented_button_selected_color="#0284c7",
            segmented_button_selected_hover_color="#0369a1",
            segmented_button_unselected_color="#0f172a",
            command=self._on_tab_switched
        )
        self.tabview.grid(row=0, column=1, padx=(8, 14), pady=14, sticky="nsew")

        self.TAB_KEYS = ["tab_profile", "tab_game_badges", "tab_groups", "tab_past_names", "tab_roblox_badges", "tab_compare"]

        self.tab_info = self.tabview.add("tab_profile")
        self.tab_game_badges = self.tabview.add("tab_game_badges")
        self.tab_groups = self.tabview.add("tab_groups")
        self.tab_past_names = self.tabview.add("tab_past_names")
        self.tab_roblox_badges = self.tabview.add("tab_roblox_badges")
        self.tab_compare = self.tabview.add("tab_compare")

        self.tab_frames = {
            "tab_profile": self.tab_info,
            "tab_game_badges": self.tab_game_badges,
            "tab_groups": self.tab_groups,
            "tab_past_names": self.tab_past_names,
            "tab_roblox_badges": self.tab_roblox_badges,
            "tab_compare": self.tab_compare
        }

        self._refresh_tab_headers()

        self._setup_info_tab()
        self._setup_game_badges_tab()
        self._setup_groups_tab()
        self._setup_past_names_tab()
        self._setup_roblox_badges_tab()
        self._setup_compare_tab()

    def _on_tab_switched(self):
        """Triggered on tab change: plays soft click and applies smooth transition animation."""
        self._play_click()
        current_tab_key = self.tabview.get()
        target_tab = self.tab_frames.get(current_tab_key)
        if target_tab and not self.is_animating_tab:
            self._animate_tab_fade_in(target_tab)

    def _animate_tab_fade_in(self, target_frame):
        """Smooth quick slide/fade-in effect for tab content."""
        self.is_animating_tab = True
        
        # Micro animation step: slightly fade colors from background to active
        colors = ["#14171f", "#171a24", "#1a1e28", "#1c212b"]
        
        def _step(idx):
            if idx < len(colors):
                try:
                    target_frame.configure(fg_color=colors[idx])
                except Exception:
                    pass
                self.after(16, _step, idx + 1)
            else:
                try:
                    target_frame.configure(fg_color="#1c212b")
                except Exception:
                    pass
                self.is_animating_tab = False

        _step(0)

    def _refresh_tab_headers(self):
        """Updates text on the tab buttons according to current language."""
        if hasattr(self.tabview, "_segmented_button"):
            for key in self.TAB_KEYS:
                if key in self.tabview._segmented_button._buttons_dict:
                    btn = self.tabview._segmented_button._buttons_dict[key]
                    btn.configure(text=I18n.t(key))

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

    def _setup_compare_tab(self):
        """Build the side-by-side account comparison tab."""
        self.tab_compare.grid_columnconfigure(0, weight=1)
        self.tab_compare.grid_rowconfigure(1, weight=1)

        # ── Search bar ───────────────────────────────────────────────────────
        search_row = ctk.CTkFrame(self.tab_compare, fg_color="#0f172a", corner_radius=10,
                                  border_width=1, border_color="#272f3d")
        search_row.grid(row=0, column=0, padx=6, pady=(8, 4), sticky="ew")
        search_row.grid_columnconfigure(0, weight=1)
        search_row.grid_columnconfigure(1, weight=1)

        self.cmp_entry1 = ctk.CTkEntry(
            search_row, placeholder_text=I18n.t("cmp_player1_placeholder"),
            font=ctk.CTkFont(size=13), height=36, corner_radius=8,
            border_color="#334155", fg_color="#0b0f17"
        )
        self.cmp_entry1.grid(row=0, column=0, padx=(10, 4), pady=8, sticky="ew")
        self.cmp_entry1.bind("<Return>", lambda e: self._on_compare_clicked())

        self.cmp_entry2 = ctk.CTkEntry(
            search_row, placeholder_text=I18n.t("cmp_player2_placeholder"),
            font=ctk.CTkFont(size=13), height=36, corner_radius=8,
            border_color="#334155", fg_color="#0b0f17"
        )
        self.cmp_entry2.grid(row=0, column=1, padx=(4, 4), pady=8, sticky="ew")
        self.cmp_entry2.bind("<Return>", lambda e: self._on_compare_clicked())

        self.cmp_btn = ctk.CTkButton(
            search_row, text=I18n.t("cmp_btn_compare"),
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36, width=110, corner_radius=8,
            fg_color="#0284c7", hover_color="#0369a1",
            command=self._on_compare_clicked
        )
        self.cmp_btn.grid(row=0, column=2, padx=(4, 6), pady=8)

        self.cmp_export_btn = ctk.CTkButton(
            search_row, text=I18n.t("cmp_btn_export"),
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36, width=90, corner_radius=8,
            fg_color="#7c3aed", hover_color="#6d28d9",
            state="disabled",
            command=self._on_compare_export_clicked
        )
        self.cmp_export_btn.grid(row=0, column=3, padx=(0, 10), pady=8)

        # ── Results area ────────────────────────────────────────────────────
        self.cmp_result_frame = ctk.CTkScrollableFrame(
            self.tab_compare, corner_radius=10, fg_color="#111620"
        )
        self.cmp_result_frame.grid(row=1, column=0, padx=6, pady=(4, 6), sticky="nsew")
        self.cmp_result_frame.grid_columnconfigure(0, weight=1)
        self.cmp_result_frame.grid_columnconfigure(1, weight=1)

        self.cmp_status_lbl = ctk.CTkLabel(
            self.cmp_result_frame,
            text=I18n.t("cmp_hint"),
            text_color="#64748b",
            font=ctk.CTkFont(size=13),
            justify="center"
        )
        self.cmp_status_lbl.grid(row=0, column=0, columnspan=2, pady=40)

        # Store compare results for export
        self._cmp_profiles = None

    def _on_compare_clicked(self):
        self._play_click()
        n1 = self.cmp_entry1.get().strip()
        n2 = self.cmp_entry2.get().strip()
        if not n1 or not n2:
            self.cmp_status_lbl.configure(text=I18n.t("cmp_error_empty"), text_color="#f59e0b")
            return
        if n1.lower() == n2.lower():
            self.cmp_status_lbl.configure(text=I18n.t("cmp_error_same"), text_color="#f59e0b")
            return

        self._clear_compare_results()
        self.cmp_status_lbl.configure(text=I18n.t("cmp_searching", p1=n1, p2=n2), text_color="#38bdf8")
        self.cmp_status_lbl.grid(row=0, column=0, columnspan=2, pady=40)
        self.cmp_btn.configure(state="disabled")
        self.cmp_export_btn.configure(state="disabled")

        threading.Thread(target=self._compare_worker, args=(n1, n2), daemon=True).start()

    def _clear_compare_results(self):
        for w in self.cmp_result_frame.winfo_children():
            w.destroy()
        self.cmp_status_lbl = ctk.CTkLabel(
            self.cmp_result_frame, text="", text_color="#64748b",
            font=ctk.CTkFont(size=13), justify="center"
        )
        self.cmp_status_lbl.grid(row=0, column=0, columnspan=2, pady=40)
        self._cmp_profiles = None

    def _compare_worker(self, name1: str, name2: str):
        errors = []
        p1, p2 = None, None

        try:
            p1 = RobloxAPI.fetch_full_profile(name1)
        except Exception as e:
            errors.append(f"{name1}: {e}")

        try:
            p2 = RobloxAPI.fetch_full_profile(name2)
        except Exception as e:
            errors.append(f"{name2}: {e}")

        # Fetch avatars
        av1, av2 = None, None
        if p1 and p1.get("avatarUrl"):
            try:
                r = requests.get(p1["avatarUrl"], timeout=6)
                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content)).convert("RGBA")
                    av1 = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
            except Exception:
                pass
        if p2 and p2.get("avatarUrl"):
            try:
                r = requests.get(p2["avatarUrl"], timeout=6)
                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content)).convert("RGBA")
                    av2 = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
            except Exception:
                pass

        self.after(0, self._render_compare_results, p1, p2, av1, av2, errors)

    def _render_compare_results(self, p1, p2, av1, av2, errors):
        self.cmp_btn.configure(state="normal")
        self._clear_compare_results()

        if errors and (p1 is None or p2 is None):
            self.cmp_status_lbl.configure(
                text=I18n.t("cmp_error_load") + "\n" + "\n".join(errors),
                text_color="#ef4444"
            )
            return

        self._cmp_profiles = (p1, p2)
        self.cmp_export_btn.configure(state="normal")

        # ── Avatar + Name cards ────────────────────────────────────────────
        def make_player_card(parent, profile, avatar_img, col):
            card = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e293b",
                                border_width=1, border_color="#334155")
            card.grid(row=1, column=col, padx=(8 if col == 0 else 4, 4 if col == 0 else 8),
                      pady=6, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)

            av_lbl = ctk.CTkLabel(card, text="" if avatar_img else "👤", image=avatar_img,
                                  width=100, height=100)
            av_lbl.grid(row=0, column=0, pady=(14, 6))

            ctk.CTkLabel(
                card, text=profile["displayName"],
                font=ctk.CTkFont(size=15, weight="bold"), text_color="#f8fafc"
            ).grid(row=1, column=0, padx=10)

            ctk.CTkLabel(
                card, text=f"@{profile['username']}",
                font=ctk.CTkFont(size=12), text_color="#94a3b8"
            ).grid(row=2, column=0, padx=10, pady=(0, 10))

            return card

        make_player_card(self.cmp_result_frame, p1, av1, 0)
        make_player_card(self.cmp_result_frame, p2, av2, 1)

        # ── VS divider ────────────────────────────────────────────────────
        vs_lbl = ctk.CTkLabel(
            self.cmp_result_frame, text="⚔️ VS",
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#f59e0b"
        )
        vs_lbl.grid(row=1, column=0, columnspan=2, pady=4)

        # ── Comparison stats ───────────────────────────────────────────────
        def parse_date(profile):
            try:
                from datetime import datetime
                return datetime.fromisoformat(
                    profile.get("rawCreated", "").replace("Z", "+00:00")
                )
            except Exception:
                return None

        dt1, dt2 = parse_date(p1), parse_date(p2)
        friends1 = p1["socials"].get("friends", 0)
        friends2 = p2["socials"].get("friends", 0)
        followers1 = p1["socials"].get("followers", 0)
        followers2 = p2["socials"].get("followers", 0)

        # Determine winners (lower = older account = wins age; higher = wins social)
        w_age = 0 if (dt1 and dt2 and dt1 < dt2) else (1 if (dt1 and dt2 and dt2 < dt1) else -1)
        w_friends = 0 if friends1 > friends2 else (1 if friends2 > friends1 else -1)
        w_followers = 0 if followers1 > followers2 else (1 if followers2 > followers1 else -1)

        WIN_COLOR = "#10b981"
        LOSE_COLOR = "#64748b"
        DRAW_COLOR = "#f59e0b"

        def stat_row(parent, row_idx, label, val1, val2, winner_idx):
            """Renders a comparison row with colored winner highlight."""
            row_frame = ctk.CTkFrame(parent, fg_color="transparent")
            row_frame.grid(row=row_idx, column=0, columnspan=2, padx=8, pady=2, sticky="ew")
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)

            color1 = WIN_COLOR if winner_idx == 0 else (DRAW_COLOR if winner_idx == -1 else LOSE_COLOR)
            color2 = WIN_COLOR if winner_idx == 1 else (DRAW_COLOR if winner_idx == -1 else LOSE_COLOR)

            ctk.CTkLabel(row_frame, text=str(val1), font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=color1, anchor="e").grid(row=0, column=0, sticky="e")
            ctk.CTkLabel(row_frame, text=f"  {label}  ",
                         font=ctk.CTkFont(size=11), text_color="#475569").grid(row=0, column=1)
            ctk.CTkLabel(row_frame, text=str(val2), font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=color2, anchor="w").grid(row=0, column=2, sticky="w")

        row_start = 2

        # Section header
        stats_header = ctk.CTkLabel(
            self.cmp_result_frame,
            text=I18n.t("cmp_stats_title"),
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8"
        )
        stats_header.grid(row=row_start, column=0, columnspan=2, pady=(10, 4))
        row_start += 1

        stat_row(self.cmp_result_frame, row_start,
                 I18n.t("cmp_stat_created"),
                 p1["createdDate"], p2["createdDate"], w_age)
        row_start += 1

        stat_row(self.cmp_result_frame, row_start,
                 I18n.t("cmp_stat_age"),
                 p1["accountAge"], p2["accountAge"], w_age)
        row_start += 1

        stat_row(self.cmp_result_frame, row_start,
                 I18n.t("cmp_stat_friends"),
                 f"{friends1:,}", f"{friends2:,}", w_friends)
        row_start += 1

        stat_row(self.cmp_result_frame, row_start,
                 I18n.t("cmp_stat_followers"),
                 f"{followers1:,}", f"{followers2:,}", w_followers)
        row_start += 1

        stat_row(self.cmp_result_frame, row_start,
                 I18n.t("cmp_stat_verified"),
                 I18n.t("verified_yes") if p1["hasVerifiedBadge"] else I18n.t("verified_no"),
                 I18n.t("verified_yes") if p2["hasVerifiedBadge"] else I18n.t("verified_no"),
                 0 if (p1["hasVerifiedBadge"] and not p2["hasVerifiedBadge"]) else
                 (1 if (p2["hasVerifiedBadge"] and not p1["hasVerifiedBadge"]) else -1))
        row_start += 1

        # ── Common groups ──────────────────────────────────────────────────
        groups1_ids = {g["id"] for g in p1.get("groups", [])}
        groups2_ids = {g["id"] for g in p2.get("groups", [])}
        common_ids = groups1_ids & groups2_ids
        common_groups = [g for g in p1.get("groups", []) if g["id"] in common_ids]

        sep = ctk.CTkFrame(self.cmp_result_frame, height=1, fg_color="#272f3d")
        sep.grid(row=row_start, column=0, columnspan=2, padx=8, pady=(14, 4), sticky="ew")
        row_start += 1

        groups_header = ctk.CTkLabel(
            self.cmp_result_frame,
            text=I18n.t("cmp_common_groups", count=len(common_groups)),
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8"
        )
        groups_header.grid(row=row_start, column=0, columnspan=2, padx=8, pady=(0, 4))
        row_start += 1

        if common_groups:
            for g in common_groups:
                g_lbl = ctk.CTkLabel(
                    self.cmp_result_frame,
                    text=f"👥  {g['name']}",
                    font=ctk.CTkFont(size=12), text_color="#a5b4fc"
                )
                g_lbl.grid(row=row_start, column=0, columnspan=2, padx=14, pady=2, sticky="w")
                row_start += 1
        else:
            ctk.CTkLabel(
                self.cmp_result_frame,
                text=I18n.t("cmp_no_common_groups"),
                text_color="#64748b", font=ctk.CTkFont(size=12)
            ).grid(row=row_start, column=0, columnspan=2, padx=8, pady=(0, 10))
            row_start += 1

        # Show partial errors (non-blocking)
        if errors:
            err_lbl = ctk.CTkLabel(
                self.cmp_result_frame,
                text="⚠️ " + "  ".join(errors),
                text_color="#f59e0b", font=ctk.CTkFont(size=11),
                wraplength=580
            )
            err_lbl.grid(row=row_start, column=0, columnspan=2, padx=8, pady=(8, 4))

    def _on_compare_export_clicked(self):
        """Export comparison as PNG using Pillow (no external deps beyond PIL)."""
        self._play_click()
        if not self._cmp_profiles:
            return
        p1, p2 = self._cmp_profiles

        import tkinter.filedialog as fd
        filepath = fd.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")],
            initialfile=f"rbx_compare_{p1['username']}_vs_{p2['username']}.png",
            title=I18n.t("cmp_export_title")
        )
        if not filepath:
            return

        threading.Thread(
            target=self._export_compare_png,
            args=(p1, p2, filepath),
            daemon=True
        ).start()

    def _export_compare_png(self, p1: dict, p2: dict, filepath: str):
        """Render a comparison card as PNG and save it."""
        try:
            from PIL import ImageDraw, ImageFont as PilFont
            W, H = 860, 520
            BG = (18, 22, 33)
            CARD_BG = (30, 41, 59)
            BLUE = (56, 189, 248)
            GREEN = (16, 185, 129)
            GRAY = (100, 116, 139)
            AMBER = (245, 158, 11)
            WHITE = (248, 250, 252)

            canvas = Image.new("RGB", (W, H), BG)
            draw = ImageDraw.Draw(canvas)

            # Try to load a system font; fall back to default
            try:
                font_title = PilFont.truetype("arial.ttf", 22)
                font_body = PilFont.truetype("arial.ttf", 16)
                font_small = PilFont.truetype("arial.ttf", 13)
            except Exception:
                font_title = PilFont.load_default()
                font_body = font_title
                font_small = font_title

            # Header
            draw.rectangle([0, 0, W, 52], fill=(15, 23, 42))
            draw.text((20, 14), "⚔️  RBX Detective — Account Comparison", font=font_title, fill=BLUE)

            # Cards
            for col, (p, side_x) in enumerate([(p1, 20), (p2, W // 2 + 10)]):
                cw = W // 2 - 30
                draw.rounded_rectangle([side_x, 64, side_x + cw, 220], radius=12, fill=CARD_BG)
                # Avatar placeholder
                draw.ellipse([side_x + 10, 74, side_x + 100, 164], fill=(30, 58, 138))
                draw.text((side_x + 30, 100), "👤", font=font_title, fill=(148, 163, 184))
                # Names
                draw.text((side_x + 115, 80), p["displayName"][:22], font=font_body, fill=WHITE)
                draw.text((side_x + 115, 110), f"@{p['username'][:22]}", font=font_small, fill=tuple(GRAY))
                draw.text((side_x + 115, 140), p["createdDate"], font=font_small, fill=tuple(GRAY))
                draw.text((side_x + 115, 162), p["accountAge"], font=font_small, fill=tuple(BLUE))

            # Stats comparison table
            rows = [
                (I18n.t("cmp_stat_friends"), p1["socials"].get("friends", 0), p2["socials"].get("friends", 0)),
                (I18n.t("cmp_stat_followers"), p1["socials"].get("followers", 0), p2["socials"].get("followers", 0)),
            ]
            y = 235
            for label, v1, v2 in rows:
                w = "left" if v1 > v2 else ("right" if v2 > v1 else "tie")
                c1 = GREEN if w == "left" else (AMBER if w == "tie" else GRAY)
                c2 = GREEN if w == "right" else (AMBER if w == "tie" else GRAY)
                draw.text((30, y), f"{v1:,}", font=font_body, fill=c1)
                draw.text((W // 2 - 80, y), label, font=font_small, fill=(148, 163, 184))
                draw.text((W // 2 + 60, y), f"{v2:,}", font=font_body, fill=c2)
                y += 30

            # Footer
            draw.rectangle([0, H - 30, W, H], fill=(15, 23, 42))
            draw.text((20, H - 22), "Generated by RBX Detective  •  github.com/RostUAGamer/RBX-detective",
                      font=font_small, fill=tuple(GRAY))

            canvas.save(filepath, "PNG")
            self.after(0, lambda: self.status_lbl.configure(
                text=I18n.t("cmp_export_done", path=filepath), text_color="#10b981"
            ))
        except Exception as e:
            self.after(0, lambda: self.status_lbl.configure(
                text=I18n.t("cmp_export_error", error=str(e)), text_color="#ef4444"
            ))

    def _open_settings_dialog(self):
        """Unified Settings Dialog with Language selector and Sound volume slider."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(I18n.t("settings_title"))
        dialog.geometry("460x340")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)

        try:
            if os.path.exists("icon.ico"):
                dialog.iconbitmap("icon.ico")
        except Exception:
            pass

        content_box = ctk.CTkFrame(dialog, corner_radius=12, fg_color="#181b22", border_width=1, border_color="#272d38")
        content_box.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Секція мови
        lang_title = ctk.CTkLabel(
            content_box,
            text=f"🌐 {I18n.t('select_language')}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38bdf8"
        )
        lang_title.pack(anchor="w", padx=20, pady=(16, 8))

        lang_options = [f"{name} ({code})" for code, name in LANGUAGES.items()]
        curr_code = I18n.current_lang
        curr_display = f"{LANGUAGES.get(curr_code, 'English')} ({curr_code})"

        lang_combo = ctk.CTkComboBox(
            content_box,
            values=lang_options,
            width=380,
            height=38,
            font=ctk.CTkFont(size=14),
            state="readonly"
        )
        lang_combo.set(curr_display)
        lang_combo.pack(padx=20, pady=(0, 16))

        # 2. Секція звуку (Повзунок гучності)
        vol_title_frame = ctk.CTkFrame(content_box, fg_color="transparent")
        vol_title_frame.pack(fill="x", padx=20, pady=(0, 4))

        vol_lbl = ctk.CTkLabel(
            vol_title_frame,
            text=f"🔊 {I18n.t('sound_volume_label')}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38bdf8"
        )
        vol_lbl.pack(side="left")

        current_vol_pct = int(SoundManager.get_volume() * 100)
        vol_val_lbl = ctk.CTkLabel(
            vol_title_frame,
            text=f"{current_vol_pct}%" if current_vol_pct > 0 else I18n.t("sound_muted"),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#a5b4fc"
        )
        vol_val_lbl.pack(side="right")

        def on_slider_move(val):
            SoundManager.set_volume(val)
            pct = int(val * 100)
            vol_val_lbl.configure(text=f"{pct}%" if pct > 0 else I18n.t("sound_muted"))

        def on_slider_release(event):
            # Test play click sound on release
            self._play_click()

        vol_slider = ctk.CTkSlider(
            content_box,
            from_=0.0,
            to=1.0,
            number_of_steps=20,
            width=380,
            height=18,
            progress_color="#0284c7",
            button_color="#38bdf8",
            button_hover_color="#7dd3fc",
            command=on_slider_move
        )
        vol_slider.set(SoundManager.get_volume())
        vol_slider.bind("<ButtonRelease-1>", on_slider_release)
        vol_slider.pack(padx=20, pady=(4, 20))

        # 3. Кнопка збереження
        def save_and_close():
            self._play_click()
            selected = lang_combo.get()
            code = selected.split("(")[-1].replace(")", "").strip()
            if code in LANGUAGES:
                I18n.set_language(code)
            I18n.set_volume(vol_slider.get())
            dialog.destroy()
            self._apply_language_change()

        btn_box = ctk.CTkFrame(content_box, fg_color="transparent")
        btn_box.pack(fill="x", padx=20, pady=(0, 16))

        save_btn = ctk.CTkButton(
            btn_box,
            text=I18n.t("btn_save"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=36,
            width=130,
            command=save_and_close
        )
        save_btn.pack(side="right")

    def _apply_language_change(self):
        """Refreshes all static text, tab headers, and re-renders profile."""
        self.title(I18n.t("app_title"))
        self.search_entry.configure(placeholder_text=I18n.t("search_placeholder"))
        self.search_btn.configure(text=I18n.t("search_btn"))
        self.open_profile_btn.configure(text=I18n.t("btn_open_profile"))
        self.desc_title.configure(text=I18n.t("bio_title"))

        self._refresh_tab_headers()

        for key, lbl in self.stat_title_labels.items():
            lbl.configure(text=I18n.t(key))

        if self.current_profile_data:
            raw_details = self.current_profile_data
            created_str = raw_details.get("rawCreated", "")
            if created_str:
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                    now = datetime.now(dt.tzinfo)
                    diff = now - dt
                    years = diff.days // 365
                    remaining_days = diff.days % 365
                    if years > 0:
                        raw_details["accountAge"] = I18n.t("years_days_ago", years=years, days=remaining_days)
                    else:
                        raw_details["accountAge"] = I18n.t("days_ago", days=diff.days)
                except Exception:
                    pass

            self._update_ui_with_profile(raw_details, self.current_avatar_image)
        else:
            self.status_lbl.configure(text=I18n.t("status_initial"))
            self.game_badges_placeholder.configure(text=I18n.t("game_badges_empty"))
            self.groups_placeholder.configure(text=I18n.t("groups_empty"))
            self.past_names_placeholder.configure(text=I18n.t("past_names_empty"))
            self.roblox_badges_placeholder.configure(text=I18n.t("roblox_badges_empty"))
            self.join_game_btn.configure(text=I18n.t("btn_player_not_ingame"))
            self.presence_badge.configure(text=f"● {I18n.t('offline')}")

        # Refresh new button labels
        if hasattr(self, "random_player_btn"):
            self.random_player_btn.configure(text=I18n.t("btn_random_player"))
        if hasattr(self, "joinable_player_btn"):
            self.joinable_player_btn.configure(text=I18n.t("btn_random_joinable"))

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
        self._re_enable_buttons()

        self.display_name_lbl.configure(text=profile["displayName"])
        self.username_lbl.configure(text=f"@{profile['username']}")

        if avatar_img:
            self.avatar_canvas.configure(image=avatar_img, text="")
            self.current_avatar_image = avatar_img
        else:
            self.avatar_canvas.configure(image="", text="👤")

        # Онлайн статус та кнопка Join Game
        pres = profile["presence"]
        ptype = pres.get("presenceType", 0)
        type_names = {
            0: I18n.t("offline"),
            1: I18n.t("online_site"),
            2: I18n.t("in_game"),
            3: I18n.t("in_studio")
        }
        status_text = type_names.get(ptype, I18n.t("offline"))
        self.presence_badge.configure(text=f"● {status_text}", fg_color=pres["color"])

        if ptype == 2:  # In-Game
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
        self._render_created_games_badges(profile["createdGamesBadges"])
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

    def _render_created_games_badges(self, badges: list):
        for widget in self.game_badges_scroll.winfo_children():
            widget.destroy()

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

            game_name = b.get("gameName", "Roblox")
            desc = b.get("description") or ""
            info_text = I18n.t("game_creator_prefix", gameName=game_name, desc=desc)

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
