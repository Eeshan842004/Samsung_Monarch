import json
from playwright.sync_api import sync_playwright
REPO="https://github.com/Eeshan842004/Samsung_Monarch"
meta=json.load(open("cap/meta.json"))
with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome")
    g=b.new_page(viewport={"width":1920,"height":1080},device_scale_factor=1.5,color_scheme="dark")
    g.goto(REPO,wait_until="load",timeout=90000); g.wait_for_timeout(5000)
    g.screenshot(path="cap/gh_repo.jpg",full_page=True,quality=90)
    rt=g.locator("article table").first
    meta["gh_table"]=rt.bounding_box()
    meta["gh_badge"]=g.locator("article img[alt=tests]").first.bounding_box()
    meta["gh_public"]=g.get_by_text("Public",exact=True).first.bounding_box()
    g.goto(REPO+"/actions",wait_until="load",timeout=90000); g.wait_for_timeout(4000)
    g.screenshot(path="cap/gh_actions.jpg",quality=90)
    b.close()
json.dump(meta,open("cap/meta.json","w"),indent=1)
print(meta["gh_table"],meta["gh_badge"],meta["gh_public"])
