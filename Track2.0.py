import sys
import traceback
import customtkinter as ctk
from datetime import datetime, date, timedelta
import sqlite3
import os

# ─── CONSTANTS ──────────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker.db")
MOOD_EMOJIS = {1: "😩", 2: "😢", 3: "😟", 4: "😕", 5: "😐", 6: "🙂", 7: "😊", 8: "😄", 9: "🤩", 10: "🔥"}

# ─── DATABASE ────────────────────────────────────────────────────────────────

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


# ─── MAIN APP ────────────────────────────────────────────────────────────────

class TrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Daily Tracker")
        self.geometry("900x750")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        init_db()

        self.selected_date = date.today()

        self._build_ui()
        self._update_date_label()  # Called AFTER all widgets are created
        self._load_entry()

    # ── UI BUILDING ──────────────────────────────────────────────────────

    def _build_ui(self):
        # Top bar - date navigation
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkButton(top, text="◀", width=40, command=self._prev_day).pack(side="left")
        self.date_label = ctk.CTkLabel(top, text="", font=("Arial", 20, "bold"))
        self.date_label.pack(side="left", expand=True)
        ctk.CTkButton(top, text="▶", width=40, command=self._next_day).pack(side="left")
        ctk.CTkButton(top, text="Today", width=70, command=self._go_today).pack(side="left", padx=(10, 0))

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # ── WEIGHT (weekly) ──
        self.weight_frame = ctk.CTkFrame(scroll)
        self.weight_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(self.weight_frame, text="⚖️  Weight (kg)", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        self.weight_entry = ctk.CTkEntry(self.weight_frame, placeholder_text="e.g. 82.5", width=150)
        self.weight_entry.pack(anchor="w", padx=15, pady=(5, 5))
        self.weight_note = ctk.CTkLabel(self.weight_frame, text="", font=("Arial", 11), text_color="gray")
        self.weight_note.pack(anchor="w", padx=15, pady=(0, 10))

        # ── SLEEP ──
        sleep_frame = ctk.CTkFrame(scroll)
        sleep_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(sleep_frame, text="😴  Sleep", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=(10, 0))

        sleep_row = ctk.CTkFrame(sleep_frame, fg_color="transparent")
        sleep_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(sleep_row, text="Hours:").pack(side="left")
        self.sleep_hours = ctk.CTkEntry(sleep_row, placeholder_text="e.g. 7.5", width=100)
        self.sleep_hours.pack(side="left", padx=(5, 20))

        ctk.CTkLabel(sleep_row, text="Disturbances:").pack(side="left")
        self.sleep_disturbances = ctk.CTkEntry(sleep_row, placeholder_text="e.g. 2", width=80)
        self.sleep_disturbances.pack(side="left", padx=(5, 0))

        self.sleep_quality_label = ctk.CTkLabel(sleep_frame, text="", font=("Arial", 12))
        self.sleep_quality_label.pack(anchor="w", padx=15, pady=(0, 10))

        # ── CALORIES ──
        cal_frame = ctk.CTkFrame(scroll)
        cal_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(cal_frame, text="🍽️  Calories", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        self.calories = ctk.CTkEntry(cal_frame, placeholder_text="e.g. 2200", width=150)
        self.calories.pack(anchor="w", padx=15, pady=(5, 10))

        # ── MOOD ──
        mood_frame = ctk.CTkFrame(scroll)
        mood_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(mood_frame, text="🧠  Mood", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        ctk.CTkLabel(mood_frame, text="1 = Awful  →  10 = Incredible", font=("Arial", 11), text_color="gray").pack(anchor="w", padx=15)

        mood_slider_row = ctk.CTkFrame(mood_frame, fg_color="transparent")
        mood_slider_row.pack(fill="x", padx=15, pady=5)

        self.mood_slider = ctk.CTkSlider(mood_slider_row, from_=1, to=10, number_of_steps=9, width=300,
                                          command=self._update_mood_label)
        self.mood_slider.set(5)
        self.mood_slider.pack(side="left")

        self.mood_value_label = ctk.CTkLabel(mood_slider_row, text="5", font=("Arial", 18, "bold"), width=40)
        self.mood_value_label.pack(side="left", padx=10)

        self.mood_emoji = ctk.CTkLabel(mood_slider_row, text="😐", font=("Arial", 24))
        self.mood_emoji.pack(side="left")

        # ── DISCOMFORT ──
        disc_frame = ctk.CTkFrame(scroll)
        disc_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(disc_frame, text="🩹  Discomfort", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        ctk.CTkLabel(disc_frame, text="0 = None  →  10 = Severe", font=("Arial", 11), text_color="gray").pack(anchor="w", padx=15)

        disc_slider_row = ctk.CTkFrame(disc_frame, fg_color="transparent")
        disc_slider_row.pack(fill="x", padx=15, pady=5)

        self.disc_slider = ctk.CTkSlider(disc_slider_row, from_=0, to=10, number_of_steps=10, width=300,
                                          command=self._update_disc_label)
        self.disc_slider.set(0)
        self.disc_slider.pack(side="left")

        self.disc_value_label = ctk.CTkLabel(disc_slider_row, text="0", font=("Arial", 18, "bold"), width=40)
        self.disc_value_label.pack(side="left", padx=10)

        ctk.CTkLabel(disc_frame, text="Notes (location, type):").pack(anchor="w", padx=15, pady=(5, 0))
        self.disc_notes = ctk.CTkTextbox(disc_frame, height=60)
        self.disc_notes.pack(fill="x", padx=15, pady=(5, 10))

        # ── GYM NOTES ──
        gym_frame = ctk.CTkFrame(scroll)
        gym_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(gym_frame, text="🏋️  Gym Notes", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        ctk.CTkLabel(gym_frame, text="How did you feel? Any PRs? Energy level?", font=("Arial", 11), text_color="gray").pack(anchor="w", padx=15)
        self.gym_notes = ctk.CTkTextbox(gym_frame, height=60)
        self.gym_notes.pack(fill="x", padx=15, pady=(5, 10))

        # ── BUTTONS ──
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(5, 10))

        ctk.CTkButton(btn_row, text="💾  Save Entry", font=("Arial", 15, "bold"),
                      height=45, command=self._save_entry).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(btn_row, text="📊  View History", font=("Arial", 15, "bold"),
                      height=45, fg_color="#2d8f4e", hover_color="#236b3c",
                      command=self._show_history).pack(side="left", expand=True, fill="x", padx=(5, 0))

        # Status bar
        self.status = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.status.pack(pady=(0, 10))

    # ── HELPERS ──────────────────────────────────────────────────────────

    def _update_date_label(self):
        d = self.selected_date
        today = date.today()
        if d == today:
            tag = " (Today)"
        elif d == today - timedelta(days=1):
            tag = " (Yesterday)"
        else:
            tag = ""
        self.date_label.configure(text=f"{d.strftime('%A, %B %d %Y')}{tag}")

        is_weigh_day = d.weekday() == 0  # Monday
        if is_weigh_day:
            self.weight_note.configure(text="📅 Monday weigh-in day!")
        else:
            self.weight_note.configure(text="Weigh-in is on Mondays. You can still log if needed.")

    def _update_mood_label(self, value):
        v = int(float(value))
        self.mood_value_label.configure(text=str(v))
        self.mood_emoji.configure(text=MOOD_EMOJIS.get(v, "😐"))

    def _update_disc_label(self, value):
        v = int(float(value))
        self.disc_value_label.configure(text=str(v))

    def _prev_day(self):
        self.selected_date -= timedelta(days=1)
        self._update_date_label()
        self._load_entry()

    def _next_day(self):
        if self.selected_date < date.today():
            self.selected_date += timedelta(days=1)
            self._update_date_label()
            self._load_entry()

    def _go_today(self):
        self.selected_date = date.today()
        self._update_date_label()
        self._load_entry()

    def _clear_fields(self):
        self.weight_entry.delete(0, "end")
        self.sleep_hours.delete(0, "end")
        self.sleep_disturbances.delete(0, "end")
        self.calories.delete(0, "end")
        self.mood_slider.set(5)
        self._update_mood_label(5)
        self.disc_slider.set(0)
        self._update_disc_label(0)
        self.disc_notes.delete("1.0", "end")
        self.gym_notes.delete("1.0", "end")
        self.sleep_quality_label.configure(text="")

    # ── DATABASE OPS ─────────────────────────────────────────────────────

    def _save_entry(self):
        date_str = self.selected_date.isoformat()
        conn = get_db()

        daily_data = (
            date_str,
            self._safe_float(self.sleep_hours.get()),
            self._safe_int(self.sleep_disturbances.get()),
            self._safe_int(self.calories.get()),
            int(float(self.mood_slider.get())),
            int(float(self.disc_slider.get())),
            self.disc_notes.get("1.0", "end").strip(),
            self.gym_notes.get("1.0", "end").strip()
        )

        conn.execute("""
            INSERT OR REPLACE INTO daily_log
            (date, sleep_hours, sleep_disturbances, calories, mood, discomfort_level, discomfort_notes, gym_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, daily_data)

        weight = self._safe_float(self.weight_entry.get())
        if weight:
            conn.execute("INSERT OR REPLACE INTO weekly_weight (date, weight_kg) VALUES (?, ?)", (date_str, weight))

        conn.commit()
        conn.close()

        self._update_sleep_quality()
        self._show_status(f"✅ Saved entry for {self.selected_date.strftime('%b %d')}!", "#2d8f4e")

    def _load_entry(self):
        self._clear_fields()
        date_str = self.selected_date.isoformat()
        conn = get_db()

        row = conn.execute("SELECT * FROM daily_log WHERE date = ?", (date_str,)).fetchone()
        if row:
            self._populate_field(self.sleep_hours, row["sleep_hours"])
            self._populate_field(self.sleep_disturbances, row["sleep_disturbances"])
            self._populate_field(self.calories, row["calories"])
            
            if row["mood"] is not None:
                self.mood_slider.set(row["mood"])
                self._update_mood_label(row["mood"])
            
            if row["discomfort_level"] is not None:
                self.disc_slider.set(row["discomfort_level"])
                self._update_disc_label(row["discomfort_level"])
            
            self._populate_textbox(self.disc_notes, row["discomfort_notes"])
            self._populate_textbox(self.gym_notes, row["gym_notes"])
            self._update_sleep_quality()

        weight_row = conn.execute("SELECT * FROM weekly_weight WHERE date = ?", (date_str,)).fetchone()
        if weight_row:
            self.weight_entry.insert(0, str(weight_row["weight_kg"]))

        conn.close()

    def _update_sleep_quality(self):
        hours = self._safe_float(self.sleep_hours.get())
        disturbances = self._safe_int(self.sleep_disturbances.get())
        
        if hours is None:
            return
        
        if hours >= 7 and (disturbances is None or disturbances <= 1):
            self.sleep_quality_label.configure(text="✅ Good sleep!", text_color="#2d8f4e")
        elif hours >= 6:
            self.sleep_quality_label.configure(text="⚠️ Okay sleep", text_color="#c9a227")
        else:
            self.sleep_quality_label.configure(text="❌ Poor sleep", text_color="#c94040")

    # ── HISTORY WINDOW ───────────────────────────────────────────────────

    def _show_history(self):
        win = ctk.CTkToplevel(self)
        win.title("📊 History - Last 14 Days")
        win.geometry("1100x700")
        win.grab_set()

        conn = get_db()
        rows = conn.execute("""
            SELECT d.*, w.weight_kg
            FROM daily_log d
            LEFT JOIN weekly_weight w ON d.date = w.date
            ORDER BY d.date DESC
            LIMIT 14
        """).fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(win, text="No entries yet! Start logging today.",
                         font=("Arial", 16)).pack(expand=True)
            return

        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self._add_summary(scroll, rows)
        self._add_charts(scroll, rows)

    def _add_summary(self, parent, rows):
        summary = ctk.CTkFrame(parent)
        summary.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(summary, text="📈 Summary", font=("Arial", 16, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

        def avg(values):
            return sum(values) / len(values) if values else 0
        
        sleep_vals = [r["sleep_hours"] for r in rows if r["sleep_hours"]]
        cal_vals = [r["calories"] for r in rows if r["calories"]]
        mood_vals = [r["mood"] for r in rows if r["mood"]]
        disc_vals = [r["discomfort_level"] for r in rows if r["discomfort_level"] is not None]

        stats = []
        if sleep_vals:
            stats.append(f"Avg Sleep: {avg(sleep_vals):.1f}h")
        if cal_vals:
            stats.append(f"Avg Calories: {int(avg(cal_vals))}")
        if mood_vals:
            stats.append(f"Avg Mood: {avg(mood_vals):.1f}/10")
        if disc_vals:
            stats.append(f"Avg Discomfort: {avg(disc_vals):.1f}/10")

        conn = get_db()
        weights = conn.execute("SELECT weight_kg FROM weekly_weight ORDER BY date DESC LIMIT 4").fetchall()
        conn.close()
        if len(weights) >= 2:
            diff = weights[0]["weight_kg"] - weights[-1]["weight_kg"]
            direction = "📉" if diff < 0 else "📈" if diff > 0 else "➡️"
            stats.append(f"Weight trend: {direction} {abs(diff):.1f}kg over {len(weights)} entries")

        ctk.CTkLabel(summary, text="  |  ".join(stats) if stats else "Not enough data yet.",
                     font=("Arial", 12)).pack(anchor="w", padx=10, pady=(0, 10))

def _add_charts(self, parent, rows):
        rows_asc = list(reversed(rows))
        
        # Sleep Chart
        self._create_chart(parent, "😴 Sleep Hours", rows_asc, "sleep_hours", "#3b82f6", max_val=12)
        
        # Mood Chart
        self._create_chart(parent, "🧠 Mood", rows_asc, "mood", "#10b981", max_val=10)
        
        # Discomfort Chart
        self._create_chart(parent, "🩹 Discomfort", rows_asc, "discomfort_level", "#ef4444", max_val=10)
        
        # Calories Chart
        self._create_chart(parent, "🍽️ Calories", rows_asc, "calories", "#f59e0b", max_val=3000)

   def _create_chart(self, parent, title, rows, field, color, max_val):
    frame = ctk.CTkFrame(parent)
    frame.pack(fill="x", pady=(0, 15))
    
    ctk.CTkLabel(frame, text=title, font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
    
    chart_frame = ctk.CTkFrame(frame, height=120)
    chart_frame.pack(fill="x", padx=10, pady=(0, 10))
    chart_frame.pack_propagate(False)

    BAR_MAX_HEIGHT = 80

    for row in rows:
        val = row[field]

        # Container per day (DO NOT use fill="both")
        bar_container = ctk.CTkFrame(chart_frame, fg_color="transparent")
        bar_container.pack(side="left", expand=True, padx=2)

        # ─── HANDLE NONE VALUES (Placeholder Column) ───
        if val is None:
            ctk.CTkFrame(
                bar_container,
                width=30,
                height=BAR_MAX_HEIGHT,
                fg_color="transparent"
            ).pack()

            date_str = datetime.fromisoformat(row["date"]).strftime("%m/%d")
            ctk.CTkLabel(
                bar_container,
                text="–",
                font=("Arial", 9),
                text_color="gray"
            ).pack(pady=(2, 0))

            ctk.CTkLabel(
                bar_container,
                text=date_str,
                font=("Arial", 8),
                text_color="gray"
            ).pack()

            continue

        # ─── NORMAL BAR CALCULATION ───
        bar_height = int((val / max_val) * BAR_MAX_HEIGHT) if max_val > 0 else 0
        bar_height = max(2, min(bar_height, BAR_MAX_HEIGHT))  # Clamp AFTER calculation
        spacer_height = BAR_MAX_HEIGHT - bar_height  # Derived from clamped value

        # Spacer (top empty part)
        ctk.CTkFrame(
            bar_container,
            width=30,
            height=spacer_height,
            fg_color="transparent"
        ).pack()

        # Actual bar
        ctk.CTkFrame(
            bar_container,
            width=30,
            height=bar_height,
            fg_color=color,
            corner_radius=3
        ).pack()

        # Value label
        ctk.CTkLabel(
            bar_container,
            text=str(int(val) if isinstance(val, (int, float)) else val),
            font=("Arial", 9, "bold")
        ).pack(pady=(2, 0))

        # Date label
        date_str = datetime.fromisoformat(row["date"]).strftime("%m/%d")
        ctk.CTkLabel(
            bar_container,
            text=date_str,
            font=("Arial", 8),
            text_color="gray"
        ).pack()

    # ── UTILITIES ────────────────────────────────────────────────────────

    def _populate_field(self, widget, value):
        if value is not None:
            widget.insert(0, str(value))
    
    def _populate_textbox(self, widget, value):
        if value:
            widget.insert("1.0", value)
    
    def _show_status(self, message, color):
        self.status.configure(text=message, text_color=color)
        self.after(3000, lambda: self.status.configure(text=""))

    def _mood_mini(self, val):
        return f"{val} {MOOD_EMOJIS.get(val, '')}"

    def _disc_mini(self, val):
        if val == 0:
            return "✅ 0"
        if val <= 3:
            return f"🟡 {val}"
        if val <= 6:
            return f"🟠 {val}"
        return f"🔴 {val}"

    def _safe_float(self, val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, val):
        try:
            return int(val)
        except (ValueError, TypeError):
            return None


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        app = TrackerApp()
        app.mainloop()
    except Exception as e:
        # Write crash info to a log file next to the script so you can see what went wrong
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker_crash.log")
        with open(log_path, "w") as f:
            f.write(traceback.format_exc())
        # Also try to show a basic tk error dialog
        try:
            import tkinter as tk
            import tkinter.messagebox as mb
            root = tk.Tk()
            root.withdraw()
            mb.showerror("Tracker crashed", f"Error: {e}\n\nSee tracker_crash.log for details.")
            root.destroy()
        except Exception:
            pass
        sys.exit(1)