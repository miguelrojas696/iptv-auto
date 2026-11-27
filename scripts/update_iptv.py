import gzip
import re
import unicodedata
import xml.etree.ElementTree as ET
import requests

# Fuentes XMLTV abiertas para Latinoamérica / España / EE.UU.
EPG_SOURCES = [
    "https://raw.githubusercontent.com/acidjesuz/EPG/master/guide.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/sites/mi.tv/mi.tv_pe.channels.xml",
]

# Canales limpios -> (URL del logo, palabras clave de búsqueda en EPG)
CHANNELS = {
    "A&E HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/A%26E_Network_logo.svg/512px-A%26E_Network_logo.svg.png", ["a&e", "ae"]),
    "AMC": ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/AMC_logo_2019.svg/512px-AMC_logo_2019.svg.png", ["amc"]),
    "AMC HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/AMC_logo_2019.svg/512px-AMC_logo_2019.svg.png", ["amc"]),
    "ATV": ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/ATV_Per%C3%BA_logo.svg/512px-ATV_Per%C3%BA_logo.svg.png", ["atv"]),
    "AXN HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/AXN_logo_2023.svg/512px-AXN_logo_2023.svg.png", ["axn"]),
    "Adult Swim": ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Adult_Swim_2023_logo.svg/512px-Adult_Swim_2023_logo.svg.png", ["adult swim"]),
    "América TV HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Am%C3%A9rica_Televisi%C3%B3n_logo.svg/512px-Am%C3%A9rica_Televisi%C3%B3n_logo.svg.png", ["america tv", "america television"]),
    "Animal Planet HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Animal_Planet_logo.svg/512px-Animal_Planet_logo.svg.png", ["animal planet"]),
    "BBC News": ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/BBC_News_2022_%28icon%29.svg/512px-BBC_News_2022_%28icon%29.svg.png", ["bbc news", "bbc world"]),
    "Bethel TV": ("", ["bethel"]),
    "Baby TV": ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/BabyTV_logo.svg/512px-BabyTV_logo.svg.png", ["baby tv", "babytv"]),
    "CHV HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Chilevisi%C3%B3n_2020.svg/512px-Chilevisi%C3%B3n_2020.svg.png", ["chilevision", "chv"]),
    "CNN Español": ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/CNN_International_logo.svg/512px-CNN_International_logo.svg.png", ["cnn en espanol", "cnn espanol"]),
    "CNN International": ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/CNN_International_logo.svg/512px-CNN_International_logo.svg.png", ["cnn international"]),
    "Canal N": ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Canal_N_logo.svg/512px-Canal_N_logo.svg.png", ["canal n"]),
    "Cartoon Network HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Cartoon_Network_2010_logo.svg/512px-Cartoon_Network_2010_logo.svg.png", ["cartoon network"]),
    "Cartoonito": ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Cartoonito_2021_logo.svg/512px-Cartoonito_2021_logo.svg.png", ["cartoonito"]),
    "Cinecanal HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Cinecanal_logo.svg/512px-Cinecanal_logo.svg.png", ["cinecanal"]),
    "Cinemax": ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Cinemax_logo.svg/512px-Cinemax_logo.svg.png", ["cinemax"]),
    "Comedy Central HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Comedy_Central_2018.svg/512px-Comedy_Central_2018.svg.png", ["comedy central"]),
    "Daystar": ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Daystar_Television_Network_logo.svg/512px-Daystar_Television_Network_logo.svg.png", ["daystar"]),
    "DW Español": ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Deutsche_Welle_symbol_2012.svg/512px-Deutsche_Welle_symbol_2012.svg.png", ["dw espanol", "deutsche welle"]),
    "De Película": ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/De_Pel%C3%ADcula_logo.svg/512px-De_Pel%C3%ADcula_logo.svg.png", ["de pelicula"]),
    "DirecTV": ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/DirecTV_logo_2019.svg/512px-DirecTV_logo_2019.svg.png", ["directv"]),
    "DSports": ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/DSports_logo.svg/512px-DSports_logo.svg.png", ["dsports", "directv sports"]),
    "Discovery Channel HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Discovery_Channel_%282019%29.svg/512px-Discovery_Channel_%282019%29.svg.png", ["discovery channel"]),
    "Discovery Kids HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Discovery_Kids_2016.svg/512px-Discovery_Kids_2016.svg.png", ["discovery kids"]),
    "Discovery Theater HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Discovery_Channel_%282019%29.svg/512px-Discovery_Channel_%282019%29.svg.png", ["discovery theater"]),
    "Disney HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Disney_Channel_logo_%282014%29.svg/512px-Disney_Channel_logo_%282014%29.svg.png", ["disney channel"]),
    "Disney Junior": ("https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Disney_Junior_logo_2014.svg/512px-Disney_Junior_logo_2014.svg.png", ["disney junior"]),
    "Distrito Comedia": ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Distrito_Comedia_logo.svg/512px-Distrito_Comedia_logo.svg.png", ["distrito comedia"]),
    "E! Entertainment TV": ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/E%21_logo_2012.svg/512px-E%21_logo_2012.svg.png", ["e! entertainment", "e entertainment"]),
    "ESPN 2 HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/ESPN2_logo.svg/512px-ESPN2_logo.svg.png", ["espn 2", "espn2"]),
    "ESPN 3 HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/ESPN3_logo.svg/512px-ESPN3_logo.svg.png", ["espn 3", "espn3"]),
    "ESPN 4 HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn 4", "espn4"]),
    "ESPN 5 HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn 5", "espn5"]),
    "ESPN 6 HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn 6", "espn6"]),
    "ESPN 7 HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn 7", "espn7"]),
    "ESPN HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn"]),
    "ESPN Premium HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn premium"]),
    "EWTN": ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/EWTN_logo.svg/512px-EWTN_logo.svg.png", ["ewtn"]),
    "El Gourmet HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/El_Gourmet_logo.svg/512px-El_Gourmet_logo.svg.png", ["el gourmet"]),
    "Enlace": ("", ["enlace"]),
    "Europa Europa": ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Europa_Europa_logo.svg/512px-Europa_Europa_logo.svg.png", ["europa europa"]),
    "Exitosa TV": ("", ["exitosa"]),
    "FMH Family": ("", ["fmh family"]),
    "FMH Family Kids": ("", ["fmh family kids"]),
    "FMH Family Movie": ("", ["fmh family movie"]),
    "Fox Sports Premium": ("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Fox_Sports_logo.svg/512px-Fox_Sports_logo.svg.png", ["fox sports premium"]),
    "FX HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/FX_logo.svg/512px-FX_logo.svg.png", ["fx"]),
    "Film&Arts": ("", ["film&arts", "film and arts"]),
    "Food Network": ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Food_Network_logo.svg/512px-Food_Network_logo.svg.png", ["food network"]),
    "France 24": ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/France_24_logo.svg/512px-France_24_logo.svg.png", ["france 24"]),
    "Global TV": ("", ["global"]),
    "Golden Edge": ("", ["golden edge"]),
    "Golden HD": ("", ["golden"]),
    "HBO Family HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo family"]),
    "HBO HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo"]),
    "HBO Mundi": ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo mundi"]),
    "HBO Plus": ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo plus"]),
    "HBO Signature": ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo signature"]),
    "HBO Xtreme HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo xtreme"]),
    "HTV": ("", ["htv"]),
    "History 2": ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/History_Channel_logo.svg/512px-History_Channel_logo.svg.png", ["history 2", "h2"]),
    "History Channel HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/History_Channel_logo.svg/512px-History_Channel_logo.svg.png", ["history"]),
    "Home & Health HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Discovery_Home_%26_Health_logo.svg/512px-Discovery_Home_%26_Health_logo.svg.png", ["home & health", "home and health"]),
    "ID HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Investigation_Discovery_logo.svg/512px-Investigation_Discovery_logo.svg.png", ["investigation discovery", "id"]),
    "Karibeña": ("", ["karibena"]),
    "Kanal D Drama": ("", ["kanal d drama"]),
    "L1": ("", ["liga 1", "l1"]),
    "L1 MAX": ("", ["liga 1 max", "l1 max"]),
    "La Red": ("", ["la red"]),
    "Las Estrellas HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Las_Estrellas_logo.svg/512px-Las_Estrellas_logo.svg.png", ["las estrellas"]),
    "Latina HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Latina_Televisi%C3%B3n_logo.svg/512px-Latina_Televisi%C3%B3n_logo.svg.png", ["latina"]),
    "Lifetime": ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Lifetime_logo.svg/512px-Lifetime_logo.svg.png", ["lifetime"]),
    "Love Nature": ("", ["love nature"]),
    "MEGA HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Mega_%28Chile%29_logo.svg/512px-Mega_%28Chile%29_logo.svg.png", ["mega"]),
    "Mi Música Hits": ("", ["mi musica hits"]),
    "Mi Música Perú": ("", ["mi musica peru"]),
    "MTV HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/MTV_Logo_2010.svg/512px-MTV_Logo_2010.svg.png", ["mtv"]),
    "Mundo de la Música": ("", ["mundo de la musica"]),
    "Música Vene": ("", ["musica vene"]),
    "Movistar Deportes": ("", ["movistar deportes"]),
    "Nuevo Tiempo": ("", ["nuevo tiempo"]),
    "Nat Geo HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/National_Geographic_Channel.svg/512px-National_Geographic_Channel.svg.png", ["national geographic", "nat geo"]),
    "Nick HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Nickelodeon_2009_logo.svg/512px-Nickelodeon_2009_logo.svg.png", ["nickelodeon", "nick"]),
    "Nick Jr.": ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Nick_Jr._logo_2009.svg/512px-Nick_Jr._logo_2009.svg.png", ["nick jr"]),
    "Nick Music": ("", ["nick music"]),
    "Nuestra Tele": ("", ["nuestra tele"]),
    "Oromar TV": ("", ["oromar"]),
    "Panamericana": ("", ["panamericana"]),
    "Pasiones HD": ("", ["pasiones"]),
    "Plim Plim TV": ("", ["plim plim"]),
    "RAI Italia": ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Rai_logo_2020.svg/512px-Rai_logo_2020.svg.png", ["rai italia"]),
    "REC TV": ("", ["rec tv"]),
    "RPP": ("", ["rpp"]),
    "Somos TV Venezuela": ("", ["somos tv"]),
    "Star Channel": ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Star_Channel_logo.svg/512px-Star_Channel_logo.svg.png", ["star channel"]),
    "Star Channel HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Star_Channel_logo.svg/512px-Star_Channel_logo.svg.png", ["star channel"]),
    "Sextreme": ("", ["sextreme"]),
    "Sony HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Sony_Channel_logo.svg/512px-Sony_Channel_logo.svg.png", ["sony channel", "sony"]),
    "Sony Movies HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Sony_Channel_logo.svg/512px-Sony_Channel_logo.svg.png", ["sony movies"]),
    "Space HD": ("", ["space"]),
    "Stingray Concerts HD": ("", ["stingray concerts"]),
    "Studio Universal HD": ("", ["studio universal"]),
    "TCM": ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/TCM_logo.svg/512px-TCM_logo.svg.png", ["tcm"]),
    "TNT HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/TNT_Logo_2016.svg/512px-TNT_Logo_2016.svg.png", ["tnt"]),
    "TNT Novelas HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/TNT_Logo_2016.svg/512px-TNT_Logo_2016.svg.png", ["tnt novelas"]),
    "TNT Series HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/TNT_Logo_2016.svg/512px-TNT_Logo_2016.svg.png", ["tnt series"]),
    "TNT Sports Premium HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/TNT_Logo_2016.svg/512px-TNT_Logo_2016.svg.png", ["tnt sports"]),
    "Top Latino": ("", ["top latino"]),
    "TV Aragua": ("", ["tv aragua"]),
    "TV Perú": ("", ["tv peru"]),
    "TVE": ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/TVE_logo.svg/512px-TVE_logo.svg.png", ["tve"]),
    "TVS Maracay": ("", ["tvs"]),
    "TeenNick": ("", ["teen nick", "teennick"]),
    "Telefé": ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Telefe_logo_2022.svg/512px-Telefe_logo_2022.svg.png", ["telefe"]),
    "Telemundo": ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Telemundo_logo_2018.svg/512px-Telemundo_logo_2018.svg.png", ["telemundo"]),
    "Tlnovelas": ("", ["tlnovelas"]),
    "Tooncast": ("", ["tooncast"]),
    "UFC": ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/UFC_Logo.svg/512px-UFC_Logo.svg.png", ["ufc"]),
    "Universal Channel HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Universal_TV_logo.svg/512px-Universal_TV_logo.svg.png", ["universal tv", "universal channel"]),
    "USA Network": ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/USA_Network_logo_2016.svg/512px-USA_Network_logo_2016.svg.png", ["usa network", "usa"]),
    "Visión Música": ("", ["vision musica"]),
    "Vía X Esports": ("", ["via x esports"]),
    "Warner Channel": ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Warner_Channel_logo_%282019%29.svg/512px-Warner_Channel_logo_%282019%29.svg.png", ["warner"]),
    "Warner Channel HD": ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Warner_Channel_logo_%282019%29.svg/512px-Warner_Channel_logo_%282019%29.svg.png", ["warner"]),
    "Willax": ("", ["willax"]),
    "Fib Music": ("", ["fib music"]),
    "Fib Películas": ("", ["fib peliculas"]),
    "VClassic Música": ("", ["vclassic"]),
    "West TV": ("", ["west tv"]),
    "DSports (Opción 3)": ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/DSports_logo.svg/512px-DSports_logo.svg.png", ["dsports"]),
    "TVO": ("", ["tvo"]),
    "Canal I": ("", ["canal i"]),
    "Globovisión": ("", ["globovision"]),
    "TLT": ("", ["tlt", "la tele tuya"]),
    "Venevisión": ("", ["venevision"]),
    "Meridiano": ("", ["meridiano"]),
    "Meridiano 2": ("", ["meridiano"]),
}

