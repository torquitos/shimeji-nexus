from shimeji_nexus.pet.habilidades.brasas import BrasasMixin
from shimeji_nexus.pet.habilidades.cinematica import CinematicaMixin
from shimeji_nexus.pet.habilidades.espiral import EspiralMixin
from shimeji_nexus.pet.habilidades.orbitar import OrbitarMixin
from shimeji_nexus.pet.habilidades.rayo import RayoMixin
from shimeji_nexus.pet.habilidades.zoomies import ZoomiesMixin


class FormasMixin(CinematicaMixin, OrbitarMixin, BrasasMixin, EspiralMixin, RayoMixin, ZoomiesMixin):
    """Efectos grandes que se dibujan en el Lienzo: el corte de camara y la tecnica de cada forma."""
