"""Comportamientos por default (REQ 4, 5).

Cada uno es un dict con name, description y code. El code es el texto de una
función decidir(contexto) que usa las primitivas (correr_hacia, patear,
robar_pelota_jugador). El seed recorre esta lista y los guarda en la tabla
behaviors.

También sirven de ejemplo para el usuario que después programe los suyos.
"""

OFENSIVO = '''\
def decidir(contexto):
    if contexto["jugador_con_pelota"] == contexto["mi_id"]:
        patear(contexto["arco_rival"])
    else:
        correr_hacia(contexto["posicion_pelota"])
'''

DEFENSIVO = '''\
def decidir(contexto):
    con_pelota = contexto["jugador_con_pelota"]
    ids_rivales = [r["id"] for r in contexto["jugadores_rivales"]]
    if con_pelota in ids_rivales:
        robar_pelota_jugador(con_pelota)
    else:
        correr_hacia(contexto["posicion_pelota"])
'''

EQUILIBRADO = '''\
def decidir(contexto):
    con_pelota = contexto["jugador_con_pelota"]
    ids_rivales = [r["id"] for r in contexto["jugadores_rivales"]]
    if con_pelota == contexto["mi_id"]:
        patear(contexto["arco_rival"])
    elif con_pelota in ids_rivales:
        robar_pelota_jugador(con_pelota)
    else:
        correr_hacia(contexto["posicion_pelota"])
'''

DEFAULT_BEHAVIORS = [
    {
        "name": "Ofensivo",
        "description": "Si tiene la pelota, patea al arco rival. Si no, corre hacia la pelota.",
        "code": OFENSIVO,
    },
    {
        "name": "Defensivo",
        "description": "Si un rival tiene la pelota, intenta robarla. Si no, corre hacia la pelota.",
        "code": DEFENSIVO,
    },
    {
        "name": "Equilibrado",
        "description": "Patea si tiene la pelota, roba si la tiene un rival y corre hacia ella si está libre.",
        "code": EQUILIBRADO,
    },
]