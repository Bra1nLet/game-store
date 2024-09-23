from PIL import Image

image = Image.open('description.png').resize((640, 360))
image.save('description.png')