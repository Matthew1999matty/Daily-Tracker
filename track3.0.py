import sys
import traceback
import customtkinter as ctk
from datetime import datetime, date, timedelta
import sqlite3
import os

# ─────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker.db")

MOOD_EMOJIS = {
    1: "😩", 2: "😢", 3: "😟", 4: "😕", 5: "😐",
    6: "🙂", 7: "😊", 8: "😄", 9: "🤩", 10: "🔥"
}

BAR_MAX_HEIGHT = 80

# ─────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS daily_log (
            date TEXT PRIMARY KEY,
            sleep_hours REAL,
            sleep_disturbances INTEGER,
            calories INTEGER,
            mood INTEGER,
            discomfort_level INTEGER,
            discomfort_notes TEXT,
            gym_notes TEXT
        );

        CREATE TABLE IF NOT EXISTS weekly_weight (
            date TEXT PRIMARY KEY,
            weight_kg REAL
        );
    """)
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────

class TrackerApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Daily Tracker")
        self.geometry("1000x800")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        init_db()

        self.selected_date = date.today()

        self.build_ui()
        self.update_date_label()
        self.load_entry()

    # ───────────────── UI ─────────────────

    def build_ui(self):

        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(top, text="◀", width=40, command=self.prev_day).pack(side="left")
        self.date_label = ctk.CTkLabel(top, text="", font=("Arial", 20, "bold"))
        self.date_label.pack(side="left", expand=True)
        ctk.CTkButton(top, text="▶", width=40, command=self.next_day).pack(side="left")
        ctk.CTkButton(top, text="Today", command=self.go_today).pack(side="left", padx=10)

        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # Weight
        self.weight_entry = self.create_entry_block(scroll, "⚖️ Weight (kg)")

        # Sleep
        sleep_frame = self.create_section(scroll, "😴 Sleep")

        row = ctk.CTkFrame(sleep_frame)
        row.pack(pady=5)

        ctk.CTkLabel(row, text="Hours:").pack(side="left")
        self.sleep_hours = ctk.CTkEntry(row, width=100)
        self.sleep_hours.pack(side="left", padx=5)

        ctk.CTkLabel(row, text="Disturbances:").pack(side="left")
        self.sleep_disturbances = ctk.CTkEntry(row, width=80)
        self.sleep_disturbances.pack(side="left", padx=5)

        self.sleep_quality_label = ctk.CTkLabel(sleep_frame, text="")
        self.sleep_quality_label.pack()

        # Calories
        self.calories = self.create_entry_block(scroll, "🍽️ Calories")

        # Mood
        mood_frame = self.create_section(scroll, "🧠 Mood (1-10)")

        self.mood_slider = ctk.CTkSlider(
            mood_frame, from_=1, to=10, number_of_steps=9,
            command=self.update_mood
        )
        self.mood_slider.set(5)
        self.mood_slider.pack(pady=5)

        self.mood_label = ctk.CTkLabel(mood_frame, text="5 😐", font=("Arial", 18))
        self.mood_label.pack()

        # Discomfort
        disc_frame = self.create_section(scroll, "🩹 Discomfort (0-10)")

        self.disc_slider = ctk.CTkSlider(
            disc_frame, from_=0, to=10, number_of_steps=10,
            command=self.update_disc
        )
        self.disc_slider.set(0)
        self.disc_slider.pack(pady=5)

        self.disc_label = ctk.CTkLabel(disc_frame, text="0")
        self.disc_label.pack()

        # Gym
        gym_frame = self.create_section(scroll, "🏋️ Gym Notes")
        self.gym_notes = ctk.CTkTextbox(gym_frame, height=60)
        self.gym_notes.pack(fill="x", pady=5)

        # Buttons
        bottom = ctk.CTkFrame(self)
        bottom.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(bottom, text="💾 Save", command=self.save_entry).pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkButton(bottom, text="📊 History", command=self.show_history).pack(side="left", expand=True, fill="x", padx=5)

        self.status = ctk.CTkLabel(self, text="")
        self.status.pack(pady=5)

    # ───────────────── UI Helpers ─────────────────

    def create_section(self, parent, title):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10)
        ctk.CTkLabel(frame, text=title, font=("Arial", 16, "bold")).pack(pady=5)
        return frame

    def create_entry_block(self, parent, title):
        frame = self.create_section(parent, title)
        entry = ctk.CTkEntry(frame)
        entry.pack(pady=5)
        return entry

    # ───────────────── Date Navigation ─────────────────

    def update_date_label(self):
        self.date_label.configure(text=self.selected_date.strftime("%A %d %B %Y"))

    def prev_day(self):
        self.selected_date -= timedelta(days=1)
        self.update_date_label()
        self.load_entry()

    def next_day(self):
        if self.selected_date < date.today():
            self.selected_date += timedelta(days=1)
            self.update_date_label()
            self.load_entry()

    def go_today(self):
        self.selected_date = date.today()
        self.update_date_label()
        self.load_entry()

    # ───────────────── Sliders ─────────────────

    def update_mood(self, val):
        v = int(float(val))
        self.mood_label.configure(text=f"{v} {MOOD_EMOJIS.get(v, '')}")

    def update_disc(self, val):
        v = int(float(val))
        self.disc_label.configure(text=str(v))

    # ───────────────── Database ─────────────────

    def save_entry(self):
        conn = get_db()
        d = self.selected_date.isoformat()

        conn.execute("""
            INSERT OR REPLACE INTO daily_log
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d,
            self.safe_float(self.sleep_hours.get()),
            self.safe_int(self.sleep_disturbances.get()),
            self.safe_int(self.calories.get()),
            int(self.mood_slider.get()),
            int(self.disc_slider.get()),
            "",
            self.gym_notes.get("1.0", "end").strip()
        ))

        weight = self.safe_float(self.weight_entry.get())
        if weight:
            conn.execute(
                "INSERT OR REPLACE INTO weekly_weight VALUES (?, ?)",
                (d, weight)
            )

        conn.commit()
        conn.close()

        self.status.configure(text="Saved!", text_color="green")
        self.after(2000, lambda: self.status.configure(text=""))

    def load_entry(self):
        conn = get_db()
        d = self.selected_date.isoformat()
        row = conn.execute("SELECT * FROM daily_log WHERE date=?", (d,)).fetchone()
        conn.close()

        self.clear_fields()

        if not row:
            return

        self.populate(self.sleep_hours, row["sleep_hours"])
        self.populate(self.sleep_disturbances, row["sleep_disturbances"])
        self.populate(self.calories, row["calories"])

        if row["mood"]:
            self.mood_slider.set(row["mood"])
            self.update_mood(row["mood"])

        if row["discomfort_level"] is not None:
            self.disc_slider.set(row["discomfort_level"])
            self.update_disc(row["discomfort_level"])

        if row["gym_notes"]:
            self.gym_notes.insert("1.0", row["gym_notes"])

    # ───────────────── History ─────────────────

    def show_history(self):
        win = ctk.CTkToplevel(self)
        win.geometry("1200x800")
        win.title("📊 History Overview")

        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill="both", expand=True, padx=15, pady=15)

        conn = get_db()

        daily_rows = conn.execute("""
            SELECT * FROM daily_log
            ORDER BY date ASC
            LIMIT 30
        """).fetchall()

        weight_rows = conn.execute("""
            SELECT * FROM weekly_weight
            ORDER BY date ASC
            LIMIT 12
        """).fetchall()

        conn.close()

        if not daily_rows and not weight_rows:
            ctk.CTkLabel(scroll, text="No history yet.").pack(pady=40)
            return

        # ───────── DAILY CALORIES ─────────
        cal_max = max((r["calories"] for r in daily_rows if r["calories"]), default=2000)
        self.create_chart(
            scroll,
            "🍽️ Daily Calories",
            daily_rows,
            "calories",
            "#f59e0b",
            max_val=max(cal_max * 1.1, 500)
        )

        # ───────── SLEEP DURATION ─────────
        self.create_chart(
            scroll,
            "😴 Sleep Duration (Hours)",
            daily_rows,
            "sleep_hours",
            "#3b82f6",
            max_val=12
        )

        # ───────── SLEEP DISTURBANCES ─────────
        self.create_chart(
            scroll,
            "🌙 Sleep Disturbances",
            daily_rows,
            "sleep_disturbances",
            "#8b5cf6",
            max_val=10
        )

        # ───────── WEEKLY WEIGHT ─────────
        weight_max = max((r["weight_kg"] for r in weight_rows if r["weight_kg"]), default=100)
        self.create_chart(
            scroll,
            "⚖️ Weekly Weight (kg)",
            weight_rows,
            "weight_kg",
            "#10b981",
            max_val=weight_max * 1.05
        )

        # ───────── GYM NOTES ─────────
        gym_frame = ctk.CTkFrame(scroll)
        gym_frame.pack(fill="x", pady=20)

        ctk.CTkLabel(
            gym_frame,
            text="🏋️ Gym Notes",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        notes_container = ctk.CTkFrame(gym_frame)
        notes_container.pack(fill="both", expand=True, padx=10)

        for row in daily_rows:
            if row["gym_notes"]:
                note_frame = ctk.CTkFrame(notes_container, border_width=1, border_color="gray")
                note_frame.pack(fill="x", pady=5)

                date_str = datetime.fromisoformat(row["date"]).strftime("%A, %d %B %Y")
                ctk.CTkLabel(
                    note_frame,
                    text=date_str,
                    font=("Arial", 11, "bold"),
                    text_color="#3b82f6"
                ).pack(anchor="w", padx=10, pady=(5, 0))

                textbox = ctk.CTkTextbox(note_frame, height=80, width=500)
                textbox.pack(fill="x", padx=10, pady=(0, 10))
                textbox.insert("1.0", row["gym_notes"])
                textbox.configure(state="disabled")

    def create_chart(self, parent, title, rows, field, color, max_val):
        BAR_HEIGHT = 120

        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=20)

        ctk.CTkLabel(
            frame,
            text=title,
            font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=10)

        chart = ctk.CTkFrame(frame, height=BAR_HEIGHT + 40)
        chart.pack(fill="x", padx=10, pady=10)
        chart.pack_propagate(False)

        for row in rows:
            container = ctk.CTkFrame(chart, fg_color="transparent")
            container.pack(side="left", expand=True, padx=4)

            value = row[field]

            # Date label
            date_str = datetime.fromisoformat(row["date"]).strftime("%d/%m")

            if value is None:
                ctk.CTkFrame(container, height=BAR_HEIGHT).pack()
                ctk.CTkLabel(container, text="–", text_color="gray").pack()
                ctk.CTkLabel(container, text=date_str, font=("Arial", 8), text_color="gray").pack()
                continue

            # Calculate proportional height
            bar_height = int((value / max_val) * BAR_HEIGHT)
            bar_height = max(4, min(bar_height, BAR_HEIGHT))
            spacer = BAR_HEIGHT - bar_height

            # Spacer (top empty area)
            ctk.CTkFrame(
                container,
                height=spacer,
                fg_color="transparent"
            ).pack()

            # Actual bar
            ctk.CTkFrame(
                container,
                height=bar_height,
                width=25,
                fg_color=color,
                corner_radius=4
            ).pack()

            # Value label
            display_value = f"{value:.1f}" if isinstance(value, float) else str(value)
            ctk.CTkLabel(
                container,
                text=display_value,
                font=("Arial", 9, "bold")
            ).pack()

            # Date label
            ctk.CTkLabel(
                container,
                text=date_str,
                font=("Arial", 8),
                text_color="gray"
            ).pack()


    # ───────────────── Utils ─────────────────

    def clear_fields(self):
        for w in [self.weight_entry, self.sleep_hours,
                  self.sleep_disturbances, self.calories]:
            w.delete(0, "end")

        self.gym_notes.delete("1.0", "end")

    def populate(self, widget, value):
        if value is not None:
            widget.insert(0, str(value))

    def safe_float(self, v):
        try:
            return float(v)
        except:
            return None

    def safe_int(self, v):
        try:
            return int(v)
        except:
            return None


# ───────────────── Entry Point ─────────────────

if __name__ == "__main__":
    try:
        app = TrackerApp()
        app.mainloop()
    except Exception:
        with open("tracker_crash.log", "w") as f:
            f.write(traceback.format_exc())
        sys.exit(1)
