import pygame

def play_sound(sound_file):
    pygame.init()
    pygame.mixer.init()
    sound = pygame.mixer.Sound(sound_file)
    sound.play()
    while pygame.mixer.get_busy():  # Wait for the sound to finish playing
        pygame.time.Clock().tick(10)

# Replace 'your_sound_file.wav' with the path to your sound file
# play_sound('speech.mp3')
# play_sound("airplane.mp4") # DOESN"T WORK 