from core.hardware import Printer

printer = Printer(3)
printer.ip = "130.13.1.66"
printer.port = 9100
printer.print_via_ethernet(zpl)
