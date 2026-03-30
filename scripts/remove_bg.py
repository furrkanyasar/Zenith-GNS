from PIL import Image, ImageOps

def make_transparent(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    
    # Process each pixel
    datas = img.getdata()
    newData = []
    width, height = img.size
    
    for i, item in enumerate(datas):
        x = i % width
        y = i // width
        
        # 1. Remove the Gemini watermark (bottom right corner)
        # Adjusted area to 140x140 to be even safer for the cap
        if x > width - 140 and y > height - 140:
            newData.append((0, 0, 0, 0))
            continue

        # 2. Transparecy for dark background
        if item[0] < 50 and item[1] < 50 and item[2] < 50:
            newData.append((0, 0, 0, 0)) # Fully transparent
        else:
            newData.append(item)
            
    img.putdata(newData)
    img.save(output_path, "PNG")
    print(f"Saved transparent logo to {output_path}")

if __name__ == "__main__":
    make_transparent("assets/splash.jpg", "assets/splash_transparent.png")
