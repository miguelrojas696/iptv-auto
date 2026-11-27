import gc
import gzip
import io
import re
import unicodedata
import xml.etree.ElementTree as ET
import requests

# Pon aquí las URLs de EPG que ya sabes que funcionan (las tuyas o feeds XML/XML.GZ activos)
EPG_SOURCES = [
    # "https://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz",
    # "https://TU-FUENTE-EPG-2.xml.gz",
]

# tvg-id -> (nombre visible, logo_url, keywords de búsqueda)
CHANNELS = {
    "AE.lat": ("A&E", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/A%26E_Network_logo.svg/512px-A%26E_Network_logo.svg.png", ["a&e", "ae network", "ae"]),
    "AMC.lat": ("AMC", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/AMC_logo_2019.svg/512px-AMC_logo_2019.svg.png", ["amc"]),
    "AMCHD.lat": ("AMC HD", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/AMC_logo_2019.svg/512px-AMC_logo_2019.svg.png", ["amc hd", "amc"]),
    "ATV.pe": ("ATV", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/ATV_Per%C3%BA_logo.svg/512px-ATV_Per%C3%BA_logo.svg.png", ["atv peru", "atv"]),
    "AXN.lat": ("AXN", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/AXN_logo_2023.svg/512px-AXN_logo_2023.svg.png", ["axn"]),
    "AdultSwim.lat": ("Adult Swim", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Adult_Swim_2023_logo.svg/512px-Adult_Swim_2023_logo.svg.png", ["adult swim"]),
    "AmericaTV.pe": ("América TV", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Am%C3%A9rica_Televisi%C3%B3n_logo.svg/512px-Am%C3%A9rica_Televisi%C3%B3n_logo.svg.png", ["america tv", "america television"]),
    "AnimalPlanet.lat": ("Animal Planet", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Animal_Planet_logo.svg/512px-Animal_Planet_logo.svg.png", ["animal planet"]),
    "BBCNews.uk": ("BBC News", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/BBC_News_2022_%28icon%29.svg/512px-BBC_News_2022_%28icon%29.svg.png", ["bbc news", "bbc world"]),
    "BethelTV.pe": ("Bethel TV", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Bethel_Television_logo.svg/512px-Bethel_Television_logo.svg.png", ["bethel tv", "bethel"]),
    "BabyTV.lat": ("Baby TV", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/BabyTV_logo.svg/512px-BabyTV_logo.svg.png", ["baby tv", "babytv"]),
    "CHV.cl": ("CHV", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Chilevisi%C3%B3n_2020.svg/512px-Chilevisi%C3%B3n_2020.svg.png", ["chilevision", "chv"]),
    "CNNespanol.lat": ("CNN Español", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/CNN_International_logo.svg/512px-CNN_International_logo.svg.png", ["cnn en espanol", "cnn espanol"]),
    "CNNintl.uk": ("CNN International", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/CNN_International_logo.svg/512px-CNN_International_logo.svg.png", ["cnn international"]),
    "CanalN.pe": ("Canal N", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Canal_N_logo.svg/512px-Canal_N_logo.svg.png", ["canal n"]),
    "CartoonNetwork.lat": ("Cartoon Network", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Cartoon_Network_2010_logo.svg/512px-Cartoon_Network_2010_logo.svg.png", ["cartoon network"]),
    "Cartoonito.lat": ("Cartoonito", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Cartoonito_2021_logo.svg/512px-Cartoonito_2021_logo.svg.png", ["cartoonito"]),
    "Cinecanal.lat": ("Cinecanal", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Cinecanal_logo.svg/512px-Cinecanal_logo.svg.png", ["cinecanal"]),
    "Cinemax.lat": ("Cinemax", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Cinemax_logo.svg/512px-Cinemax_logo.svg.png", ["cinemax"]),
    "ComedyCentral.lat": ("Comedy Central", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Comedy_Central_2018.svg/512px-Comedy_Central_2018.svg.png", ["comedy central"]),
    "Daystar.us": ("Daystar", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Daystar_Television_Network_logo.svg/512px-Daystar_Television_Network_logo.svg.png", ["daystar"]),
    "DWespanol.de": ("DW Español", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Deutsche_Welle_symbol_2012.svg/512px-Deutsche_Welle_symbol_2012.svg.png", ["dw espanol", "deutsche welle"]),
    "DePelicula.mx": ("De Película", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/De_Pel%C3%ADcula_logo.svg/512px-De_Pel%C3%ADcula_logo.svg.png", ["de pelicula"]),
    "DirecTV.lat": ("DirecTV", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/DirecTV_logo_2019.svg/512px-DirecTV_logo_2019.svg.png", ["directv"]),
    "DSports.lat": ("DSports", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/DSports_logo.svg/512px-DSports_logo.svg.png", ["dsports", "directv sports"]),
    "DiscoveryChannel.lat": ("Discovery Channel", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Discovery_Channel_%282019%29.svg/512px-Discovery_Channel_%282019%29.svg.png", ["discovery channel", "discovery"]),
    "DiscoveryKids.lat": ("Discovery Kids", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Discovery_Kids_2016.svg/512px-Discovery_Kids_2016.svg.png", ["discovery kids"]),
    "DiscoveryTheater.lat": ("Discovery Theater", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Discovery_Channel_%282019%29.svg/512px-Discovery_Channel_%282019%29.svg.png", ["discovery theater", "discovery turbo"]),
    "DisneyChannel.lat": ("Disney Channel", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Disney_Channel_logo_%282014%29.svg/512px-Disney_Channel_logo_%282014%29.svg.png", ["disney channel", "disney"]),
    "DisneyJunior.lat": ("Disney Junior", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Disney_Junior_logo_2014.svg/512px-Disney_Junior_logo_2014.svg.png", ["disney junior"]),
    "DistritoComedia.mx": ("Distrito Comedia", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Distrito_Comedia_logo.svg/512px-Distrito_Comedia_logo.svg.png", ["distrito comedia"]),
    "E.lat": ("E! Entertainment TV", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/E%21_logo_2012.svg/512px-E%21_logo_2012.svg.png", ["e entertainment", "e! entertainment"]),
    "ESPN2.lat": ("ESPN 2", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/ESPN2_logo.svg/512px-ESPN2_logo.svg.png", ["espn 2", "espn2"]),
    "ESPN2b.lat": ("ESPN 2 (Op 2)", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/ESPN2_logo.svg/512px-ESPN2_logo.svg.png", ["espn 2", "espn2"]),
    "ESPN3.lat": ("ESPN 3", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/ESPN3_logo.svg/512px-ESPN3_logo.svg.png", ["espn 3", "espn3"]),
    "ESPN4.lat": ("ESPN 4", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn 4", "espn4"]),
    "ESPN5.lat": ("ESPN 5", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn 5", "espn5"]),
    "ESPN6.lat": ("ESPN 6", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn 6", "espn6"]),
    "ESPN7.lat": ("ESPN 7", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn 7", "espn7"]),
    "ESPN.lat": ("ESPN", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn"]),
    "ESPNb.lat": ("ESPN (Op 2)", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn"]),
    "ESPNc.lat": ("ESPN (Op 3)", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn"]),
    "ESPNPremium.ar": ("ESPN Premium", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_wordmark.svg/512px-ESPN_wordmark.svg.png", ["espn premium"]),
    "EWTN.us": ("EWTN", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/EWTN_logo.svg/512px-EWTN_logo.svg.png", ["ewtn"]),
    "ElGourmet.lat": ("El Gourmet", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/El_Gourmet_logo.svg/512px-El_Gourmet_logo.svg.png", ["el gourmet"]),
    "Enlace.lat": ("Enlace", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Enlace_TV_logo.svg/512px-Enlace_TV_logo.svg.png", ["enlace"]),
    "EuropaEuropa.lat": ("Europa Europa", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Europa_Europa_logo.svg/512px-Europa_Europa_logo.svg.png", ["europa europa"]),
    "ExitosaTV.pe": ("Exitosa TV", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Exitosa_TV_logo.svg/512px-Exitosa_TV_logo.svg.png", ["exitosa"]),
    "FMHFamily.lat": ("FMH Family", "", ["fmh family"]),
    "FMHFamilyKids.lat": ("FMH Family Kids", "", ["fmh family kids"]),
    "FMHFamilyMovie.lat": ("FMH Family Movie", "", ["fmh family movie"]),
    "FoxSportsPremium.ar": ("Fox Sports Premium", "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Fox_Sports_logo.svg/512px-Fox_Sports_logo.svg.png", ["fox sports premium", "fox sports"]),
    "FX.lat": ("FX", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/FX_logo.svg/512px-FX_logo.svg.png", ["fx"]),
    "FilmArts.lat": ("Film&Arts", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Film%26Arts_logo.svg/512px-Film%26Arts_logo.svg.png", ["film&arts", "film and arts"]),
    "FilmArtsb.lat": ("Film&Arts (Op 2)", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Film%26Arts_logo.svg/512px-Film%26Arts_logo.svg.png", ["film&arts", "film and arts"]),
    "FoodNetwork.lat": ("Food Network", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Food_Network_logo.svg/512px-Food_Network_logo.svg.png", ["food network"]),
    "France24.fr": ("France 24", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/France_24_logo.svg/512px-France_24_logo.svg.png", ["france 24"]),
    "Global.pe": ("Global TV", "", ["global tv", "global"]),
    "GoldenEdge.lat": ("Golden Edge", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Golden_Edge_logo.svg/512px-Golden_Edge_logo.svg.png", ["golden edge"]),
    "Golden.lat": ("Golden", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Golden_TV_logo.svg/512px-Golden_TV_logo.svg.png", ["golden"]),
    "HBOFamily.lat": ("HBO Family", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo family"]),
    "HBO.lat": ("HBO", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo"]),
    "HBOMundi.lat": ("HBO Mundi", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo mundi"]),
    "HBOPlus.lat": ("HBO Plus", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo plus"]),
    "HBOSignature.lat": ("HBO Signature", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo signature"]),
    "HBOExtreme.lat": ("HBO Xtreme", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/HBO_logo.svg/512px-HBO_logo.svg.png", ["hbo xtreme"]),
    "HTV.lat": ("HTV", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/HTV_logo.svg/512px-HTV_logo.svg.png", ["htv"]),
    "HTVb.lat": ("HTV (Op 2)", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/HTV_logo.svg/512px-HTV_logo.svg.png", ["htv"]),
    "History2.lat": ("History 2", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/History_Channel_logo.svg/512px-History_Channel_logo.svg.png", ["history 2", "h2"]),
    "History.lat": ("History Channel", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/History_Channel_logo.svg/512px-History_Channel_logo.svg.png", ["history channel", "history"]),
    "HomeHealth.lat": ("Home & Health", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Discovery_Home_%26_Health_logo.svg/512px-Discovery_Home_%26_Health_logo.svg.png", ["home & health", "home and health"]),
    "ID.lat": ("ID", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Investigation_Discovery_logo.svg/512px-Investigation_Discovery_logo.svg.png", ["investigation discovery", "id"]),
    "Karibena.pe": ("Karibeña", "", ["karibena"]),
    "KanalDDrama.lat": ("Kanal D Drama", "", ["kanal d drama"]),
    "L1.pe": ("L1", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Liga_1_%28Per%C3%BA%29_logo.svg/512px-Liga_1_%28Per%C3%BA%29_logo.svg.png", ["liga 1", "l1"]),
    "L1Max.pe": ("L1 MAX", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Liga_1_%28Per%C3%BA%29_logo.svg/512px-Liga_1_%28Per%C3%BA%29_logo.svg.png", ["liga 1 max", "l1 max"]),
    "LaRed.cl": ("La Red", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/La_Red_%28Chile%29_logo.svg/512px-La_Red_%28Chile%29_logo.svg.png", ["la red"]),
    "LasEstrellas.mx": ("Las Estrellas", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Las_Estrellas_logo.svg/512px-Las_Estrellas_logo.svg.png", ["las estrellas"]),
    "Latina.pe": ("Latina", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Latina_Televisi%C3%B3n_logo.svg/512px-Latina_Televisi%C3%B3n_logo.svg.png", ["latina"]),
    "Lifetime.lat": ("Lifetime", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Lifetime_logo.svg/512px-Lifetime_logo.svg.png", ["lifetime"]),
    "LoveNature.lat": ("Love Nature", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Love_Nature_logo.svg/512px-Love_Nature_logo.svg.png", ["love nature"]),
    "Mega.cl": ("MEGA", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Mega_%28Chile%29_logo.svg/512px-Mega_%28Chile%29_logo.svg.png", ["mega"]),
    "MiMusicaHits.lat": ("Mi Música Hits", "", ["mi musica hits"]),
    "MiMusicaPeru.pe": ("Mi Música Perú", "", ["mi musica peru"]),
    "MTV.lat": ("MTV", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/MTV_Logo_2010.svg/512px-MTV_Logo_2010.svg.png", ["mtv"]),
    "MundoMusica.lat": ("Mundo de la Música", "", ["mundo de la musica"]),
    "MusicaVene.ve": ("Música Vene", "", ["musica vene"]),
    "Megab.cl": ("Mega (Op 2)", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Mega_%28Chile%29_logo.svg/512px-Mega_%28Chile%29_logo.svg.png", ["mega"]),
    "MovistarDeportes.pe": ("Movistar Deportes", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Movistar_Deportes_logo.svg/512px-Movistar_Deportes_logo.svg.png", ["movistar deportes"]),
    "NuevoTiempo.lat": ("Nuevo Tiempo", "", ["nuevo tiempo"]),
    "NatGeo.lat": ("Nat Geo", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/National_Geographic_Channel.svg/512px-National_Geographic_Channel.svg.png", ["national geographic", "nat geo"]),
    "Nick.lat": ("Nick", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Nickelodeon_2009_logo.svg/512px-Nickelodeon_2009_logo.svg.png", ["nickelodeon", "nick"]),
    "NickJr.lat": ("Nick Jr.", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Nick_Jr._logo_2009.svg/512px-Nick_Jr._logo_2009.svg.png", ["nick jr"]),
    "NickMusic.lat": ("Nick Music", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/NickMusic_logo.svg/512px-NickMusic_logo.svg.png", ["nick music"]),
    "NuestraTele.co": ("Nuestra Tele", "", ["nuestra tele"]),
    "OromarTV.ec": ("Oromar TV", "", ["oromar"]),
    "Panamericana.pe": ("Panamericana", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Panamericana_Televisi%C3%B3n_logo.svg/512px-Panamericana_Televisi%C3%B3n_logo.svg.png", ["panamericana"]),
    "Pasiones.lat": ("Pasiones", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Pasiones_TV_logo.svg/512px-Pasiones_TV_logo.svg.png", ["pasiones"]),
    "PlimPlim.ar": ("Plim Plim TV", "", ["plim plim"]),
    "RAIItalia.it": ("RAI Italia", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Rai_logo_2020.svg/512px-Rai_logo_2020.svg.png", ["rai italia"]),
    "RECTV.cl": ("REC TV", "", ["rec tv"]),
    "RPP.pe": ("RPP", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/RPP_logo.svg/512px-RPP_logo.svg.png", ["rpp"]),
    "SomosTV.ve": ("Somos TV Venezuela", "", ["somos tv"]),
    "StarChannel.lat": ("Star Channel", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Star_Channel_logo.svg/512px-Star_Channel_logo.svg.png", ["star channel"]),
    "StarChannelHD.lat": ("Star Channel (Op 2)", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Star_Channel_logo.svg/512px-Star_Channel_logo.svg.png", ["star channel"]),
    "Sextreme.lat": ("Sextreme", "", ["sextreme"]),
    "Sony.lat": ("Sony", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Sony_Channel_logo.svg/512px-Sony_Channel_logo.svg.png", ["sony channel", "sony"]),
    "SonyMovies.lat": ("Sony Movies", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Sony_Channel_logo.svg/512px-Sony_Channel_logo.svg.png", ["sony movies"]),
    "Space.lat": ("Space", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Space_logo_2015.svg/512px-Space_logo_2015.svg.png", ["space"]),
    "StingrayConcerts.lat": ("Stingray Concerts", "", ["stingray concerts"]),
    "StudioUniversal.lat": ("Studio Universal", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Studio_Universal_logo.svg/512px-Studio_Universal_logo.svg.png", ["studio universal"]),
    "TCM.lat": ("TCM", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/TCM_logo.svg/512px-TCM_logo.svg.png", ["tcm"]),
    "TNT.lat": ("TNT", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/TNT_Logo_2016.svg/512px-TNT_Logo_2016.svg.png", ["tnt"]),
    "TNTNovelas.lat": ("TNT Novelas", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/TNT_Logo_2016.svg/512px-TNT_Logo_2016.svg.png", ["tnt novelas"]),
    "TNTSeries.lat": ("TNT Series", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/TNT_Logo_2016.svg/512px-TNT_Logo_2016.svg.png", ["tnt series"]),
    "TNTSportsPremium.ar": ("TNT Sports Premium", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/TNT_Logo_2016.svg/512px-TNT_Logo_2016.svg.png", ["tnt sports"]),
    "TopLatino.lat": ("Top Latino", "", ["top latino"]),
    "TVAragua.ve": ("TV Aragua", "", ["tv aragua"]),
    "TVPeru.pe": ("TV Perú", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/TV_Per%C3%BA_logo.svg/512px-TV_Per%C3%BA_logo.svg.png", ["tv peru"]),
    "TVE.es": ("TVE", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/TVE_logo.svg/512px-TVE_logo.svg.png", ["tve"]),
    "TVSMaracay.ve": ("TVS Maracay", "", ["tvs maracay"]),
    "TeenNick.lat": ("TeenNick", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/TeenNick_logo_2009.svg/512px-TeenNick_logo.svg.png", ["teen nick", "teennick"]),
    "Telefe.ar": ("Telefé", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Telefe_logo_2022.svg/512px-Telefe_logo_2022.svg.png", ["telefe"]),
    "Telemundo.us": ("Telemundo", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Telemundo_logo_2018.svg/512px-Telemundo_logo_2018.svg.png", ["telemundo"]),
    "Tlnovelas.mx": ("Tlnovelas", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Tlnovelas_logo.svg/512px-Tlnovelas_logo.svg.png", ["tlnovelas"]),
    "Tooncast.lat": ("Tooncast", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Tooncast_logo.svg/512px-Tooncast_logo.svg.png", ["tooncast"]),
    "UFC.us": ("UFC", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/UFC_Logo.svg/512px-UFC_Logo.svg.png", ["ufc"]),
    "UniversalChannel.lat": ("Universal Channel", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Universal_TV_logo.svg/512px-Universal_TV_logo.svg.png", ["universal tv", "universal channel"]),
    "USA.us": ("USA Network", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/USA_Network_logo_2016.svg/512px-USA_Network_logo_2016.svg.png", ["usa network"]),
    "VisionMusica.lat": ("Visión Música", "", ["vision musica"]),
    "ViaXEsports.cl": ("Vía X Esports", "", ["via x esports"]),
    "WarnerChannel.lat": ("Warner Channel", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Warner_Channel_logo_%282019%29.svg/512px-Warner_Channel_logo_%282019%29.svg.png", ["warner channel", "warner"]),
    "WarnerChannelHD.lat": ("Warner Channel (Op 2)", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Warner_Channel_logo_%282019%29.svg/512px-Warner_Channel_logo_%282019%29.svg.png", ["warner channel", "warner"]),
    "Willax.pe": ("Willax", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Willax_Televisi%C3%B3n_logo.svg/512px-Willax_Televisi%C3%B3n_logo.svg.png", ["willax"]),
    "FibMusic.lat": ("Fib Music", "", ["fib music"]),
    "FibPeliculas.lat": ("Fib Películas", "", ["fib peliculas"]),
    "VclassicMusica.lat": ("VClassic Música", "", ["vclassic"]),
    "WestTV.lat": ("West TV", "", ["west tv"]),
    "DSportsOp3.lat": ("DSports (Opción 3)", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/DSports_logo.svg/512px-DSports_logo.svg.png", ["dsports"]),
    "TVO.es": ("TVO", "", ["tvo"]),
    "CanalI.ve": ("Canal I", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Canal_i_%28Venezuela%29_logo.svg/512px-Canal_i_%28Venezuela%29_logo.svg.png", ["canal i"]),
    "Globovision.ve": ("Globovisión", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Globovisi%C3%B3n_logo.svg/512px-Globovisi%C3%B3n_logo.svg.png", ["globovision"]),
    "TLT.ve": ("TLT", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/La_Tele_Tuya_logo.svg/512px-La_Tele_Tuya_logo.svg.png", ["tlt", "la tele tuya"]),
    "Venevision.ve": ("Venevisión", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Venevisi%C3%B3n_logo.svg/512px-Venevisi%C3%B3n_logo.svg.png", ["venevision"]),
}


def norm(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()


def open_stream(url):
    headers = {"User-Agent": "Mozilla/5.0 (iptv-epg-builder/3.0)"}
    r = requests.get(url, headers=headers, timeout=60, stream=True)
    r.raise_for_status()
    raw_bytes = io.BytesIO(r.content)
    header = raw_bytes.getbuffer()[:2]
    raw_bytes.seek(0)
    if url.endswith(".gz") or bytes(header) == b"\x1f\x8b":
        return gzip.GzipFile(fileobj=raw_bytes)
    return raw_bytes


def find_best_channel_match(tvg_id, keywords, source_channels):
    norm_id = norm(tvg_id.split(".")[0])
    norm_keywords = [norm(kw) for kw in keywords if norm(kw)]
    candidates = ([norm_id] if norm_id else []) + norm_keywords

    for kw in candidates:
        for cid, names in source_channels.items():
            if kw in names:
                return cid

    for kw in candidates:
        pattern = re.compile(rf"(?:^|\s){re.escape(kw)}(?:\s|$)")
        for cid, names in source_channels.items():
            if any(pattern.search(n) for n in names):
                return cid

    return None


def build_epg():
    root = ET.Element("tv", attrib={"generator-info-name": "miguelrojas696-iptv-epg"})
    channel_elements = {}

    for tvg_id, (display_name, logo_url, _) in CHANNELS.items():
        ch_el = ET.SubElement(root, "channel", attrib={"id": tvg_id})
        dn = ET.SubElement(ch_el, "display-name")
        dn.text = display_name
        if logo_url:
            ET.SubElement(ch_el, "icon", attrib={"src": logo_url})
        channel_elements[tvg_id] = ch_el

    matched_counts = {tvg_id: 0 for tvg_id in CHANNELS}

    for url in EPG_SOURCES:
        try:
            stream = open_stream(url)
            source_channels = {}
            target_cids = set()

            for event, elem in ET.iterparse(stream, events=("end",)):
                if elem.tag == "channel":
                    cid = elem.attrib.get("id", "").strip()
                    names = [norm(d.text) for d in elem.findall("display-name") if d.text]
                    if cid:
                        source_channels[cid] = names
                    elem.clear()
                elif elem.tag == "programme":
                    break

            cid_to_tvg = {}
            for tvg_id, (_, _, keywords) in CHANNELS.items():
                best_cid = find_best_channel_match(tvg_id, keywords, source_channels)
                if best_cid:
                    cid_to_tvg[best_cid] = tvg_id
                    target_cids.add(best_cid)

            stream.seek(0)
            stream = open_stream(url)
            for event, elem in ET.iterparse(stream, events=("end",)):
                if elem.tag == "programme":
                    cid = elem.attrib.get("channel", "").strip()
                    if cid in cid_to_tvg:
                        tvg_id = cid_to_tvg[cid]
                        new_p = ET.SubElement(root, "programme", attrib={
                            "start": elem.attrib.get("start", ""),
                            "stop": elem.attrib.get("stop", ""),
                            "channel": tvg_id,
                        })
                        for child in elem:
                            new_p.append(child)
                        matched_counts[tvg_id] += 1
                    elem.clear()

            print(f"[FUENTE OK] {url} -> {len(cid_to_tvg)} canales emparejados")
            del source_channels, cid_to_tvg, target_cids
            gc.collect()
        except Exception as e:
            print(f"[AVISO FUENTE] {url}: {e}")

    matched_total = 0
    for tvg_id, (display_name, _, _) in CHANNELS.items():
        if matched_counts[tvg_id] > 0:
            matched_total += 1
            print(f"[OK] {tvg_id} ({matched_counts[tvg_id]} programas)")
        else:
            print(f"[SIN GUIA] {tvg_id} ({display_name}) sin programas en fuentes")

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print(f"epg.xml generado: {matched_total} con guía real, {len(CHANNELS) - matched_total} sin guía.")


if __name__ == "__main__":
    build_epg()
