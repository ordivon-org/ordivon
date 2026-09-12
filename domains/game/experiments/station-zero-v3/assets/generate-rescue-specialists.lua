local output = app.params["output"] or "assets/station-zero-v3/rescue-specialists.aseprite"
local sprite = Sprite(72, 24, ColorMode.RGB)
sprite.filename = output
local layer = sprite.layers[1]
layer.name = "specialist-tokens"
local image = sprite.cels[1].image

local function rgba(r,g,b,a)
  return app.pixelColor.rgba(r,g,b,a or 255)
end

local transparent = rgba(0,0,0,0)
local ink = rgba(8,16,24,255)
local pale = rgba(221,235,239,255)
local engineer = rgba(105,224,194,255)
local medic = rgba(138,168,255,255)
local security = rgba(255,197,102,255)
local shadow = rgba(48,63,79,255)
image:clear(transparent)

local function px(x,y,c)
  if x >= 0 and x < image.width and y >= 0 and y < image.height then image:drawPixel(x,y,c) end
end

local function rect(x,y,w,h,c)
  for yy=y,y+h-1 do for xx=x,x+w-1 do px(xx,yy,c) end end
end

local function hline(x,y,w,c) rect(x,y,w,1,c) end
local function vline(x,y,h,c) rect(x,y,1,h,c) end

local function frameBase(o, accent)
  -- compact dark backing, deliberately not a filled square so silhouettes survive grayscale
  hline(o+5, 20, 14, shadow)
  hline(o+6, 21, 12, ink)
  px(o+4,19,accent); px(o+19,19,accent)
end

-- Engineer: squared helmet + side-mounted tool silhouette
local o=0
frameBase(o, engineer)
rect(o+5,5,14,10,ink)
rect(o+6,4,12,1,engineer)
vline(o+5,6,8,engineer); vline(o+18,6,8,engineer)
hline(o+7,8,10,2,engineer)
rect(o+8,10,8,4,pale)
rect(o+7,15,10,4,ink)
hline(o+8,15,8,engineer)
-- wrench/tool on right edge
vline(o+20,7,9,engineer); px(o+19,6,engineer); px(o+21,6,engineer); px(o+19,16,engineer); px(o+21,16,engineer)

-- Medic: narrower helmet + unmistakable cross and side medical pack
local m=24
frameBase(m, medic)
rect(m+6,5,12,11,ink)
px(m+7,4,medic); hline(m+8,3,8,medic); px(m+16,4,medic)
vline(m+6,6,8,medic); vline(m+17,6,8,medic)
rect(m+8,7,8,7,pale)
rect(m+11,7,2,7,medic); rect(m+9,9,6,3,medic)
rect(m+7,16,10,3,ink); hline(m+8,16,8,medic)
rect(m+18,11,3,6,medic); px(m+19,10,medic)

-- Security: shield silhouette with pointed lower edge and visor bar
local s=48
frameBase(s, security)
hline(s+6,5,12,security)
vline(s+5,6,8,security); vline(s+18,6,8,security)
hline(s+6,14,12,security)
rect(s+6,6,12,8,ink)
hline(s+8,8,8,2,security)
rect(s+9,10,6,3,pale)
-- shield body / distinct taper
hline(s+6,16,12,security)
hline(s+7,17,10,security)
hline(s+8,18,8,security)
hline(s+9,19,6,security)
hline(s+10,20,4,security)
hline(s+11,21,2,security)
vline(s+11,16,5,ink); vline(s+12,16,5,ink)

sprite:saveAs(output)
