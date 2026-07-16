import cv2
path = "icon/search.png"
output = "icon/search-1.png"
threshold = 175

img = cv2.imread(path, cv2.IMREAD_COLOR)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
b, g, r = cv2.split(img)
rgba = cv2.merge([b, g, r, mask])
cv2.imwrite(output, rgba)
print(f"✅ 已保存透明背景图: {output}")


