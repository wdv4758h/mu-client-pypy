from rpython.tool.ansi_print import AnsiLogger
from rpython.tool.ansi_mandelbrot import Driver

log = AnsiLogger("MuBundleGen")
__mdb = Driver()


def get_rmu():
    from rpython.config.translationoption import get_translation_config
    config = get_translation_config()
    log.info('vmargs: ' + config.mu.vmargs)


class MuBundleGen:
    def __init__(self, db):
        pass

    def bundlegen(self, bdlpath):
        pass