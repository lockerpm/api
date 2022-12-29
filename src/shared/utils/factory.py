import sys


def to_class_name_style(snake_string):
    components = snake_string.split('_')
    return ''.join(x.title() for x in components)


def factory(module_name, *args):
    try:
        __import__(module_name)
        class_name = to_class_name_style(module_name.split('.')[-1])
        module_inst = sys.modules[module_name]
        a_class = getattr(module_inst, class_name)
        return a_class(*args)
    except (ModuleNotFoundError, AttributeError):
        return None
