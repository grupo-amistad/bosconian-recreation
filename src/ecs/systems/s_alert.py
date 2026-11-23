import esper
from src.ecs.components.c_alert import CAlert
from src.ui.alert_system import AlertController


def system_alert(world: esper.World, delta_time: float, alert_controller: AlertController) -> None:
    """Actualiza las entidades con CAlert usando la máquina de estados AlertController."""
    for _, c_alert in world.get_component(CAlert):
        alert_controller.update(c_alert, delta_time)