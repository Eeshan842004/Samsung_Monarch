"""Compose 1920x1080 frames: content (1700x956) on navy, caption strip below."""
from PIL import Image, ImageDraw, ImageFont
import textwrap
W,H=1920,1080; BG=(10,14,26); INK=(232,237,245); MUTE=(154,167,180); CY=(56,189,248)
FB=ImageFont.truetype("/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf",34)
FS=ImageFont.truetype("/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf",22)
def frame(content, caption, step=None):
    im=Image.new("RGB",(W,H),BG)
    c=content if isinstance(content,Image.Image) else Image.open(content)
    c=c.convert("RGB").resize((1700,956)); im.paste(c,(110,8))
    d=ImageDraw.Draw(im)
    lines=textwrap.wrap(caption,width=82)[:2]
    y=972 if len(lines)>1 else 990
    for ln in lines:
        w=d.textlength(ln,font=FB); d.text(((W-w)/2,y),ln,font=FB,fill=INK); y+=42
    d.text((24,1040),"Team MONARCH  ·  VIT Vellore",font=FS,fill=MUTE)
    if step: d.text((W-24-d.textlength(step,font=FS),1040),step,font=FS,fill=CY)
    return im
