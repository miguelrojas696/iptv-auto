import gzip
import io
import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import requests

EPG_SOURCES = [
    "https://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz",
]

# tvg-id de tu M3U -> (nombre visible, logo_url, keywords de búsqueda)
CHANNELS = {
    "ESPN2.lat": ("ESPN 2 HD", "", ["espn 2", "espn2"]),
    "ESPN2b.lat": ("ESPN 2 HD (Op. 2)", "", ["espn 2", "espn2"]),
    "ESPN3.lat": ("ESPN 3 HD", "", ["espn 3", "espn3"]),
    "ESPN4.lat": ("ESPN 4 HD", "", ["espn 4", "espn4"]),
    "ESPN5.lat": ("ESPN 5 HD", "", ["espn 5", "espn5"]),
    "ESPN6.lat": ("ESPN 6 HD", "", ["espn 6", "espn6"]),
    "ESPN7.lat": ("ESPN 7 HD", "", ["espn 7", "espn7"]),
    "ESPN.lat": ("ESPN HD", "", ["espn"]),
    "ESPNb.lat": ("ESPN HD (Op. 2)", "", ["espn"]),
    "ESPNc.lat": ("ESPN HD (Op. 3)", "", ["espn"]),
    "ESPNPremium.ar": ("ESPN Premium HD", "", ["espn premium"]),
    "FoxSportsPremium.ar": ("Fox Sports Premium", "", ["fox sports premium"]),
    "DSports.lat": ("DSports", "", ["dsports", "directv sports"]),
    "L1.pe": ("L1", "", ["liga 1"]),
    "L1Max.pe": ("L1 MAX", "", ["liga 1 max"]),
    "MovistarDeportes.pe": ("Movistar Deportes", "", ["movistar deportes"]),
    "TNTSportsPremium.ar": ("TNT Sports Premium HD", "", ["tnt sports"]),
    "UFC.us": ("UFC", "", ["ufc"]),
    "ViaXEsports.cl": ("Vía X Esports", "", ["via x esports"]),
    "AMCHD.lat": ("AMC HD", "", ["amc"]),
    "Cinecanal.lat": ("Cinecanal HD", "", ["cinecanal"]),
    "Cinemax.lat": ("Cinemax", "", ["cinemax"]),
    "DePelicula.mx": ("De Película", "", ["de pelicula"]),
    "FMHFamilyMovie.lat": ("FMH Family Movie", "", ["fmh family movie"]),
    "GoldenEdge.lat": ("Golden Edge", "", ["golden edge"]),
    "Golden.lat": ("Golden HD", "", ["golden"]),
    "HBOFamily.lat": ("HBO Family HD", "", ["hbo family"]),
    "HBO.lat": ("HBO HD", "", ["hbo"]),
    "HBOMundi.lat": ("HBO Mundi", "", ["hbo mundi"]),
    "HBOPlus.lat": ("HBO Plus", "", ["hbo plus"]),
    "HBOSignature.lat": ("HBO Signature", "", ["hbo signature"]),
    "HBOExtreme.lat": ("HBO Xtreme HD", "", ["hbo xtreme"]),
    "SonyMovies.lat": ("Sony Movies", "", ["sony movies"]),
    "Space.lat": ("Space HD", "", ["space"]),
    "StudioUniversal.lat": ("Studio Universal HD", "", ["studio universal"]),
    "TCM.lat": ("TCM", "", ["tcm"]),
    "TNT.lat": ("TNT HD", "", ["tnt"]),
    "FibPeliculas.lat": ("Fib Películas", "", ["fib peliculas"]),
    "KanalDDrama.lat": ("Kanal D Drama", "", ["kanal d drama"]),
    "Pasiones.lat": ("Pasiones HD", "", ["pasiones"]),
    "TNTNovelas.lat": ("TNT Novelas HD", "", ["tnt novelas"]),
    "Telemundo.us": ("Telemundo", "", ["telemundo"]),
    "Tlnovelas.mx": ("Tlnovelas", "", ["tlnovelas"]),
    "AE.lat": ("A&E HD", "", ["a&e", "ae network"]),
    "AXN.lat": ("AXN HD", "", ["axn"]),
    "AdultSwim.lat": ("Adult Swim", "", ["adult swim"]),
    "AnimalPlanet.lat": ("Animal Planet HD", "", ["animal planet"]),
    "ComedyCentral.lat": ("Comedy Central HD", "", ["comedy central"]),
    "DiscoveryChannel.lat": ("Discovery Channel HD", "", ["discovery channel"]),
    "DiscoveryTheater.lat": ("Discovery Theater HD", "", ["discovery theater"]),
    "DistritoComedia.mx": ("Distrito Comedia", "", ["distrito comedia"]),
    "E.lat": ("E! Entertainment TV", "", ["e entertainment", "e! entertainment"]),
    "ElGourmet.lat": ("El Gourmet HD", "", ["el gourmet"]),
    "EuropaEuropa.lat": ("Europa Europa", "", ["europa europa"]),
    "FMHFamily.lat": ("FMH Family", "", ["fmh family"]),
    "FX.lat": ("FX HD", "", ["fx"]),
    "FilmArts.lat": ("Film&Arts", "", ["film&arts", "film and arts"]),
    "FilmArtsb.lat": ("Film&Arts (Op. 2)", "", ["film&arts", "film and arts"]),
    "FoodNetwork.lat": ("Food Network", "", ["food network"]),
    "History2.lat": ("History 2", "", ["history 2", "h2"]),
    "History.lat": ("History Channel HD", "", ["history"]),
    "HomeHealth.lat": ("Home & Health HD", "", ["home & health", "home and health"]),
    "ID.lat": ("ID HD", "", ["investigation discovery"]),
    "Lifetime.lat": ("Lifetime", "", ["lifetime"]),
    "LoveNature.lat": ("Love Nature", "", ["love nature"]),
    "NatGeo.lat": ("Nat Geo HD", "", ["national geographic", "nat geo"]),
    "Sony.lat": ("Sony HD", "", ["sony channel"]),
    "TNTSeries.lat": ("TNT Series HD", "", ["tnt series"]),
    "UniversalChannel.lat": ("Universal Channel HD", "", ["universal tv", "universal channel"]),
    "USA.us": ("USA Network", "", ["usa network"]),
    "WarnerChannel.lat": ("Warner Channel", "", ["warner"]),
    "WarnerChannelHD.lat": ("Warner Channel HD", "", ["warner"]),
    "BabyTV.lat": ("Baby TV", "", ["baby tv", "babytv"]),
    "CartoonNetwork.lat": ("Cartoon Network HD", "", ["cartoon network"]),
    "Cartoonito.lat": ("Cartoonito", "", ["cartoonito"]),
    "DiscoveryKids.lat": ("Discovery Kids HD", "", ["discovery kids"]),
    "DisneyChannel.lat": ("Disney HD", "", ["disney channel"]),
    "DisneyJunior.lat": ("Disney Junior", "", ["disney junior"]),
    "FMHFamilyKids.lat": ("FMH Family Kids", "", ["fmh family kids"]),
    "Nick.lat": ("Nick HD", "", ["nickelodeon"]),
    "NickJr.lat": ("Nick Jr.", "", ["nick jr"]),
    "PlimPlim.ar": ("Plim Plim TV", "", ["plim plim"]),
    "TeenNick.lat": ("TeenNick", "", ["teen nick", "teennick"]),
    "Tooncast.lat": ("Tooncast", "", ["tooncast"]),
    "ATV.pe": ("ATV", "", ["atv peru", "atv"]),
    "AmericaTV.pe": ("América TV HD", "", ["america tv", "america television"]),
    "BBCNews.uk": ("BBC News", "", ["bbc news", "bbc world"]),
    "CHV.cl": ("CHV HD", "", ["chilevision", "chv"]),
    "CNNespanol.lat": ("CNN Español", "", ["cnn en espanol", "cnn espanol"]),
    "CNNintl.uk": ("CNN International", "", ["cnn international"]),
    "CanalN.pe": ("Canal N", "", ["canal n"]),
    "DWespanol.de": ("DW Español", "", ["dw espanol", "deutsche welle"]),
    "DirecTV.lat": ("DirecTV", "", ["directv"]),
    "ExitosaTV.pe": ("Exitosa TV", "", ["exitosa"]),
    "France24.fr": ("France 24", "", ["france 24"]),
    "Global.pe": ("Global TV", "", ["global tv", "global"]),
    "Karibena.pe": ("Karibeña", "", ["karibena"]),
    "LaRed.cl": ("La Red", "", ["la red"]),
    "LasEstrellas.mx": ("Las Estrellas HD", "", ["las estrellas"]),
    "Latina.pe": ("Latina HD", "", ["latina"]),
    "Mega.cl": ("MEGA HD", "", ["mega"]),
    "Megab.cl": ("Mega (Op. 2)", "", ["mega"]),
    "NuestraTele.co": ("Nuestra Tele", "", ["nuestra tele"]),
    "OromarTV.ec": ("Oromar TV", "", ["oromar"]),
    "Panamericana.pe": ("Panamericana", "", ["panamericana"]),
    "RAIItalia.it": ("RAI Italia", "", ["rai italia"]),
    "RECTV.cl": ("REC TV", "", ["rec tv"]),
    "RPP.pe": ("RPP", "", ["rpp"]),
    "SomosTV.ve": ("Somos TV Venezuela", "", ["somos tv"]),
    "StarChannel.lat": ("Star Channel", "", ["star channel"]),
    "StarChannelHD.lat": ("Star Channel HD", "", ["star channel"]),
    "TVAragua.ve": ("TV Aragua", "", ["tv aragua"]),
    "TVPeru.pe": ("TV Perú", "", ["tv peru"]),
    "TVE.es": ("TVE", "", ["tve"]),
    "TVSMaracay.ve": ("TVS Maracay", "", ["tvs maracay"]),
    "Telefe.ar": ("Telefé", "", ["telefe"]),
    "Willax.pe": ("Willax", "", ["willax"]),
    "WestTV.lat": ("West TV", "", ["west tv"]),
    "TVO.es": ("TVO", "", ["tvo"]),
    "CanalI.ve": ("Canal I", "", ["canal i"]),
    "Globovision.ve": ("Globovisión", "", ["globovision"]),
    "TLT.ve": ("TLT", "", ["tlt", "la tele tuya"]),
    "Venevision.ve": ("Venevisión", "", ["venevision"]),
    "HTV.lat": ("HTV", "", ["htv"]),
    "HTVb.lat": ("HTV (Op. 2)", "", ["htv"]),
    "MiMusicaHits.lat": ("Mi Música Hits", "", ["mi musica hits"]),
    "MiMusicaPeru.pe": ("Mi Música Perú", "", ["mi musica peru"]),
    "MTV.lat": ("MTV HD", "", ["mtv"]),
    "MundoMusica.lat": ("Mundo de la Música", "", ["mundo de la musica"]),
    "MusicaVene.ve": ("Música Vene", "", ["musica vene"]),
    "NickMusic.lat": ("Nick Music", "", ["nick music"]),
    "StingrayConcerts.lat": ("Stingray Concerts HD", "", ["stingray concerts"]),
    "TopLatino.lat": ("Top Latino", "", ["top latino"]),
    "VisionMusica.lat": ("Visión Música", "", ["vision musica"]),
    "FibMusic.lat": ("Fib Music", "", ["fib music"]),
    "VclassicMusica.lat": ("VClassic Música", "", ["vclassic"]),
    "BethelTV.pe": ("Bethel TV", "", ["bethel"]),
    "Daystar.us": ("Daystar", "", ["daystar"]),
    "EWTN.us": ("EWTN", "", ["ewtn"]),
    "Enlace.lat": ("Enlace", "", ["enlace"]),
    "NuevoTiempo.lat": ("Nuevo Tiempo", "", ["nuevo tiempo"]),
    "Sextreme.lat": ("Sextreme", "", ["sextreme"]),
}


