for theme in ['transparent', 'win98', 'midnight', 'dark', 'light', 'coffee', 'tron', '4chan']:
    with open(f"./files/assets/style/{theme}_ff66ac.css", encoding='utf-8') as t:
        text = t.read()
        for color in ['ff66ac','805ad5','62ca56','38a169','80ffff','2a96f3','62ca56','eb4963','ff0000','f39731','30409f','3e98a7','e4432d','7b9ae4','ec72de','7f8fa6', 'f8db58']:
            newtext = text.replace("ff66ac", color).replace("ff4097", color).replace("ff1a83", color).replace("ff3390", color).replace("rgba(255, 102, 172, 0.25)", color)
            with open(f"./files/assets/style/{theme}_{color}.css", encoding='utf-8', mode='w') as nt:
                nt.write(newtext)