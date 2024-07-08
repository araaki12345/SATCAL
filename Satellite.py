from sgp4.api import Satrec

def validate_tle(line1, line2):
    try:
        # 衛星オブジェクトを作成してTLEをパース
        satellite = Satrec.twoline2rv(line1, line2)
        
        # 離心率の範囲チェック
        if not (0.0 <= satellite.ecco < 1.0):
            return False, "離心率が範囲外です (0.0 <= e < 1.0)"
        
        # 軌道傾斜角の範囲チェック
        if not (0.0 <= satellite.inclo <= 180.0):
            return False, "軌道傾斜角が範囲外です (0.0 <= inclo <= 180.0)"
        
        # 他のチェックを追加することができます
        
        return True, "TLEデータは有効です"
    except Exception as e:
        return False, f"TLEデータのパース中にエラーが発生しました: {e}"

line1 = "1 58400U 23179A   24189.90245992  .00005957  00000-0  26900-3 0  9999"
line2 = "2 58400  97.4012  76.4000 0003640 108.4471 251.7161 15.21338773 34872"

is_valid, message = validate_tle(line1, line2)
print(message)
