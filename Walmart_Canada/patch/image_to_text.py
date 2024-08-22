from PIL import Image
import pytesseract

def remove_empty_lines(text):
    return '\n'.join(line for line in text.splitlines() if line.strip())

image_path = 'label2.png'
img = Image.open(image_path)
text = pytesseract.image_to_string(img)
text = remove_empty_lines(text)
print(text)

