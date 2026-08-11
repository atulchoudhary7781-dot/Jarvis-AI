import os
from PIL import Image

def find_and_convert():
    # Folder mein PNG dhoondna
    files = [f for f in os.listdir('.') if f.endswith('.png') or f.endswith('.jpg')]
    
    if not files:
        print("❌ Error: Folder mein koi photo (.png ya .jpg) nahi mili!")
        return

    img_name = files[0] # Jo pehli photo milegi use use karega
    print(f"🔄 Processing: {img_name}...")

    try:
        img = Image.open(img_name)
        img = img.convert("RGBA")
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save("jarvis_icon.ico", sizes=sizes)
        print("✅ SUCCESS! 'jarvis_icon.ico' ban gayi hai.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_and_convert()