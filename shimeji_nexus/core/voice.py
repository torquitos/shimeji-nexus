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
}


class Voz:
    """Frases de un personaje por situacion. Usa las del config.json ('frases') y,
    donde falten, las de FRASES_DEFECTO, asi un personaje nuevo siempre tiene voz."""

    def __init__(self, config):
        propias = config.get("frases") or {}
        self.frases = {cat: list(propias.get(cat) or base) for cat, base in FRASES_DEFECTO.items()}
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
