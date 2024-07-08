import tkinter as tk
from tkinter import ttk, messagebox
from sgp4.api import Satrec, jday
from sgp4.api import SGP4_ERRORS
from datetime import datetime, timedelta
from pyproj import Proj, Transformer

class SatelliteTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SATCAL - 衛星軌道予測ツール")
        self.create_widgets()

    def create_widgets(self):
        # 入力フィールドを作成
        ttk.Label(self.root, text="TLE ライン1:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.line1_entry = ttk.Entry(self.root, width=80)
        self.line1_entry.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(self.root, text="TLE ライン2:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.line2_entry = ttk.Entry(self.root, width=80)
        self.line2_entry.grid(row=1, column=1, padx=10, pady=10)

        # 予測期間の入力フィールドを作成
        ttk.Label(self.root, text="予測期間:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        duration_frame = ttk.Frame(self.root)
        duration_frame.grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(duration_frame, text="日:").grid(row=0, column=0)
        self.days_var = tk.StringVar()
        self.days_combobox = ttk.Combobox(duration_frame, textvariable=self.days_var, width=5)
        self.days_combobox['values'] = [str(i) for i in range(8)]  # 0日から7日まで
        self.days_combobox.grid(row=0, column=1)

        ttk.Label(duration_frame, text="時間:").grid(row=0, column=2)
        self.hours_var = tk.StringVar()
        self.hours_combobox = ttk.Combobox(duration_frame, textvariable=self.hours_var, width=5)
        self.hours_combobox['values'] = [str(i) for i in range(24)]  # 0時間から23時間まで
        self.hours_combobox.grid(row=0, column=3)

        ttk.Label(duration_frame, text="分:").grid(row=0, column=4)
        self.minutes_var = tk.StringVar()
        self.minutes_combobox = ttk.Combobox(duration_frame, textvariable=self.minutes_var, width=5)
        self.minutes_combobox['values'] = [str(i) for i in range(60)]  # 0分から59分まで
        self.minutes_combobox.grid(row=0, column=5)

        ttk.Label(duration_frame, text="秒:").grid(row=0, column=6)
        self.seconds_var = tk.StringVar()
        self.seconds_combobox = ttk.Combobox(duration_frame, textvariable=self.seconds_var, width=5)
        self.seconds_combobox['values'] = [str(i) for i in range(60)]  # 0秒から59秒まで
        self.seconds_combobox.grid(row=0, column=7)

        # インターバル入力フィールドを作成
        ttk.Label(self.root, text="インターバル（秒）:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        self.interval_entry = ttk.Entry(self.root)
        self.interval_entry.grid(row=3, column=1, padx=10, pady=10)

        # 予測開始ボタンを作成
        self.predict_button = ttk.Button(self.root, text="予測開始", command=self.predict)
        self.predict_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        # 出力テキストボックスを作成
        self.output_text = tk.Text(self.root, width=100, height=20)
        self.output_text.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    def predict(self):
        # 以前の出力をクリア
        self.output_text.delete(1.0, tk.END)

        # 入力値を取得
        line1 = self.line1_entry.get()
        line2 = self.line2_entry.get()
        try:
            days = int(self.days_var.get())
            hours = int(self.hours_var.get())
            minutes = int(self.minutes_var.get())
            seconds = int(self.seconds_var.get())
            interval_seconds = int(self.interval_entry.get())
        except ValueError:
            messagebox.showerror("入力エラー", "有効な数字を入力してください。")
            return

        # 入力値を検証
        if not line1 or not line2 or (days == 0 and hours == 0 and minutes == 0 and seconds == 0) or interval_seconds <= 0:
            messagebox.showerror("入力エラー", "有効なTLEデータ、期間、およびインターバルを提供してください。")
            return

        # 合計期間を秒単位で計算
        duration_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds

        # 衛星オブジェクトを作成
        try:
            satellite = Satrec.twoline2rv(line1, line2)
        except Exception as e:
            messagebox.showerror("TLEエラー", f"TLEデータの読み込みに失敗しました: {e}")
            return
        
        start_datetime = datetime.utcnow()

        # 時間ステップを生成
        time_steps = [start_datetime + timedelta(seconds=i) for i in range(0, duration_seconds, interval_seconds)]
        positions = self.calculate_positions(satellite, time_steps)

        # 結果を表示
        self.display_results(positions)

    def calculate_positions(self, satellite, time_steps):
        positions = []
        transformer = Transformer.from_proj(Proj(proj="geocent", ellps="WGS84", datum="WGS84"),
                                            Proj(proj="latlong", datum="WGS84"))
        for step in time_steps:
            jd, fr = jday(step.year, step.month, step.day, step.hour, step.minute, step.second + step.microsecond * 1e-6)
            try:
                e, r, v = satellite.sgp4(jd, fr)
                if e == 0:
                    # ECEF座標を緯度経度高度に変換
                    x, y, z = r
                    lon, lat, alt = transformer.transform(x * 1000, y * 1000, z * 1000, radians=False)
                    positions.append((step, (lat, lon, alt)))
                else:
                    error_message = SGP4_ERRORS.get(e, 'Unknown error')
                    positions.append((step, (None, None, None)))
                    self.output_text.insert(tk.END, f"時間: {step}, 位置: {error_message}\n")
            except Exception as e:
                self.output_text.insert(tk.END, f"時間: {step}, 位置: 計算中にエラーが発生しました: {e}\n")
                positions.append((step, (None, None, None)))
        return positions

    def display_results(self, positions):
        for pos in positions:
            time, (lat, lon, alt) = pos
            if lat is not None:
                self.output_text.insert(tk.END, f"時間: {time}, 緯度: {lat:.6f}, 経度: {lon:.6f}, 高度: {alt / 1000:.2f} km\n")
            else:
                self.output_text.insert(tk.END, f"時間: {time}, 位置: 計算エラー\n")

def main():
    root = tk.Tk()
    app = SatelliteTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
