import argparse
import soundfile as sf
import numpy as np

MORSE_CODE_DICT = {'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
                   'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
                   'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
                   'Y': '-.--', 'Z': '--..', '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
                   '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----', ', ': '--..--', '.': '.-.-.-',
                   '?': '..--..', '/': '-..-.', '-': '-....-', '(': '-.--.', ')': '-.--.-'}

INVERTED_MORSE_CODE_DICT = {v: k for k, v in MORSE_CODE_DICT.items()}

parser = argparse.ArgumentParser(description='Morse code to ASCII.')
parser.add_argument('-i', '--input', type=str, help='WAV file path', required=True)

args = parser.parse_args()

input_path = args.input

data, samplerate = sf.read(input_path)

silence_limit = 0.001
blocksize = int(samplerate // 200)  # 1/200th of second
overlap = int(blocksize // 2)

# Split the audio wave to blocks and calculate mean value of each chunk
mean_blocks = [np.mean(block) for block in sf.blocks(input_path, blocksize=blocksize, overlap=overlap)]

# Iterate over each block and check if the mean value of each pitch is smaller than the silence limit. Store long
# consecutive silences to rms_silence_length array as tuples of (silence start index, silence length, "SILENCE) and
# consecutive sounds to rms_sound_length as tuples of (sound start index, sound length, "SOUND")
silence_length = 0
sound_length = 0
consecutive_blocks = []

for index, pitch in enumerate(mean_blocks):
    # In case of "sound block"
    if abs(pitch) > silence_limit:
        sound_length += 1

        if silence_length > 10:
            # Calculate the original index by multiplying both values by (blocksize - overlap) so we "re-expand" the
            # block indexes and can map the blocks to original data
            consecutive_blocks.append(
                [(index - silence_length) * (blocksize - overlap),
                 silence_length * (blocksize - overlap), "SILENCE"]
            )
            silence_length = 0

    # In case of "silence block"
    else:
        silence_length += 1

        if sound_length > 10:
            consecutive_blocks.append(
                [(index - sound_length) * (blocksize - overlap),
                 sound_length * (blocksize - overlap), "SOUND"]
            )
            sound_length = 0

# Merge all consecutive blocks, so we always have alteration between silence and sound
merged_blocks = []

for block in consecutive_blocks:
    # Just add the first block
    if len(merged_blocks) == 0:
        merged_blocks.append(block)
    else:
        block_type = block[2]
        # If the merged blocks last block is the same type, we have two consecutive same type blocks we can merge
        if merged_blocks[-1][2] == block_type:
            # Add the current blocks length to the merge blocks last element's length
            merged_blocks[-1][1] = merged_blocks[-1][1] + block[1]
        else:
            merged_blocks.append(block)

words = []
current_word = []

for block in merged_blocks:
    if block[2] == 'SILENCE':
        if block[1] > 7000 and len(current_word) != 0:
            words.append("".join(current_word))
            current_word = []
        # In case we had a long silence, let's add space to separate letters
        if block[1] > 15000:
            words.append(" ")
    else:
        if block[1] > 5000:
            current_word.append("-")
        else:
            current_word.append(".")

ascii_conversion = []

for string in words:
    if string == ' ':
        ascii_conversion.append(" ")
    elif string in INVERTED_MORSE_CODE_DICT:
        ascii_conversion.append(INVERTED_MORSE_CODE_DICT[string])
    else:
        print(f"Could not find {string} from dict")

print(f"Morse code message: {''.join(ascii_conversion)}")