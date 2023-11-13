from krita import DockWidgetFactory, DockWidgetFactoryBase
from .blender_krita_link import BlenderKritaLink

DOCKER_ID = 'template_docker'
instance = Krita.instance()
dock_widget_factory = DockWidgetFactory(DOCKER_ID,
DockWidgetFactoryBase.DockRight,
BlenderKritaLink)

instance.addDockWidgetFactory(dock_widget_factory)