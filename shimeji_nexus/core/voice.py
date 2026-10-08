import random

FRASES_DEFECTO = {
    "mouse": ["¿Qué?", "¿Me llamaste?", "Hm?", "¿Sí?"],
    "aterrizar": ["¡Arriba!", "Aquí se ve bien~", "*se posa*", "¿Qué ventana es esta?", "Cómodo aquí"],
    "posarse": ["*se posa*", "Aquí estaré bien."],
    "magia": ["¡Mira esto!", "*invoca su aura*"],
    "choque": ["¡Oye!", "¡Quita!", "Eh...", "¡Casi chocamos!", "Ups~"],
    "hola_otro": ["¡Hola!", "Hey!", "¿Qué tal?", "¡{nombre}!", "Qué gusto~"],
    "bailar": ["¡A bailar!", "Sigue el ritmo~", "*danza*"],
    "volar": ["¡A volar!", "*flota*", "Arriba~"],
    "pomodoro_inicio": ["Pomodoro de {min} min en marcha. ¡A concentrarse!"],
    "pomodoro_mitad": ["Vas por la mitad, sigue así."],
    "pomodoro_fin": ["¡Tiempo! Descansa {descanso} min, te lo ganaste."],
    "descanso_fin": ["Se acabó el descanso. ¿Otro pomodoro?"],
    "pomodoro_parar": ["Pomodoro detenido."],
    "pomodoro_nada": ["No hay ningún pomodoro activo."],
    "pomodoro_tiempo": ["Quedan {restante} de {fase}."],
    "responder_saludo": ["¡Hola, {nombre}!", "Hey, {nombre}."],
    "responder_baile": ["¡Qué buen ritmo!", "Jaja, ¡qué bien bailas!"],
    "reaccion_habilidad": ["¡Wow!", "¿Eso fue una habilidad?", "¡Increíble, {nombre}!"],
    "recordatorio_ok": ["Anotado, te aviso en {min} min: {texto}"],
    "recordatorio": ["Recordatorio: {texto}"],
    "recordatorio_tarde": ["Se te pasó esto: {texto}"],
    "reac_codigo": ["Qué buen código. Sigue así.", "Programando, ¿eh? Concentración total."],
    "reac_video": ["¿Qué estás viendo? Se ve interesante.", "Un descanso con videos, te lo mereces."],
    "reac_juego": ["¡A jugar! Diviértete.", "Que gane el mejor. ¡Suerte!"],
    "reac_chat": ["Saluda a quien esté al otro lado de mi parte.", "Hablando con alguien, ¿eh?"],
    "reac_doc": ["Ese documento va quedando muy bien.", "Qué aplicado estás hoy."],
    "reac_musica": ["Buena música.", "Qué buena canción, sube el volumen."],
    "reac_redes": ["Mucho scroll... ¿y tus pendientes?", "Un ratito de redes está bien, no más."],
    "idle": ["¿Sigues ahí?", "Te fuiste... aquí te espero."],
    "vuelve": ["¡Volviste! Te esperaba.", "Bienvenido de vuelta."],
    "tarde": ["Es muy tarde, deberías dormir.", "¿Sigues despierto? A descansar."],
    "descanso": ["Llevas horas seguidas. Haz una pausa.", "Estira las piernas y bebe agua."],
}


SONIDOS_GATO = ["Miau~", "Prrr...", "¡Miau!", "*ronronea*", "*mueve la cola*"]
# Un personaje con "habla": false (un gato, por ejemplo) solo maulla y hace gestos; los avisos con datos conservan el dato.
FRASES_MUDO = {cat: list(SONIDOS_GATO) for cat in FRASES_DEFECTO}
FRASES_MUDO.update({
    "mouse": ["¿Miau?", "*te mira fijamente*", "Prrr..."],
    "aterrizar": ["¡Miau!", "*se acomoda*"],
    "posarse": ["*se acurruca*", "Prrr..."],
    "magia": ["¡MIAUUU!", "*le da la locura*"],
    "choque": ["¡Fshh!", "¡Miau!"],
    "hola_otro": ["Miau~ {nombre}", "*se frota contra {nombre}*"],
    "bailar": ["*mueve la cola*", "Miau miau~"],
    "volar": ["¡Miau!"],
    "pomodoro_inicio": ["¡Miau! {min} min de concentración."],
    "pomodoro_mitad": ["*ronronea* Ya vas por la mitad."],
    "pomodoro_fin": ["¡Miau! Descansa {descanso} min."],
    "descanso_fin": ["¡Miau! A trabajar otra vez."],
    "pomodoro_parar": ["*bosteza* Miau..."],
    "pomodoro_nada": ["Miau... no hay pomodoro."],
    "pomodoro_tiempo": ["Miau. Quedan {restante} de {fase}."],
    "responder_saludo": ["¡Miau, {nombre}!", "*ronronea* {nombre}"],
    "responder_baile": ["*mueve la cola*", "Miau miau~"],
    "reaccion_habilidad": ["¡Miau!", "*se queda mirando con los ojos grandes*"],
    "recordatorio_ok": ["Miau. En {min} min: {texto}"],
    "recordatorio": ["¡Miau! {texto}"],
    "recordatorio_tarde": ["¡Miau! Se pasó: {texto}"],
    "reac_codigo": ["*mira la pantalla con curiosidad*", "Prrr..."],
    "reac_video": ["*se queda mirando fijo la pantalla*", "Miau?"],
    "reac_juego": ["*mueve la cola emocionado*", "¡Miau!"],
    "reac_chat": ["¿Miau?", "*se sienta a esperar*"],
    "reac_doc": ["*se sienta a mirar*", "Prrr..."],
    "reac_musica": ["*mueve la cabeza al ritmo*", "Miau~"],
    "reac_redes": ["*se estira*", "Miau..."],
    "idle": ["*se hace bolita y duerme* Zzz", "Zzz... prrr"],
    "vuelve": ["¡Miau! *ronronea*", "*corre a recibirte*"],
    "tarde": ["*bosteza* Miau...", "Zzz... miau"],
    "descanso": ["*se estira muy largo*", "Miau... ¿descansamos?"],
})


class Voz:
    """Frases de un personaje por situacion. Usa las del config.json ('frases') y,
    donde falten, las de FRASES_DEFECTO, asi un personaje nuevo siempre tiene voz."""

    def __init__(self, config):
        propias = config.get("frases") or {}
        base_frases = FRASES_DEFECTO if config.get("habla", True) else FRASES_MUDO
        self.frases = {cat: list(propias.get(cat) or base) for cat, base in base_frases.items()}
        self._ultima = {}

    def decir(self, categoria, **datos):
        opciones = self.frases.get(categoria) or [""]
        if len(opciones) > 1:
            opciones = [o for o in opciones if o != self._ultima.get(categoria)] or opciones
        elegida = random.choice(opciones)
        self._ultima[categoria] = elegida
        try:
            return elegida.format(**datos)
        except (KeyError, IndexError):
            return elegida