def norm(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()


def find_best_channel_match(keywords, source_channels):
    norm_keywords = [norm(kw) for kw in keywords if norm(kw)]
    if not norm_keywords:
        return None

    for kw in norm_keywords:
        for cid, names in source_channels.items():
            if kw in names:
                return cid

    for kw in norm_keywords:
        pattern = re.compile(rf"(?:^|\s){re.escape(kw)}(?:\s|$)")
        for cid, names in source_channels.items():
            if any(pattern.search(n) for n in names):
                return cid

    return None


def add_fallback_programme(root, tvg_id, display_name):
    tz_ve = timezone(timedelta(hours=-4))
    now_ve = datetime.now(tz_ve)
    start_dt = now_ve.replace(hour=0, minute=0, second=0, microsecond=0)
    stop_dt = start_dt + timedelta(hours=24)

    prog = ET.SubElement(root, "programme", attrib={
        "start": start_dt.strftime("%Y%m%d%H%M%S -0400"),
        "stop": stop_dt.strftime("%Y%m%d%H%M%S -0400"),
        "channel": tvg_id,
    })
    title_el = ET.SubElement(prog, "title", attrib={"lang": "es"})
    title_el.text = "Programación en emisión"
    desc_el = ET.SubElement(prog, "desc", attrib={"lang": "es"})
    desc_el.text = f"Guía activa para {display_name}."


def stream_parse_source(url, source_channels, matched_cids_needed, source_programmes):
    headers = {"User-Agent": "Mozilla/5.0 (iptv-epg-builder/1.0)"}
    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        raw_stream = r.raw
        stream = gzip.GzipFile(fileobj=raw_stream) if url.endswith(".gz") else raw_stream

        # Primera pasada ligera: solo canales
        for event, elem in ET.iterparse(stream, events=("end",)):
            if elem.tag == "channel":
                cid = elem.attrib.get("id", "")
                names = [norm(d.text) for d in elem.findall("display-name") if d.text]
                if cid and names:
                    source_channels[cid] = names
                elem.clear()
            elif elem.tag == "programme":
                elem.clear()

    # Determinar qué source_cid necesitamos guardar
    needed_set = set()
    for _, _, keywords in CHANNELS.values():
        matched = find_best_channel_match(keywords, source_channels)
        if matched:
            needed_set.add(matched)
            matched_cids_needed.add(matched)

    if not needed_set:
        return

    # Segunda pasada ligera: solo programas de los canales que sí coinciden
    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        raw_stream = r.raw
        stream = gzip.GzipFile(fileobj=raw_stream) if url.endswith(".gz") else raw_stream

        for event, elem in ET.iterparse(stream, events=("end",)):
            if elem.tag == "programme":
                cid = elem.attrib.get("channel", "")
                if cid in needed_set:
                    source_programmes.setdefault(cid, []).append(elem)
                else:
                    elem.clear()
            elif elem.tag == "channel":
                elem.clear()


def build_epg():
    root = ET.Element("tv", attrib={"generator-info-name": "miguelrojas696-iptv-epg"})
    source_channels = {}
    matched_cids_needed = set()
    source_programmes = {}

    for url in EPG_SOURCES:
        try:
            stream_parse_source(url, source_channels, matched_cids_needed, source_programmes)
            print(f"Fuente procesada: {url} ({len(source_channels)} canales detectados)")
        except Exception as e:
            print(f"Aviso con fuente {url}: {e}")

    matched_total = 0
    fallback_total = 0

    for tvg_id, (display_name, logo_url, keywords) in CHANNELS.items():
        ch_el = ET.SubElement(root, "channel", attrib={"id": tvg_id})
        dn = ET.SubElement(ch_el, "display-name")
        dn.text = display_name
        if logo_url:
            ET.SubElement(ch_el, "icon", attrib={"src": logo_url})

        matched_cid = find_best_channel_match(keywords, source_channels)
        added_count = 0

        if matched_cid and matched_cid in source_programmes:
            for p in source_programmes[matched_cid]:
                new_p = ET.SubElement(root, "programme", attrib={
                    "start": p.attrib.get("start", ""),
                    "stop": p.attrib.get("stop", ""),
                    "channel": tvg_id,
                })
                for child in p:
                    new_p.append(child)
                added_count += 1

        if added_count > 0:
            matched_total += 1
            print(f"[OK] {tvg_id} -> {matched_cid} ({added_count} programas)")
        else:
            fallback_total += 1
            add_fallback_programme(root, tvg_id, display_name)
            print(f"[RESPALDO] {tvg_id} ({display_name}) sin programas en fuente")

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print(f"epg.xml generado: {matched_total} con guía real, {fallback_total} con respaldo.")


if __name__ == "__main__":
    build_epg()