def norm(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()

def fetch_xml(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = gzip.decompress(r.content) if url.endswith(".gz") else r.content
    return ET.fromstring(data)

def build_epg():
    root = ET.Element("tv", attrib={"generator-info-name": "miguelrojas696-iptv-epg"})
    source_channels = {}
    source_programmes = {}

    for url in EPG_SOURCES:
        try:
            src = fetch_xml(url)
            for ch in src.findall("channel"):
                cid = ch.attrib.get("id", "")
                names = [norm(d.text) for d in ch.findall("display-name") if d.text]
                if cid:
                    source_channels[cid] = names
            for prog in src.findall("programme"):
                cid = prog.attrib.get("channel", "")
                if cid:
                    source_programmes.setdefault(cid, []).append(prog)
        except Exception as e:
            print(f"Aviso con fuente {url}: {e}")

    for ch_name, (logo_url, keywords) in CHANNELS.items():
        ch_el = ET.SubElement(root, "channel", attrib={"id": ch_name})
        dn = ET.SubElement(ch_el, "display-name")
        dn.text = ch_name
        if logo_url:
            ET.SubElement(ch_el, "icon", attrib={"src": logo_url})

        matched_cid = None
        for cid, names in source_channels.items():
            if any(kw == n or kw in n for kw in keywords for n in names):
                matched_cid = cid
                break

        if matched_cid and matched_cid in source_programmes:
            for p in source_programmes[matched_cid]:
                new_p = ET.SubElement(root, "programme", attrib={
                    "start": p.attrib.get("start", ""),
                    "stop": p.attrib.get("stop", ""),
                    "channel": ch_name,
                })
                for child in p:
                    new_p.append(child)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print("epg.xml generado correctamente.")

if __name__ == "__main__":
    build_epg()
