import pygame
import threading

num_wav = "sound\\metan_num.wav"
providing_wav = "sound\\metan_providing.wav"

pygame.mixer.init()

# スレッド排他制御用のロックを作成
lock = threading.Lock()

def play_sound(providing_num:int):
    "引数で指定した番号を呼び出す音声を再生"
    sound_files = [num_wav, f"sound\\metan_{str(providing_num)}.wav", providing_wav]
    sounds = [pygame.mixer.Sound(file) for file in sound_files]
    for sound in sounds:
        sound.play()
        while pygame.mixer.get_busy():
            pygame.time.wait(100)

# 音声再生を別スレッドで開始
def play_sound_thread(providing_num:int):
    """音声再生を別スレッドで実行し、同時に並列実行されないように制御"""
    def sound_with_lock():
        with lock:
            play_sound(providing_num)
    
    thread = threading.Thread(target=sound_with_lock)
    thread.start()

if __name__ == "__main__":
    play_sound_thread("1")
    play_sound_thread("2")