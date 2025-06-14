local args = {...}
if #args < 1 then
  print("Usage: nfp_display <path>")
  return
end

local path = args[1]
local image = paintutils.loadImage(path)
if not image then
  error("Failed to load image: " .. path)
end

local w, h = term.getSize()
local imgW = #image[1]
local imgH = #image
local startX = math.floor((w - imgW) / 2) + 1
local startY = math.floor((h - imgH) / 2) + 1

paintutils.drawImage(image, startX, startY)
