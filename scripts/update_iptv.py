import gzip
import re
import unicodedata
import xml.etree.ElementTree as ET
import requests

EPG_SOURCES = [
    "https://raw.githubusercontent.com/acidjesuz/EPG/master/guide.xml",
]

# tvg-id de tu M3U -> (nombre visible, logo_url, keywords de búsqueda)
CHANNELS = {
    "AE.lat": ("A&E HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/A%26E_Network_logo.svg/512px-A%26E_Network_logo.svg.png", ["a&e", "ae network"]),
    "AMC.lat": ("AMC", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/AMC_logo_2019.svg/512px-AMC_logo_2019.svg.png", ["amc"]),
    "AMCHD.lat": ("AMC HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/AMC_logo_2019.svg/512px-AMC_logo_2019.svg.png", ["amc"]),
    "ATV.pe": ("ATV", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/ATV_Per%C3%BA_logo.svg/512px-ATV_Per%C3%BA_logo.svg.png", ["atv peru", "atv"]),
    "AXN.lat": ("AXN HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/AXN_logo_2023.svg/512px-AXN_logo_2023.svg.png", ["axn"]),
    "AdultSwim.lat": ("Adult Swim", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Adult_Swim_2023_logo.svg/512px-Adult_Swim_2023_logo.svg.png", ["adult swim"]),
    "AmericaTV.pe": ("América TV HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Am%C3%A9rica_Televisi%C3%B3n_logo.svg/512px-Am%C3%A9rica_Televisi%C3%B3n_logo.svg.png", ["america tv", "america television"]),
    "AnimalPlanet.lat": ("Animal Planet HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Animal_Planet_logo.svg/512px-Animal_Planet_logo.svg.png", ["animal planet"]),
    "BBCNews.uk": ("BBC News", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/BBC_News_2022_%28icon%29.svg/512px-BBC_News_2022_%28icon%29.svg.png", ["bbc news", "bbc world"]),
    "BethelTV.pe": ("Bethel TV", "", ["bethel"]),
    "BabyTV.lat": ("Baby TV", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/BabyTV_logo.svg/512px-BabyTV_logo.svg.png", ["baby tv", "babytv"]),
    "CHV.cl": ("CHV HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Chilevisi%C3%B3n_2020.svg/512px-Chilevisi%C3%B3n_2020.svg.png", ["chilevision", "chv"]),
    "CNNespanol.lat": ("CNN Español", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/CNN_International_logo.svg/512px-CNN_International_logo.svg.png", ["cnn en espanol", "cnn espanol"]),
    "CNNintl.uk": ("CNN International", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/CNN_International_logo.svg/512px-CNN_International_logo.svg.png", ["cnn international"]),
    "CanalN.pe": ("Canal N", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Canal_N_logo.svg/512px-Canal_N_logo.svg.png", ["canal n"]),
    "CartoonNetwork.lat": ("Cartoon Network HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Cartoon_Network_2010_logo.svg/512px-Cartoon_Network_2010_logo.svg.png", ["cartoon network"]),
    "Cartoonito.lat": ("Cartoonito", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Cartoonito_2021_logo.svg/512px-Cartoonito_2021_logo.svg.png", ["cartoonito"]),
    "Cinecanal.lat": ("Cinecanal HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Cinecanal_logo.svg/512px-Cinecanal_logo.svg.png", ["cinecanal"]),
    "Cinemax.lat": ("Cinemax", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Cinemax_logo.svg/512px-Cinemax_logo.svg.png", ["cinemax"]),
    "ComedyCentral.lat": ("Comedy Central HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Comedy_Central_2018.svg/512px-Comedy_Central_2018.svg.png", ["comedy central"]),
    "Daystar.us": ("Daystar", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Daystar_Television_Network_logo.svg/512px-Daystar_Television_Network_logo.svg.png", ["daystar"]),
    "DWespanol.de": ("DW Español", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Deutsche_Welle_symbol_2012.svg/512px-Deutsche_Welle_symbol_2012.svg.png", ["dw espanol", "deutsche welle"]),
    "DePelicula.mx": ("De Película", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/De_Pel%C3%ADcula_logo.svg/512px-De_Pel%C3%ADcula_logo.svg.png", ["de pelicula"]),
    "DirecTV.lat": ("DirecTV", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/DirecTV_logo_2019.svg/512px-DirecTV_logo_2019.svg.png", ["directv"]),
    "DSports.lat": ("DSports", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/DSports_logo.svg/512px-DSports_logo.svg.png", ["dsports", "directv sports"]),
    "DiscoveryChannel.lat": ("Discovery Channel HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Discovery_Channel_%282019%29.svg/512px-Discovery_Channel_%282019%29.svg.png", ["discovery channel"]),
    "DiscoveryKids.lat": ("Discovery Kids HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Discovery_Kids_2016.svg/512px-Discovery_Kids_2016.svg.png", ["discovery kids"]),
    "DiscoveryTheater.lat": ("Discovery Theater HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Discovery_Channel_%282019%29.svg/512px-Discovery_Channel_%282019%29.svg.png", ["discovery theater"]),
    "DisneyChannel.lat": ("Disney HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Disney_Channel_logo_%282014%29.svg/512px-Disney_Channel_logo_%282014%29.svg.png", ["disney channel"]),
    "DisneyJunior.lat": ("Disney Junior", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Disney_Junior_logo_2014.svg/512px-Disney_Junior_logo_2014.svg.png", ["disney junior"]),
    "DistritoComedia.mx": ("Distrito Comedia", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Distrito_Comedia_logo.svg/512px-Distrito_Comedia_logo.svg.png", ["distrito comedia"]),
    "E.lat": ("E! Entertainment TV", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/E%21_logo_2012.svg/512px-E%21_logo_2012.svg.png", ["e entertainment", "e! entertainment"]),
    "ESPN2.lat": ("ESPN 2 HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/ESPN2_logo.svg/512px-ESPN2_logo.svg.png", ["espn 2", "espn2"]),
    "ESPN2b.lat": ("ESPN 2 HD (Op 2)", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/ESPN2_logo.svg/512px-ESPN2_logo.svg.png", ["espn 2", "espn2"]),
    "ESPN3.lat": ("ESPN 3 HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/ESPN3_logo.svg/512px-ESPN3_logo.svg.png", ["espn 3", "espn3"]),
    "ESPN4.lat": ("ESPN 4 HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn 4", "espn4"]),
    "ESPN5.lat": ("ESPN 5 HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn 5", "espn5"]),
    "ESPN6.lat": ("ESPN 6 HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn 6", "espn6"]),
    "ESPN7.lat": ("ESPN 7 HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn 7", "espn7"]),
    "ESPN.lat": ("ESPN HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn"]),
    "ESPNb.lat": ("ESPN HD (Op 2)", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn"]),
    "ESPNc.lat": ("ESPN HD (Op 3)", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn"]),
    "ESPNPremium.ar": ("ESPN Premium HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn premium"]),
    "EWTN.us": ("EWTN", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/EWTN_logo.svg/512px-EWTN_logo.svg.png", ["ewtn"]),
    "ElGourmet.lat": ("El Gourmet HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/El_Gourmet_logo.svg/512px-El_Gourmet_logo.svg.png", ["el gourmet"]),
    "Enlace.lat": ("Enlace", "", ["enlace"]),
    "EuropaEuropa.lat": ("Europa Europa", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Europa_Europa_logo.svg/512px-Europa_Europa_logo.svg.png", ["europa europa"]),
    "ExitosaTV.pe": ("Exitosa TV", "", ["exitosa"]),
    "FMHFamily.lat": ("FMH Family", "", ["fmh family"]),
    "FMHFamilyKids.lat": ("FMH Family Kids", "", ["fmh family kids"]),
    "FMHFamilyMovie.lat": ("FMH Family Movie", "", ["fmh family movie"]),
    "FoxSportsPremium.ar": ("Fox Sports Premium", "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Fox_Sports_logo.svg/512px-Fox_Sports_logo.svg.png", ["fox sports premium"]),
    "FX.lat": ("FX HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/FX_logo.svg/512px-FX_logo.svg.png", ["fx"]),
    "FilmArts.lat": ("Film&Arts", "", ["film&arts", "film and arts"]),
    "FilmArtsb.lat": ("Film&Arts (Op 2)", "", ["film&arts", "film and arts"]),
    "FoodNetwork.lat": ("Food Network", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Food_Network_logo.svg/512px-Food_Network_logo.svg.png", ["food network"]),
    "France24.fr": ("France 24", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/France_24_logo.svg/512px-France_24_logo.svg.png", ["france 24"]),
    "Global.pe": ("Global TV", "", ["global tv", "global"]),
    "GoldenEdge.lat": ("Golden Edge", "", ["golden edge"]),
    "Golden.lat": ("Golden HD", "", ["golden"]),
    "HBOFamily.lat": ("HBO Family HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo family"]),
    "HBO.lat": ("HBO HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo"]),
    "HBOMundi.lat": ("HBO Mundi", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo mundi"]),
    "HBOPlus.lat": ("HBO Plus", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo plus"]),
    "HBOSignature.lat": ("HBO Signature", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo signature"]),
    "HBOExtreme.lat": ("HBO Xtreme HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo xtreme"]),
    "HTV.lat": ("HTV", "", ["htv"]),
    "HTVb.lat": ("HTV (Op 2)", "", ["htv"]),
    "History2.lat": ("History 2", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/History_Channel_logo.svg/512px-History_Channel_logo.svg.png", ["history 2", "h2"]),
    "History.lat": ("History Channel HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/History_Channel_logo.svg/512px-History_Channel_logo.svg.png", ["history"]),
    "HomeHealth.lat": ("Home & Health HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Discovery_Home_%26_Health_logo.svg/512px-Discovery_Home_%26_Health_logo.svg.png", ["home & health", "home and health"]),
    "ID.lat": ("ID HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Investigation_Discovery_logo.svg/512px-Investigation_Discovery_logo.svg.png", ["investigation discovery"]),
    "Karibena.pe": ("Karibeña", "", ["karibena"]),
    "KanalDDrama.lat": ("Kanal D Drama", "", ["kanal d drama"]),
    "L1.pe": ("L1", "", ["liga 1"]),
    "L1Max.pe": ("L1 MAX", "", ["liga 1 max"]),
    "LaRed.cl": ("La Red", "", ["la red"]),
    "LasEstrellas.mx": ("Las Estrellas HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Las_Estrellas_logo.svg/512px-Las_Estrellas_logo.svg.png", ["las estrellas"]),
    "Latina.pe": ("Latina HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Latina_Televisi%C3%B3n_logo.svg/512px-Latina_Televisi%C3%B3n_logo.svg.png", ["latina"]),
    "Lifetime.lat": ("Lifetime", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Lifetime_logo.svg/512px-Lifetime_logo.svg.png", ["lifetime"]),
    "LoveNature.lat": ("Love Nature", "", ["love nature"]),
    "Mega.cl": ("MEGA HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Mega_%28Chile%29_logo.svg/512px-Mega_%28Chile%29_logo.svg.png", ["mega"]),
    "MiMusicaHits.lat": ("Mi Música Hits", "", ["mi musica hits"]),
    "MiMusicaPeru.pe": ("Mi Música Perú", "", ["mi musica peru"]),
    "MTV.lat": ("MTV HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/MTV_Logo_2010.svg/512px-MTV_Logo_2010.svg.png", ["mtv"]),
    "MundoMusica.lat": ("Mundo de la Música", "", ["mundo de la musica"]),
    "MusicaVene.ve": ("Música Vene", "", ["musica vene"]),
    "Megab.cl": ("Mega (Op 2)", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Mega_%28Chile%29_logo.svg/512px-Mega_%28Chile%29_logo.svg.png", ["mega"]),
    "MovistarDeportes.pe": ("Movistar Deportes", "", ["movistar deportes"]),
    "NuevoTiempo.lat": ("Nuevo Tiempo", "", ["nuevo tiempo"]),
    "NatGeo.lat": ("Nat Geo HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/National_Geographic_Channel.svg/512px-National_Geographic_Channel.svg.png", ["national geographic", "nat geo"]),
    "Nick.lat": ("Nick HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Nickelodeon_2009_logo.svg/512px-Nickelodeon_2009_logo.svg.png", ["nickelodeon"]),
    "NickJr.lat": ("Nick Jr.", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Nick_Jr._logo_2009.svg/512px-Nick_Jr._logo_2009.svg.png", ["nick jr"]),
    "NickMusic.lat": ("Nick Music", "", ["nick music"]),
    "NuestraTele.co": ("Nuestra Tele", "", ["nuestra tele"]),
    "OromarTV.ec": ("Oromar TV", "", ["oromar"]),
    "Panamericana.pe": ("Panamericana", "", ["panamericana"]),
    "Pasiones.lat": ("Pasiones HD", "", ["pasiones"]),
    "PlimPlim.ar": ("Plim Plim TV", "", ["plim plim"]),
    "RAIItalia.it": ("RAI Italia", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Rai_logo_2020.svg/512px-Rai_logo_2020.svg.png", ["rai italia"]),
    "RECTV.cl": ("REC TV", "", ["rec tv"]),
    "RPP.pe": ("RPP", "", ["rpp"]),
    "SomosTV.ve": ("Somos TV Venezuela", "", ["somos tv"]),
    "StarChannel.lat": ("Star Channel", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Star_Channel_logo.svg/512px-Star_Channel_logo.svg.png", ["star channel"]),
    "StarChannelHD.lat": ("Star Channel HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Star_Channel_logo.svg/512px-Star_Channel_logo.svg.png", ["star channel"]),
    "Sextreme.lat": ("Sextreme", "", ["sextreme"]),
    "Sony.lat": ("Sony HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Sony_Channel_logo.svg/512px-Sony_Channel_logo.svg.png", ["sony channel"]),
    "SonyMovies.lat": ("Sony Movies HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Sony_Channel_logo.svg/512px-Sony_Channel_logo.svg.png", ["sony movies"]),
    "Space.lat": ("Space HD", "", ["space"]),
    "StingrayConcerts.lat": ("Stingray Concerts HD", "", ["stingray concerts"]),
    "StudioUniversal.lat": ("Studio Universal HD", "", ["studio universal"]),
    "TCM.lat": ("TCM", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/TCM_logo.svg/512px-TCM_logo.svg.png", ["tcm"]),
    "TNT.lat": ("TNT HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/TNT_Logo_2016.svg/512px-TNT_Logo_2016.svg.png", ["tnt"]),
    "TNTNovelas.lat": ("TNT Novelas HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/TNT_Logo_2016.svg/512px-TNT_Logo_2016.svg.png", ["tnt novelas"]),
    "TNTSeries.lat": ("TNT Series HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/TNT_Logo_2016.svg/512px-TNT_Logo_2016.svg.png", ["tnt series"]),
    "TNTSportsPremium.ar": ("TNT Sports Premium HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/TNT_Logo_2016.svg/512px-TNT_Logo_2016.svg.png", ["tnt sports"]),
    "TopLatino.lat": ("Top Latino", "", ["top latino"]),
    "TVAragua.ve": ("TV Aragua", "", ["tv aragua"]),
    "TVPeru.pe": ("TV Perú", "", ["tv peru"]),
    "TVE.es": ("TVE", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/TVE_logo.svg/512px-TVE_logo.svg.png", ["tve"]),
    "TVSMaracay.ve": ("TVS Maracay", "", ["tvs maracay"]),
    "TeenNick.lat": ("TeenNick", "", ["teen nick", "teennick"]),
    "Telefe.ar": ("Telefé", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Telefe_logo_2022.svg/512px-Telefe_logo_2022.svg.png", ["telefe"]),
    "Telemundo.us": ("Telemundo", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Telemundo_logo_2018.svg/512px-Telemundo_logo_2018.svg.png", ["telemundo"]),
    "Tlnovelas.mx": ("Tlnovelas", "", ["tlnovelas"]),
    "Tooncast.lat": ("Tooncast", "", ["tooncast"]),
    "UFC.us": ("UFC", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/UFC_Logo.svg/512px-UFC_Logo.svg.png", ["ufc"]),
    "UniversalChannel.lat": ("Universal Channel HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Universal_TV_logo.svg/512px-Universal_TV_logo.svg.png", ["universal tv", "universal channel"]),
    "USA.us": ("USA Network", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/USA_Network_logo_2016.svg/512px-USA_Network_logo_2016.svg.png", ["usa network"]),
    "VisionMusica.lat": ("Visión Música", "", ["vision musica"]),
    "ViaXEsports.cl": ("Vía X Esports", "", ["via x esports"]),
    "WarnerChannel.lat": ("Warner Channel", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Warner_Channel_logo_%282019%29.svg/512px-Warner_Channel_logo_%282019%29.svg.png", ["warner"]),
    "WarnerChannelHD.lat": ("Warner Channel HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Warner_Channel_logo_%282019%29.svg/512px-Warner_Channel_logo_%282019%29.svg.png", ["warner"]),
    "Willax.pe": ("Willax", "", ["willax"]),
    "FibMusic.lat": ("Fib Music", "", ["fib music"]),
    "FibPeliculas.lat": ("Fib Películas", "", ["fib peliculas"]),
    "VclassicMusica.lat": ("VClassic Música", "", ["vclassic"]),
    "WestTV.lat": ("West TV", "", ["west tv"]),
    "DSportsOp3.lat": ("DSports (Opción 3)", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/DSports_logo.svg/512px-DSports_logo.svg.png", ["dsports"]),
    "TVO.es": ("TVO", "", ["tvo"]),
    "CanalI.ve": ("Canal I", "", ["canal i"]),
    "Globovision.ve": ("Globovisión", "", ["globovision"]),
    "TLT.ve": ("TLT", "", ["tlt", "la tele tuya"]),
    "Venevision.ve": ("Venevisión", "", ["venevision"]),
    "Meridiano.ve": ("Meridiano", "", ["meridiano"]),
    "Meridiano2.ve": ("Meridiano 2", "", ["meridiano"]),
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

    for tvg_id, (display_name, logo_url, keywords) in CHANNELS.items():
        ch_el = ET.SubElement(root, "channel", attrib={"id": tvg_id})
        dn = ET.SubElement(ch_el, "display-name")
        dn.text = display_name
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
                    "channel": tvg_id,
                })
                for child in p:
                    new_p.append(child)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print("epg.xml generado correctamente.")

if __name__ == "__main__":
    build_epg()
