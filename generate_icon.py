from PIL import Image

# Input and output
INPUT_IMAGE = "ras_logo.png"
OUTPUT_ICON = "ras.ico"

# Recommended Windows icon sizes
ICON_SIZES = [
    (256, 256),
    (128, 128),
    (64, 64),
    (48, 48),
    (32, 32),
    (24, 24),
    (16, 16),
]

def generate_icon():
    img = Image.open(INPUT_IMAGE)

    # Ensure image has alpha channel (transparency)
    img = img.convert("RGBA")

    # Save multi-resolution ICO
    img.save(OUTPUT_ICON, format="ICO", sizes=ICON_SIZES)

    print("✅ Icon generated successfully:", OUTPUT_ICON)


if __name__ == "__main__":
    generate_icon()