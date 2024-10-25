fetch hackernews stories locally

apply whitelist and blacklist

save story basic details locally

cache content for 24 hours

list interesting stories as a short podcast

fetch actual urls, save locally

extract main text



conda create -n hnlocal -y
conda activate hnlocal
pip install -r .\requirements.txt

usage

open two terminals

fetch results
python .\hn_topnews_fetch.py

flask app 



todo
whitelist and blacklist
user agent from txt file instead of hardcoded
can downloads be paralelized
better flask ui
pinokio
can each day database kept seperate
can update be performed from webui
show extracted content, show AI summary, notebooklm version of content
github
search hn via https://hn.algolia.com/?q=llama



