git pull
git add .
git commit -m "sneed"
git push

npm install -g sass
apt install ruby-sass
sass ./files/assets/style/transparent.scss ./files/assets/style/transparent_ff66ac.css
sass ./files/assets/style/win98.scss ./files/assets/style/win98_ff66ac.css
sass ./files/assets/style/midnight.scss ./files/assets/style/midnight_ff66ac.css
sass ./files/assets/style/dark.scss ./files/assets/style/dark_ff66ac.css
sass ./files/assets/style/light.scss ./files/assets/style/light_ff66ac.css
sass ./files/assets/style/coffee.scss ./files/assets/style/coffee_ff66ac.css
sass ./files/assets/style/tron.scss ./files/assets/style/tron_ff66ac.css
sass ./files/assets/style/4chan.scss ./files/assets/style/4chan_ff66ac.css
python ./compilecss.py
python3 ./compilecss.py
git add .
git commit -m "css"
git push

cd D:\1
git pull