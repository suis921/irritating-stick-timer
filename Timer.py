import time, json, os, sys, pygame
import tkinter as tk
from tkinter import ttk, messagebox

old_green = '#AADDAA'
old_pink = '#FFBBBB'

white = '#FFFFFF'
black = '#000000'
gray = '#CCCCCC'
beige = '#FFFCDB'
p_blue = '#D3EDFB'
p_pink = '#FADCD9'

# 基準ウィンドウサイズ(フォント等の拡大率の基準)
BASE_W = 800
BASE_H = 600

# 曲リスト(表示名: ファイル名)。曲名・ファイル名はここを書き換えてください
SONGS = {
  "なし": None,  # 曲を流さない
  "天国と地獄": "heaven_and_hell_loop.mp3",
  "道化師のギャロップ": "comedians_galop_loop.mp3",
  "クシコス・ポスト": "csikos_post_loop.mp3",
}

# 同梱ファイル(音声)の場所:exe化時は一時展開先、通常実行時はスクリプトのフォルダ
RESOURCE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

# 書き込むファイル(ランキング)の場所:exeやスクリプトと同じフォルダ
if getattr(sys, "frozen", False):
  APP_DIR = os.path.dirname(sys.executable)
else:
  APP_DIR = os.path.dirname(os.path.abspath(__file__))
RANKING_PATH = os.path.join(APP_DIR, "ranking.json")

time_bef = 0
delta_time = 0
total_time = 0

isTimering = False

records = []

pygame.mixer.init()

# ---------- 音楽 ----------
def play_music():
  filename = SONGS[song_var.get()]
  if filename is None:  # 「なし」なら何も流さない
    pygame.mixer.music.stop()
    return
  path = os.path.join(RESOURCE_DIR, filename)
  try:
    pygame.mixer.music.load(path)
    pygame.mixer.music.play(loops=-1)  # -1 で無限ループ
  except (pygame.error, FileNotFoundError):
    messagebox.showwarning("音声エラー", f"音声ファイルを再生できませんでした:\n{path}")
  return

def stop_music():
  pygame.mixer.music.stop()
  return

def on_song_change(event=None):
  # 計測中に曲を変えたら、すぐ新しい曲に切り替える
  if isTimering:
    play_music()
  tab_timer.focus_set()  # コンボボックスにフォーカスが残らないように
  return

# ---------- ボタンに与える関数 ----------
def start_stop_timer():
  global isTimering
  
  if not isTimering:
    isTimering = True
    start_stop_button.config(text="STOP")
    start_timer()
    play_music()
  else:
    isTimering = False
    start_stop_button.config(text="START")
    stop_timer()
    stop_music()
  return

def start_timer():
  global time_bef
  
  time_bef = time.perf_counter()
  return

def stop_timer():
  global total_time
  
  total_time += time.perf_counter() - time_bef
  return

def reset_timer():
  global time_bef, total_time
  total_time = 0
  
  if isTimering:
    time_bef = time.perf_counter()
  return

def save_time():
  popup = tk.Toplevel(root)
  popup.title("ランキングに保存")
  popup.geometry("360x130")
  popup.transient(root)
  
  tk.Label(popup, text="名前:", font=("Arial", 14)).pack(pady=(10, 0))
  
  name_entry = tk.Entry(popup, font=("Arial", 14))
  name_entry.pack(pady=5)
  name_entry.focus_set()
  
  def save():
    name = name_entry.get().strip()
    
    if not name:
      name = "名無し"
    
    save_record(name)
    popup.destroy()
    
  tk.Button(popup, text="OK", font=("Arial", 14), command=save).pack()
  
  name_entry.bind("<Return>", lambda e: save())
  
  return

def save_record(name):
  global records
  records.append((delta_time, name))
  records.sort()
  update_ranking()
  
  return

def delete_ranking():
  selected = tree.selection()
  
  if not selected:
    return
  value = tree.item(selected)['values']
  records.pop(value[0] - 1)
  
  update_ranking()
  
  return

def delete_all():
  global records
  records.clear()
  update_ranking()
  
  return

# ---------- 画面構築 ----------
root = tk.Tk()
root.title("Timer v1.1")
root.geometry(f"{BASE_W}x{BASE_H}+100+100")
root.minsize(640, 480)
root.configure(bg=white)

# 起動時にウィンドウを最大化(タイトルバーと最大化/元に戻すボタンは残る)
try:
  root.state("zoomed")  # Windows / macOS
except tk.TclError:
  root.attributes("-zoomed", True)  # Linux

# コンボボックスのドロップダウン一覧のフォント
root.option_add("*TCombobox*Listbox.font", ("Arial", 16))

style = ttk.Style()
style.theme_use("default")

style.configure("Treeview", rowheight=40, font=("Arial", 30, "bold"))
style.configure("Treeview.Heading", font=("Arial", 16, "bold"))
style.configure("Treeview", background=beige, fieldbackground=beige)
style.configure("TNotebook.Tab", font=("Arial", 14), padding=(12, 4))

notebook = ttk.Notebook(root)

tab_timer = tk.Frame(notebook, bg=beige)
tab_ranking = tk.Frame(notebook, bg=beige)

notebook.add(tab_timer, text="タイマー")
notebook.add(tab_ranking, text="ランキング")

notebook.pack(expand=True, fill="both")

# --- タイマータブ:grid で伸縮するレイアウト ---
tab_timer.columnconfigure(0, weight=1)
tab_timer.rowconfigure(0, weight=0)  # 上部バー
tab_timer.rowconfigure(1, weight=1)  # 「タイム」
tab_timer.rowconfigure(2, weight=2)  # 時間表示
tab_timer.rowconfigure(3, weight=1)  # 下部ボタン

