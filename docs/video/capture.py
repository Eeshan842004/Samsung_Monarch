import os, json, time
from playwright.sync_api import sync_playwright
URL="https://eeshan842004.github.io/Samsung_Monarch/"
REPO="https://github.com/Eeshan842004/Samsung_Monarch"
EST=os.path.abspath("../../eval/demo/estimated_trajectory.txt")
DSF=1.5
plan={"MH":("Machine Hall 03",420),"V1":("Vicon Room 1-02",210),"M5":("Machine Hall 05",210)}
os.makedirs("cap",exist_ok=True)
meta={}
t0=time.time()
with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome")
    pg=b.new_page(viewport={"width":1920,"height":1080},device_scale_factor=DSF,color_scheme="dark")
    pg.goto(URL,wait_until="networkidle"); pg.wait_for_timeout(1500)
    # remove focus rings / cursor artefacts
    pg.add_style_tag(content="*:focus{outline:none!important}")
    def box(sel): return pg.locator(sel).first.bounding_box()
    sels=["#tabs button","#top","#side","#err","#metrics-card","#play","#scrub","#phase","#tab-own","#mbody","header"]
    meta["boxes"]={s:box(s) for s in sels}
    meta["h"]=pg.evaluate("document.documentElement.scrollHeight")
    pg.screenshot(path="cap/hero.jpg",full_page=True,quality=92)
    for key,(label,n) in plan.items():
        pg.locator("#tabs button",has_text=label).click(); pg.wait_for_timeout(600)
        d=f"cap/{key}"; os.makedirs(d,exist_ok=True)
        for i in range(n):
            v=round(1000*i/(n-1))
            pg.evaluate("v=>{const s=document.getElementById('scrub');s.value=v;s.dispatchEvent(new Event('input'))}",v)
            pg.screenshot(path=f"{d}/{i:04d}.jpg",full_page=True,quality=90)
        meta[key+"_rows"]=pg.locator("#mbody").inner_text()
        print(key,"done",round(time.time()-t0),"s",flush=True)
    # your file
    pg.locator("#tab-own").click(); pg.wait_for_timeout(500)
    pg.screenshot(path="cap/own_empty.jpg",full_page=True,quality=90)
    pg.set_input_files("#fEst",EST); pg.wait_for_timeout(2500)
    d="cap/OW"; os.makedirs(d,exist_ok=True)
    for i in range(150):
        v=round(1000*i/149)
        pg.evaluate("v=>{const s=document.getElementById('scrub');s.value=v;s.dispatchEvent(new Event('input'))}",v)
        pg.screenshot(path=f"{d}/{i:04d}.jpg",full_page=True,quality=90)
    meta["own_rows"]=pg.locator("#mbody").inner_text(); meta["own_msg"]=pg.locator("#msg").inner_text()
    meta["own_boxes"]={s:box(s) for s in ["#own-card","#metrics-card","#top"]}
    # GitHub
    g=b.new_page(viewport={"width":1920,"height":1080},device_scale_factor=DSF,color_scheme="dark")
    g.goto(REPO,wait_until="networkidle"); g.wait_for_timeout(2000)
    g.screenshot(path="cap/gh_repo.jpg",full_page=True,quality=90)
    meta["gh_h"]=g.evaluate("document.documentElement.scrollHeight")
    rt=g.locator("article table").first
    meta["gh_table"]=rt.bounding_box() if rt.count() else None
    meta["gh_readme"]=g.locator("article").first.bounding_box()
    g.goto(REPO+"/actions",wait_until="networkidle"); g.wait_for_timeout(2000)
    g.screenshot(path="cap/gh_actions.jpg",full_page=False,quality=90)
    b.close()
json.dump(meta,open("cap/meta.json","w"),indent=1)
print("all done",round(time.time()-t0),"s")
