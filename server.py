from flask import Flask, render_template
import requests
from threading import Thread
from bs4 import BeautifulSoup
import time
import json
import os
app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


def fetch(ll=[], url="https://polcompball.fandom.com/wiki/Category:Characters"):
    print(url)
    r = requests.get(url)
    bs = BeautifulSoup(r.content, "html.parser")
    hrefs = [[a.text, a['href']] for a in bs.find_all('a', {'class': 'category-page__member-link'}, href=True) if len(a.text.split(":"))==1]
    for p in hrefs:
        if p not in ll:
            ll.append(p)
    #open('f.txt', 'w').write("\n".join([a[0] for a in hrefs]))
    try:
        n = bs.find_all('a', {'class': 'category-page__pagination-next wds-button wds-is-secondary'}, href=True)[0]['href']
        return fetch(ll, n)
    except IndexError:
        pass
    return ll


def get_logo(pol, bs):
    try: 
        img = bs.find_all('img', {'class': 'pi-image-thumbnail'})[0]
        return requests.get(img['src']).content
    except IndexError: 
        print("No logo provided for " + pol[0])
    return b''



def get_text(pol, bs):
    
    info = bs.find('div', {'class': 'mw-parser-output'}).text.strip().split("\n\n\n\n\n")[1]
    try:
        reduced = info.split("\n\n\n\n")[1].split("\n\n")[0]
        return reduced 
    except IndexError:
        return info


def get_info(pol):

    url = "https://polcompball.fandom.com"+pol[1]
    # print(url)
    r = requests.get(url)
    bs = BeautifulSoup(r.content, "html.parser")
    img = get_logo(pol, bs)
    try:
        open(os.path.join('static/logo', pol[0]+"_logo.png"), "wb").write(img)
        text = get_text(pol, bs)
        open(os.path.join('static/text', pol[0]+".txt"), "w").write(text)
    except TypeError:
        raise Exception("stop")



def get_info_range(pols, pid):
    print(f"Thread #{pid} doing {len(pols)}")
    for pol in pols:
        get_info(pol)



def pooler(pols, threads=[]):
    global MAX_THREADS
    n = len(pols)//MAX_THREADS # 235
    mod = len(pols)%MAX_THREADS # 1
    if mod == 0:
        for i in range(MAX_THREADS):
            t = Thread(target=get_info_range, args=(pols[n*i:n*(i+1)], i+1))
            t.start()
            threads.append(t)
        return threads
    else:
        t = Thread(target=get_info_range, args=(pols[-mod:], 0))
        t.start()
        threads.append(t)
        return pooler(pols[:-mod], threads=threads)



MAX_THREADS = 30



def work(update=False):
    time.sleep(.1)
    if update:
        POL = sorted(fetch())
        open("pol.json", "w").write(json.dumps(POL))
    else:
        try:
            POL = json.loads(open("pol.json", "r").read())
        except FileNotFoundError:
            raise Exception("File pol.json not found try updating first")
    print(f"There are currently {len(POL)} different political Ideologies on polcompball")
    for t in pooler(POL):
        t.join()
    print("DONE")


t = Thread(target=work, args=(False, ))
t.start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4002, debug=False)

t.join()