# 上部バー(曲選択 + SAVE)
frame_top = tk.Frame(tab_timer, bg=beige)
frame_top.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
frame_top.columnconfigure(1, weight=1)

song_label = tk.Label(frame_top, text="BGM:", font=("Arial", 16), bg=beige)
song_var = tk.StringVar(value="なし")  # 初期選択(「なし」にしたい場合は "なし")
song_combo = ttk.Combobox(frame_top, textvariable=song_var, values=list(SONGS.keys()), state="readonly", font=("Arial", 16), width=18)
song_combo.bind("<<ComboboxSelected>>", on_song_change)
save_button = tk.Button(frame_top, text='SAVE', font=("Arial", 30), command=save_time, bg=p_pink)

song_label.grid(row=0, column=0, sticky="w")
song_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))
save_button.grid(row=0, column=2, sticky="e")

# テキスト
label_time = tk.Label(tab_timer, text="タイム", font=("Arial", 50, "bold"), bg=beige)
time_show = tk.Label(tab_timer, text="0:00.00", font=("Arial", 100, "bold"), bg=beige)
label_time.grid(row=1, column=0, sticky="s")
time_show.grid(row=2, column=0)

# START / RESET ボタン
frame_buttons = tk.Frame(tab_timer, bg=beige)
frame_buttons.grid(row=3, column=0, sticky="ew", padx=40, pady=(0, 40))
frame_buttons.columnconfigure(0, weight=1)
frame_buttons.columnconfigure(1, weight=1)

start_stop_button = tk.Button(frame_buttons, text='START', width=10, font=("Arial", 30), command=start_stop_timer, bg=p_pink)
reset_button = tk.Button(frame_buttons, text='RESET', width=10, font=("Arial", 30), command=reset_timer, bg=p_pink)
start_stop_button.grid(row=0, column=0)
reset_button.grid(row=0, column=1)

# --- ランキングタブ ---
frame_bottom = tk.Frame(tab_ranking, bg=beige)
delete_button = tk.Button(frame_bottom, text="選択行を削除", font=("Arial", 20), command=delete_ranking, bg=p_pink)
alldelete_button = tk.Button(frame_bottom, text="ランキングを全削除", font=("Arial", 20), command=delete_all, bg=p_pink)

tree = ttk.Treeview(tab_ranking, columns=("rank", "name", "time"), show="headings")
tree.heading("rank", text="順位")
tree.heading("name", text="名前")
tree.heading("time", text="タイム")

# ---------- ボタンに与えない関数 ----------
def update_ranking():
  tree.delete(*tree.get_children())
  
  records.sort()
  
  for i, (t, name) in enumerate(records[:5], start=1):
    minutes = int(t // 60)
    seconds = int(t % 60)
    underseconds = int((t % 1) * 100)
    
    tree.insert("", "end", values=(i, name, f"{minutes}:{seconds:02d}.{underseconds:02d}"))
  
  return

def save_to_file():
  with open(RANKING_PATH, "w", encoding="utf-8") as f:
    json.dump(records, f)
  return

def load_from_file():
  global records
  try:
    with open(RANKING_PATH, "r", encoding="utf-8") as f:
      records = [tuple(r) for r in json.load(f)]
  
  except FileNotFoundError:
    records = []
  
  return

def on_close():
  save_to_file()
  pygame.mixer.music.stop()
  root.destroy()

# ウィンドウサイズに応じてフォント・行高さを拡大縮小
def on_resize(event):
  if event.widget is not root:
    return
  scale = min(event.width / BASE_W, event.height / BASE_H)
  scale = max(scale, 0.6)
  
  def f(size):
    return max(int(size * scale), 8)
  
  label_time.config(font=("Arial", f(50), "bold"))
  time_show.config(font=("Arial", f(100), "bold"))
  start_stop_button.config(font=("Arial", f(30)))
  reset_button.config(font=("Arial", f(30)))
  save_button.config(font=("Arial", f(30)))
  song_label.config(font=("Arial", f(16)))
  song_combo.config(font=("Arial", f(16)))
  delete_button.config(font=("Arial", f(20)))
  alldelete_button.config(font=("Arial", f(20)))
  
  style.configure("Treeview", rowheight=f(40), font=("Arial", f(30), "bold"))
  style.configure("Treeview.Heading", font=("Arial", f(16), "bold"))
  style.configure("TNotebook.Tab", font=("Arial", f(14)))
  return

root.bind("<Configure>", on_resize)

load_from_file()
update_ranking()

# ランキングタブの配置(ボタン帯を先に下端へ確保してから表を広げる)
frame_bottom.pack(side=tk.BOTTOM, fill="x")
tree.pack(fill="both", expand=True)

alldelete_button.pack(side=tk.RIGHT)
delete_button.pack(side=tk.RIGHT)

# ---------- 常時処理(計測時間更新) ----------
def refresh_timer():
  global delta_time
  
  # 経過時間取得
  if isTimering:
    delta_time = total_time + time.perf_counter() - time_bef
  else:
    delta_time = total_time
    
  # 表示計算
  delta_minute = int(delta_time // 60)
  delta_second = int(delta_time % 60)
  delta_underzero = int((delta_time % 1) * 100)
  time_show["text"] = f"{delta_minute}:{delta_second:02d}.{delta_underzero:02d}"
  root.after(10, refresh_timer)
  return

root.protocol("WM_DELETE_WINDOW", on_close)

root.after(10, refresh_timer)
root.mainloop()