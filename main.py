import xml.etree.ElementTree as ET
from enum import Enum
from pathlib import Path
from pprint import pprint

PATH_TO_XML = Path(__file__).parent.joinpath('input', 'impulse_test_input.xml')
tree = ET.parse(PATH_TO_XML)
root = tree.getroot()


class Types(Enum):
    CLASS = 'class'
    ATTRIBUTE = 'attribute'
    AGGREGATION = 'aggregation'


classes = set()
aggregations = set()

for element in root:
    # print(element.tag, element.attrib)
    if element.tag.lower() == Types.CLASS.value:
        childs = list()
        # у поля Class может быть элемент Attribute
        for child in element:
            childs.append(child.attrib)
        element.attrib.update({Types.ATTRIBUTE.value: childs})
        classes.add(element)
    elif element.tag.lower() == Types.AGGREGATION.value:
        aggregations.add(element)

for class_ in classes:
    for aggregation in aggregations:
        if aggregation.get('source') == class_.get('name'):
            class_.attrib.update(aggregation.attrib)

# for class_ in classes:
#     pprint(class_.attrib)

# все уникальные имена классов
class_names = set(class_.attrib['name'] for class_ in classes)
# print(class_names)

DELIMITER = '..'
for class_ in classes:
    class_.attrib['parameters'] = class_.attrib.pop('attribute')
    class_.attrib['class'] = class_.attrib.pop('name')

    try:
        multiplier = int(class_.attrib.get('targetMultiplicity'))
    except TypeError as e:
        pass
    else:
        class_.attrib.pop('targetMultiplicity')
        try:
            min_src, max_src = map(int, class_.attrib.get('sourceMultiplicity').split(DELIMITER))
        # если рутовый
        except AttributeError:
            min_src, max_src = class_.attrib.get('sourceMultiplicity'), class_.attrib.get('sourceMultiplicity')
        except ValueError as e:
            min_src, max_src = class_.attrib.get('sourceMultiplicity'), class_.attrib.get('sourceMultiplicity')
        finally:
            class_.attrib['min'], class_.attrib['max'] = str(min_src*multiplier), str(max_src*multiplier)
        class_.attrib.pop('sourceMultiplicity')

    if class_.attrib.get('source') == class_.attrib.get('class'):
        class_.attrib.pop('source')

    cur_class = class_.attrib.get('class')

    # print('______________')
    # pprint(class_.attrib)
    # print('______________')


result_dicts = dict()

for class_ in classes:
    result_dicts[class_.attrib.get('class')] = class_.attrib


for class_ in classes:
    if class_.attrib.get('target') in class_names and class_.attrib.get('target') != class_.attrib.get('source'):
        result_dicts[class_.attrib.get('target')]['parameters'].append(
            { "name": class_.attrib.get('class'), "type": "class" }
        )

for _, v in result_dicts.items():
    try:
        del v['target']
    except Exception:
        pass


for k, v in result_dicts.items():
    print('______________')
    pprint(v)
    print('______________')
