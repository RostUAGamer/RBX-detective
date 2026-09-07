"""
RBX Detective - Головний застосунок (CustomTkinter GUI)
Зручний та сучасний інтерфейс для аналізу гравців Roblox.
"""
import threading
import webbrowser
from io import BytesIO
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
import requests

from roblox_api import RobloxAPI


# Налаштування теми CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class RBXDetectiveApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("RBX Detective — Roblox Player Intel")
        self.geometry("980x740")
        self.minsize(880, 640)

        # Змінна для посилань на аватар (щоб GC не видаляв)
        self.current_avatar_image = None
        self.current_profile_data = None

        self._init_ui()

    def _init_ui(self):
        # Головний контейнер з відступами
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Верхня панель пошуку (Header / Search Bar)
        search_frame = ctk.CTkFrame(self, corner_radius=14, fg_color="#181b22", border_width=1, border_color="#272d38")
        search_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
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
            placeholder_text="Введіть нікнейм або User ID гравця Roblox...",
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
            text="Знайти гравця",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self.start_search
        )
        self.search_btn.grid(row=0, column=2, padx=(0, 16), pady=12)

        # 2. Статус-бар (завантаження / помилки)
        self.status_lbl = ctk.CTkLabel(
            self,
            text="Введіть нікнейм гравця та натисніть «Знайти гравця» або клавішу Enter",
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8"
        )
        self.status_lbl.grid(row=2, column=0, padx=20, pady=(4, 12), sticky="w")

        # 3. Основна область вмісту
        self.main_content = ctk.CTkFrame(self, corner_radius=16, fg_color="#13161c")
        self.main_content.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        self.main_content.grid_columnconfigure(0, weight=1, minsize=290)
        self.main_content.grid_columnconfigure(1, weight=3)
        self.main_content.grid_rowconfigure(0, weight=1)

        # Ліва колонка: Аватар + Статус онлайну + Посилання
        self._build_left_profile_panel()

        # Права колонка: Вкладки з детальною інформацією
        self._build_right_tabview()

    def _build_left_profile_panel(self):
        self.left_card = ctk.CTkFrame(self.main_content, corner_radius=14, fg_color="#1c212b", border_width=1, border_color="#2b3240")
        self.left_card.grid(row=0, column=0, padx=(14, 8), pady=14, sticky="nsew")
        self.left_card.grid_columnconfigure(0, weight=1)

        # Аватар
        self.avatar_canvas = ctk.CTkLabel(self.left_card, text="", width=150, height=150)
        self.avatar_canvas.grid(row=0, column=0, pady=(20, 10))

        # Нікнейм та Display Name
        self.display_name_lbl = ctk.CTkLabel(
            self.left_card,
            text="—",
            font=ctk.CTkFont(size=19, weight="bold"),
            text_color="#f8fafc"
        )
        self.display_name_lbl.grid(row=1, column=0, padx=12, pady=(0, 2))

        self.username_lbl = ctk.CTkLabel(
            self.left_card,
            text="@—",
            font=ctk.CTkFont(size=14),
            text_color="#94a3b8"
        )
        self.username_lbl.grid(row=2, column=0, padx=12, pady=(0, 10))

        # Бейдж статусу онлайн
        self.presence_badge = ctk.CTkLabel(
            self.left_card,
            text="● Offline",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#334155",
            text_color="#e2e8f0",
            corner_radius=8,
            padx=12,
            pady=4
        )
        self.presence_badge.grid(row=3, column=0, pady=(0, 12))

        # Бейдж бану / валідності
        self.banned_badge = ctk.CTkLabel(
            self.left_card,
            text="Активний",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#14532d",
            text_color="#86efac",
            corner_radius=6,
            padx=10,
            pady=3
        )
        self.banned_badge.grid(row=4, column=0, pady=(0, 15))

        # Кнопка відкриття профілю на сайті
        self.open_profile_btn = ctk.CTkButton(
            self.left_card,
            text="Відкрити профіль Roblox ↗",
            font=ctk.CTkFont(size=13),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            corner_radius=8,
            command=self._open_roblox_profile
        )
        self.open_profile_btn.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="ew")

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

        # Створення вкладок
        self.tab_info = self.tabview.add("👤 Профіль")
        self.tab_groups = self.tabview.add("👥 Групи")
        self.tab_past_names = self.tabview.add("📜 Старі нікнейми")
        self.tab_badges = self.tabview.add("🏅 Бейджі")

        self._setup_info_tab()
        self._setup_groups_tab()
        self._setup_past_names_tab()
        self._setup_badges_tab()

    def _setup_info_tab(self):
        self.tab_info.grid_columnconfigure(0, weight=1)
        self.tab_info.grid_columnconfigure(1, weight=1)

        # Статистичні картки (User ID, Дата створення, Друзі, Підписники)
        self.stat_cards = {}
        fields = [
            ("User ID", "0", 0, 0),
            ("Верифікація", "Ні", 0, 1),
            ("Дата реєстрації", "—", 1, 0),
            ("Вік акаунта", "—", 1, 1),
            ("Друзів", "0", 2, 0),
            ("Підписників", "0", 2, 1),
        ]

        for title, val, r, c in fields:
            card = ctk.CTkFrame(self.tab_info, corner_radius=10, fg_color="#111620", border_width=1, border_color="#272f3d")
            card.grid(row=r, column=c, padx=6, pady=5, sticky="ew")
            
            lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color="#94a3b8")
            lbl_title.pack(anchor="w", padx=12, pady=(6, 0))

            lbl_val = ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=14, weight="bold"), text_color="#38bdf8")
            lbl_val.pack(anchor="w", padx=12, pady=(0, 8))
            self.stat_cards[title] = lbl_val

        # Біографія / Опис
        desc_frame = ctk.CTkFrame(self.tab_info, corner_radius=10, fg_color="#111620", border_width=1, border_color="#272f3d")
        desc_frame.grid(row=3, column=0, columnspan=2, padx=6, pady=10, sticky="nsew")
        self.tab_info.grid_rowconfigure(3, weight=1)

        desc_title = ctk.CTkLabel(desc_frame, text="Опис гравця (About / Bio):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#cbd5e1")
        desc_title.pack(anchor="w", padx=12, pady=(8, 2))

        self.desc_textbox = ctk.CTkTextbox(
            desc_frame,
            wrap="word",
            font=ctk.CTkFont(size=13),
            fg_color="#0b0f17",
            text_color="#e2e8f0",
            corner_radius=8
        )
        self.desc_textbox.pack(fill="both", expand=True, padx=10, pady=(2, 10))

    def _setup_groups_tab(self):
        self.groups_scroll = ctk.CTkScrollableFrame(self.tab_groups, corner_radius=10, fg_color="#111620")
        self.groups_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self.groups_placeholder = ctk.CTkLabel(self.groups_scroll, text="Інформація про групи з'явиться тут", text_color="#64748b")
        self.groups_placeholder.pack(pady=40)

    def _setup_past_names_tab(self):
        self.past_names_scroll = ctk.CTkScrollableFrame(self.tab_past_names, corner_radius=10, fg_color="#111620")
        self.past_names_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self.past_names_placeholder = ctk.CTkLabel(self.past_names_scroll, text="Історія нікнеймів з'явиться тут", text_color="#64748b")
        self.past_names_placeholder.pack(pady=40)

    def _setup_badges_tab(self):
        self.badges_scroll = ctk.CTkScrollableFrame(self.tab_badges, corner_radius=10, fg_color="#111620")
        self.badges_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self.badges_placeholder = ctk.CTkLabel(self.badges_scroll, text="Офіційні бейджі Roblox з'являться тут", text_color="#64748b")
        self.badges_placeholder.pack(pady=40)

    def start_search(self):
        query = self.search_entry.get().strip()
        if not query:
            self.status_lbl.configure(text="⚠️ Будь ласка, введіть нікнейм або ID!", text_color="#f59e0b")
            return

        self.status_lbl.configure(text=f"⏳ Отримую дані для «{query}» з серверів Roblox...", text_color="#38bdf8")
        self.search_btn.configure(state="disabled")

        # Запускаємо в окремому потоці, щоб UI не блокувався під час мережевих запитів
        thread = threading.Thread(target=self._search_worker, args=(query,), daemon=True)
        thread.start()

    def _search_worker(self, query: str):
        try:
            profile = RobloxAPI.fetch_full_profile(query)
            
            # Завантаження аватара
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
        self.status_lbl.configure(text=f"✅ Успішно завантажено профіль @{profile['username']}", text_color="#10b981")

        # Оновлення лівої картки
        self.display_name_lbl.configure(text=profile["displayName"])
        self.username_lbl.configure(text=f"@{profile['username']}")

        if avatar_img:
            self.avatar_canvas.configure(image=avatar_img, text="")
            self.current_avatar_image = avatar_img
        else:
            self.avatar_canvas.configure(image="", text="👤\n(Немає фото)")

        # Онлайн статус
        pres = profile["presence"]
        self.presence_badge.configure(text=f"● {pres['status']}", fg_color=pres["color"])

        # Бан статус
        if profile["isBanned"]:
            self.banned_badge.configure(text="⛔ ЗАБАНЕНИЙ", fg_color="#7f1d1d", text_color="#fca5a5")
        else:
            self.banned_badge.configure(text="✓ Активний", fg_color="#14532d", text_color="#86efac")

        # Статистичні поля
        self.stat_cards["User ID"].configure(text=str(profile["id"]))
        self.stat_cards["Верифікація"].configure(
            text="✓ Підтверджено" if profile["hasVerifiedBadge"] else "Ні",
            text_color="#38bdf8" if profile["hasVerifiedBadge"] else "#94a3b8"
        )
        self.stat_cards["Дата реєстрації"].configure(text=profile["createdDate"])
        self.stat_cards["Вік акаунта"].configure(text=profile["accountAge"])
        self.stat_cards["Друзів"].configure(text=f"{profile['socials']['friends']:,}")
        self.stat_cards["Підписників"].configure(text=f"{profile['socials']['followers']:,}")

        # Опис
        self.desc_textbox.delete("1.0", "end")
        self.desc_textbox.insert("1.0", profile["description"])

        # Оновлення списку груп
        self._render_groups(profile["groups"])

        # Оновлення минулих нікнеймів
        self._render_past_names(profile["pastNames"])

        # Оновлення бейджів
        self._render_badges(profile["badges"])

    def _render_groups(self, groups: list):
        for widget in self.groups_scroll.winfo_children():
            widget.destroy()

        if not groups:
            lbl = ctk.CTkLabel(self.groups_scroll, text="Користувач не є учасником публічних груп", text_color="#64748b")
            lbl.pack(pady=30)
            return

        header = ctk.CTkLabel(self.groups_scroll, text=f"Групи (всього: {len(groups)}):", font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8")
        header.pack(anchor="w", padx=10, pady=(6, 8))

        for g in groups:
            card = ctk.CTkFrame(self.groups_scroll, corner_radius=8, fg_color="#1e293b", border_width=1, border_color="#334155")
            card.pack(fill="x", padx=6, pady=4)
            card.grid_columnconfigure(0, weight=1)

            name_lbl = ctk.CTkLabel(card, text=g["name"], font=ctk.CTkFont(size=13, weight="bold"), text_color="#f8fafc", anchor="w")
            name_lbl.grid(row=0, column=0, padx=12, pady=(6, 2), sticky="w")

            role_lbl = ctk.CTkLabel(card, text=f"Роль: {g['role']} (Ранг: {g['rank']})  •  Учасників: {g['memberCount']:,}", font=ctk.CTkFont(size=11), text_color="#94a3b8", anchor="w")
            role_lbl.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="w")

    def _render_past_names(self, past_names: list):
        for widget in self.past_names_scroll.winfo_children():
            widget.destroy()

        if not past_names:
            lbl = ctk.CTkLabel(self.past_names_scroll, text="Історія минулих імен порожня (або користувач ніколи не змінював нік)", text_color="#64748b")
            lbl.pack(pady=30)
            return

        header = ctk.CTkLabel(self.past_names_scroll, text=f"Попередні нікнейми ({len(past_names)}):", font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8")
        header.pack(anchor="w", padx=10, pady=(6, 8))

        for idx, name in enumerate(past_names, 1):
            row_frame = ctk.CTkFrame(self.past_names_scroll, corner_radius=8, fg_color="#1e293b")
            row_frame.pack(fill="x", padx=6, pady=3)

            lbl = ctk.CTkLabel(row_frame, text=f"#{idx}  {name}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#e2e8f0")
            lbl.pack(anchor="w", padx=12, pady=6)

    def _render_badges(self, badges: list):
        for widget in self.badges_scroll.winfo_children():
            widget.destroy()

        if not badges:
            lbl = ctk.CTkLabel(self.badges_scroll, text="Офіційних бейджів не знайдено", text_color="#64748b")
            lbl.pack(pady=30)
            return

        header = ctk.CTkLabel(self.badges_scroll, text=f"Офіційні нагороди Roblox ({len(badges)}):", font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8")
        header.pack(anchor="w", padx=10, pady=(6, 8))

        for b in badges:
            card = ctk.CTkFrame(self.badges_scroll, corner_radius=8, fg_color="#1e293b", border_width=1, border_color="#334155")
            card.pack(fill="x", padx=6, pady=4)
            card.grid_columnconfigure(0, weight=1)

            b_name = ctk.CTkLabel(card, text=f"🏅 {b.get('name')}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#f59e0b", anchor="w")
            b_name.grid(row=0, column=0, padx=12, pady=(6, 2), sticky="w")

            b_desc = ctk.CTkLabel(card, text=b.get("description", ""), font=ctk.CTkFont(size=11), text_color="#94a3b8", wraplength=550, justify="left", anchor="w")
            b_desc.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="w")

    def _show_error(self, error_message: str):
        self.search_btn.configure(state="normal")
        self.status_lbl.configure(text=f"❌ Помилка: {error_message}", text_color="#ef4444")

    def _open_roblox_profile(self):
        if self.current_profile_data and self.current_profile_data.get("profileUrl"):
            webbrowser.open(self.current_profile_data["profileUrl"])


if __name__ == "__main__":
    app = RBXDetectiveApp()
    app.mainloop()
