from PySide2.QtCore import QObject
from numpy import equal
from shape_core.pcb_manager import PcbObj
from shape_core.path_manager import MachinePath
from shape_core.gcode_manager import GCoder
import os
import logging
import traceback

logger = logging.getLogger(__name__)


class ViewController(QObject):
    def __init__(self, settings):
        super(ViewController, self).__init__()
        self.pcb = PcbObj()
        self.settings = settings

    def load_new_layer(self, layer, file_path):
        # takes layer name and file path
        # returns layer info and file type flag

        grb_tags = self.pcb.GBR_KEYS
        exc_tags = self.pcb.EXN_KEYS
        if layer in grb_tags:
            self.pcb.load_gerber(file_path, layer)
            loaded_layer = self.pcb.get_gerber_layer(layer)
            return [loaded_layer, False]
        elif layer in exc_tags:
            self.pcb.load_excellon(file_path, layer)
            loaded_layer = self.pcb.get_excellon_layer(layer)
            return [loaded_layer, True]
        else:
            logger.error("Layer not in Gerber or Excellon Tags.")
            return [None, None]

    def generate_new_path(self, tag, cfg, machining_type):
        if machining_type == "gerber" or machining_type == "profile" or machining_type == "slot":
            machining_layer = self.pcb.get_gerber_layer(tag)
        elif machining_type == "drill":
            machining_layer = self.pcb.get_excellon_layer(tag)
        else:
            logger.error("Wrong machining type")
        path = MachinePath(tag, machining_type)
        path.load_geom(machining_layer[0])
        path.load_cfg(cfg)
        path.execute()
        new_paths = path.get_path()
        return new_paths

    def generate_new_gcode_file(self, tag, cfg, machining_type, path):
        gcoder = GCoder(tag, machining_type)
        gcoder.load_cfg(cfg)
        gcoder.load_path(path)
        if gcoder.compute():
            gcode_filename = gcoder.get_file_name()
            gcode_path = os.path.join(self.settings.gcf_settings.gcode_folder, gcode_filename)
            gcoder.write(gcode_path)
        else:
            logging.error("Gcode generation failed.")
