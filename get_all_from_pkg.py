import importlib
import inspect
import json
import pkgutil
import os
from time import sleep
import sys
from threading import Thread

PACKAGE_SUBPACKAGE = 'package_or_subpackage'
MODULE = 'module'
CLASS_SUBCLASS = 'class_or_subclass'
ATTRIBUTE = 'attribute'
FUNCTION = 'function'
UNKNOWN = 'unknown'


def extract_module_info(module_name):
    counter = 0
    try:
        
        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            print(str(e).replace('\n',' '))
            return {}
          
        module_info = {"name": module_name,"type":"","members": []}
       
        module_info['type'] = get_package_type(module_name)

        for name, obj in inspect.getmembers(module):

            if name.startswith('__'):
                continue
            member_info = {"type": type(obj).__name__}

            obj_help = inspect.getdoc(obj)
                                
            if inspect.isclass(obj):
                member_info['import'] = f'from {module_name} import {name}'
                member_info["attributes"] = []
                member_info["methods"] = []
                member_info["functions"] = []
                

                attrs_list_1 = []
                for attr_name, package_obj in inspect.getmembers(obj):
                    if  attr_name.startswith('__'):
                        continue
                    #package_obj = inspect.getmodule(package_name+'.'+attr_name)
                    package_obj_help = inspect.getdoc(package_obj)
                    elem = {'name':attr_name, 
                            'type':type(package_obj).__name__, 
                            'help':package_obj_help,
                            'callable':callable(package_obj)}
                    if inspect.isfunction(package_obj):
                        elem['parametters'] = (get_function_parameters(package_obj))
                    attrs_list_1.append(elem)

                mem_elem = {'name':name, 
                            'type':type(obj).__name__, 
                            'import':f'from {module_name} import {name}',
                            'help':obj_help,
                            "attributes":attrs_list_1}
                module_info["members"].append(mem_elem)
            elif inspect.ismodule(obj):
                all_info = extract_module_info(module_name+'.'+name)
                if all_info:
                    mem_elem = {'name':name, 
                                'type':type(obj).__name__,
                                'import':f'import {name}',
                                'help':obj_help ,
                                'members':all_info
                                }
                else:
                    mem_elem = {'name':name, 'type':type(obj).__name__,
                                'import':f'import {name}',
                                'help':obj_help}
                if inspect.isfunction(obj):
                    mem_elem['parametters'] = get_function_parameters(funct=obj)
                mem_elem['callable'] = callable(obj)
                module_info["members"].append(mem_elem)

           
                
                counter+=1
        return module_info

    except ImportError:
        print('error')
        return {}
    
def get_class_attributes(class_string):
    try:
        module_name, class_name = class_string.rsplit('.', 1)
        module = importlib.import_module(module_name)
        class_obj = getattr(module, class_name)
        attributes = []

        for attr_name in dir(class_obj):
            attr_value = getattr(class_obj, attr_name)
            if not attr_name.startswith("__"):
                tmp_dict = {'name': attr_name,
                            'callable': callable(attr_value),
                            'type': get_package_type(class_string+'.'+attr_name),
                            'help':inspect.getdoc(attr_value)}
                if get_package_type(class_string+'.'+attr_name) == FUNCTION :
                    tmp_dict['parametters'] = get_function_parameters(attr_value)
                attributes.append(tmp_dict)

        return attributes

    except (ImportError, AttributeError):
        print(f"Class {class_string} not found.")
        return []




