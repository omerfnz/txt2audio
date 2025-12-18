
import librosa
import numpy as np
import soundfile as sf
import os

def analyze_audio(file_path):
    print(f"Analiz ediliyor: {file_path}")
    
    # Sesi yükle
    y, sr = librosa.load(file_path, sr=None)
    
    # 1. Clipping (Kırpılma) Kontrolü
    # Maksimum genlik kontrolü
    max_val = np.abs(y).max()
    clipping_count = np.sum(np.abs(y) >= 0.99)
    print(f"Maksimum Genlik: {max_val:.4f}")
    if clipping_count > 0:
        print(f"UYARI: {clipping_count} adet clipping (kırpılma) noktası tespit edildi.")

    # 2. Ani Değişimler (Glitch/Crackle tespiti)
    dy = np.diff(y)
    max_dy = np.abs(dy).max()
    glitch_threshold = 0.2 # Eşiği düşürdüm (0.5 -> 0.2)
    glitches = np.where(np.abs(dy) > glitch_threshold)[0]
    
    print(f"Maksimum Genlik Değişimi (Delta): {max_dy:.4f}")
    if len(glitches) > 0:
        print(f"TESPİT: {len(glitches)} adet potansiyel ani 'glitch' veya 'click' tespit edildi.")
        for g in glitches[:10]:
            print(f" - Glitch saniyesi: {g/sr:.4f}s")
    
    # 3. Sıfır Seviyesi ve Tekrarlar (Stutter/Mechanical sound)
    # Kısa pencerelerde RMS (Enerji) kontrolü
    hop_length = 256
    rms = librosa.feature.rms(y=y, hop_length=hop_length)
    
    # Enerjideki aşırı düzenli dalgalanmalar mekanik takılmaya işaret edebilir
    rms_diff = np.diff(rms[0])
    print(f"RMS Standart Sapması: {np.std(rms):.6f}")

    # 4. Spektral Düzlük ve Rolloff
    flatness = librosa.feature.spectral_flatness(y=y)
    print(f"Ortalama Spektral Düzlük: {np.mean(flatness):.6f}")
    
    # 5. Öz-ilintili (Autocorrelation) - Takılma/Döngü tespiti
    # Eğer ses belli bir periyotta takılıyorsa (loop), autocorrelation zirve yapar
    r = librosa.autocorrelate(y, max_size=int(sr/2)) # 0.5 saniyeye kadar olan tekrarlar
    peaks = librosa.util.peak_pick(r, pre_max=20, post_max=20, pre_avg=100, post_avg=100, delta=0.5, wait=100)
    if len(peaks) > 5:
        print(f"UYARI: Beklenmedik periyodik tekrarlar (takılan ses) tespit edildi ({len(peaks)} zirve).")

if __name__ == "__main__":
    path = "/home/omer/projects/txt2audio/segment_analysis.wav"
    if os.path.exists(path):
        analyze_audio(path)
    else:
        print(f"Dosya bulunamadı: {path}")
