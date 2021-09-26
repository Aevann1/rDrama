git pull
git add .
git commit -m "sneed"
git push

npm install -g sass
apt install ruby-sass
sass ./files/assets/css/transparent.scss ./files/assets/css/transparent_ff66ac.css
sass ./files/assets/css/win98.scss ./files/assets/css/win98_ff66ac.css
sass ./files/assets/css/midnight.scss ./files/assets/css/midnight_ff66ac.css
sass ./files/assets/css/dark.scss ./files/assets/css/dark_ff66ac.css
sass ./files/assets/css/light.scss ./files/assets/css/light_ff66ac.css
sass ./files/assets/css/coffee.scss ./files/assets/css/coffee_ff66ac.css
sass ./files/assets/css/tron.scss ./files/assets/css/tron_ff66ac.css
sass ./files/assets/css/4chan.scss ./files/assets/css/4chan_ff66ac.css
python ./compilecss.py
python3 ./compilecss.py
git add .
git commit -m "css"
git push

cd D:\1
git pull