def progress(count, total, suffix=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
    sys.stdout.flush()  # As suggested by Rom Ruben


def one_line_progress(st):
    sleep(.5)
    sys.stdout.write('%s\r' % (st))
    sys.stdout.flush()  # As suggested by Rom Ruben


def extract_package_info(package_name):
    package_info = {"name": package_name, 'import':'',"type":"","help":""}
    list_checker = []
    try:
        try:
            package = importlib.import_module(package_name)
        except:
            package = get_nested_attribute(package_name)


        package_info['type'] = get_package_type(package_name)
        package_info['help'] = inspect.getdoc(package)
        
      
        other_attrs = []
        for item in dir(package):
            if item.startswith('__') :
                continue
            item_pkg_name = package_name+'.'+item
            item_obj = package_str_to_object(item_pkg_name)
            temp_dict = {"name": item, 
                         "package_name": item_pkg_name,
                         'import':f'from {package_name} import {item}',
                         "type": type(item_obj).__name__,
                         "help": inspect.getdoc(item_obj)
                         }
            if inspect.isfunction(item_obj):
                temp_dict['parametters'] = get_function_parameters(item_obj)
            elif inspect.isclass(item_obj):
                temp_dict['import'] = f'from {package_name} import {item}'
                temp_dict['attributes'] = get_class_attributes(item_pkg_name)
            elif inspect.ismodule(item_obj):
                item_members = extract_module_info(item_pkg_name)
                temp_dict['import'] = f'import {package_name}'
                temp_dict['members'] = item_members.get('members', [])
                
                
            list_checker.append(item)
            other_attrs.append(temp_dict)
        
        package_info['members'] = other_attrs


        if get_package_type(package_name) == PACKAGE_SUBPACKAGE:
            m_dict = {}
            m_list = []
            no_dup_list = []
            for module_obj in list(pkgutil.walk_packages(package.__path__, package_name + '.')):
                module_name = module_obj.name
                if module_name in no_dup_list:
                    continue
                if not module_name.startswith(package_name):
                    continue
                module_info = extract_module_info(module_name)
                
                #m_dict[module_name] = module_info
                m_list.append(module_info)
                no_dup_list.append(module_name)
            package_info['import'] = f'import {package_name}'
            package_info["modules"] = m_list
            
            
        elif get_package_type(package_name) == CLASS_SUBCLASS:
            
            pkg, name = package_name.split('.', 1)
            package_info['import'] = f'from {pkg} import {name}'
            package_info["members"] = get_class_attributes(package_name)
            
        elif get_package_type(package_name) == FUNCTION:
            package_info["parametters"] = get_function_parameters(package_name)

        elif get_package_type(package_name) == MODULE:
            
            module_info = extract_module_info(package_name)
            package_info['import'] = f'import {package_name}'
            m_list = []
            for md in module_info['members']:
                m_list.append(md)
            package_info["members"] = m_list
            
    except ImportError as e:
        print(f'error {e}')
        pass  # Ignore built-in modules that don't have a __path__

    return package_info

def get_function_parameters(funct):
    try:
        if inspect.isfunction(funct):
            signature = inspect.signature(funct)
            parameters = list(signature.parameters.keys())
            return parameters
        else:
            return []
    except (ModuleNotFoundError, AttributeError):
        return []

def package_str_to_object(full_path):
    parts = full_path.split('.')
    
    if len(parts) == 1:
        return __import__(full_path)
    
    current_path = parts[0]
    current_object = __import__(current_path)
    
    for part in parts[1:]:
        try:
            current_object = getattr(current_object, part)
        except AttributeError:
            current_path += "." + part
            current_object = __import__(current_path)
    
    return current_object

def get_package_type(entity_name):
    typ = ''
    try:
        # Attempt to import the entity
        entity = importlib.import_module(entity_name)
        
        # Check if it's a package or subpackage
        if hasattr(entity, '__path__'):
            typ = PACKAGE_SUBPACKAGE
        else:
            typ = MODULE
        
    except ImportError:
        try:
            module_name, class_name = entity_name.rsplit('.', 1)
            module = importlib.import_module(module_name)
            class_obj = getattr(module, class_name)
            typ = CLASS_SUBCLASS
        except (ImportError, AttributeError):
            try:
                pkgname, name = module_name.rsplit('.', 1)
                module = importlib.import_module(pkgname)
                obj = getattr(module, name)
                obj2 = getattr(obj, class_name)
                if callable(obj2):
                    typ = FUNCTION
                else:
                    typ = ATTRIBUTE
            except:
                typ = UNKNOWN
    return typ


def get_nested_attribute(attribute_path):
    parts = attribute_path.split('.')
    attribute = None

    for part in parts:
        if attribute is None:
            attribute = globals().get(part, None)
        else:
            attribute = getattr(attribute, part, None)

        if attribute is None:
            break

    return attribute

if __name__ == "__main__":
    
    ''' list_uix_packages = ["kivy.uix.accordion","kivy.uix.actionbar","kivy.uix.anchorlayout","kivy.uix.behaviors","kivy.uix.boxlayout","kivy.uix.bubble","kivy.uix.button","kivy.uix.camera","kivy.uix.carousel","kivy.uix.checkbox","kivy.uix.codeinput","kivy.uix.colorpicker","kivy.uix.dropdown","kivy.uix.effectwidget","kivy.uix.filechooser","kivy.uix.floatlayout","kivy.uix.gesturesurface","kivy.uix.gridlayout","kivy.uix.image","kivy.uix.label","kivy.uix.layout","kivy.uix.modalview","kivy.uix.pagelayout","kivy.uix.popup","kivy.uix.progressbar","kivy.uix.recycleboxlayout","kivy.uix.recyclegridlayout","kivy.uix.recyclelayout","kivy.uix.recycleview","kivy.uix.relativelayout","kivy.uix.scatter","kivy.uix.scatterlayout","kivy.uix.screenmanager","kivy.uix.scrollview","kivy.uix.settings","kivy.uix.slider","kivy.uix.spinner","kivy.uix.splitter","kivy.uix.stacklayout","kivy.uix.stencilview","kivy.uix.switch","kivy.uix.tabbedpanel","kivy.uix.textinput","kivy.uix.togglebutton","kivy.uix.treeview","kivy.uix.video","kivy.uix.videoplayer","kivy.uix.vkeyboard","kivy.uix.widget"]

    package_name = "kivy.uix"
    
    for uix in list_uix_packages:
        try:        
            package_info = extract_package_info(uix)
            with open(f"/home/hichemkanon/Downloads/uix_packages/{uix}.json", "w") as json_file:
                json.dump(package_info, json_file, indent=4)
            print('extracted '+ uix)
        except:
            print('cant extract '+ uix)'''
   

    pkg = 'os'
    package_info = extract_package_info(pkg)
    with open(f"os.json", "w") as json_file:
        json.dump(package_info, json_file, indent=4)