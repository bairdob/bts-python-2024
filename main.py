import copy
import distutils
import xml.etree.ElementTree as ET
from enum import Enum
from pathlib import Path
from pprint import pprint
from typing import Tuple, List


class Types(Enum):
    """Енам тегов xml."""

    CLASS = 'class'
    ATTRIBUTE = 'attribute'
    AGGREGATION = 'aggregation'


class AggregationElement:
    """Класс, отвечающий за тэг Aggregation."""

    source: str = ...
    """Класс источник"""
    target: str = ...
    """Целевой класс"""
    sourceMultiplicity: str = ...
    """Множество источника"""
    targetMultiplicity: int = ...
    """Множество цели"""

    def __init__(self, element):
        """
        :param element: xml элемент
        """
        self.source = element.get('source')
        self.target = element.get('target')
        self.sourceMultiplicity = element.get('sourceMultiplicity')
        self.targetMultiplicity = int(element.get('targetMultiplicity'))

    def to_dict(self):
        """Получаем словарь полей класса."""
        return self.__dict__

    def __repr__(self):
        return '<{cls_name}({data})>'.format(cls_name=self.__class__.__name__,
                                             data=', '.join(('{}={}'.format(k, v) for k, v in self.__dict__.items())))


class ClassElement:
    """Класс, отвечающий за тэг Class."""

    name: str = ...
    """Имя"""
    isRoot: bool = ...
    """Корень"""
    documentation: str = ...
    """Документация"""
    attributes: list = ...
    """Аттрибуты"""
    max: str = ...  # str(int)
    """Максимальное значение"""
    min: str = ...  # str(int)
    """Минимальное значение"""
    __DELIMETER = '..'
    """Разделитель поля sourceMultiplicity"""

    def __init__(self, element: ET.Element):
        """
        :param element: xml элемент
        """
        self.name = element.get('name')
        self.isRoot = bool(distutils.util.strtobool(element.get('isRoot')))
        self.documentation = element.get('documentation')
        self.attributes = []
        for child in element:
            if child.tag.lower() == Types.ATTRIBUTE.value:
                self.attributes.append(child.attrib)

    def __repr__(self):
        return '<{cls_name}({data})>'.format(cls_name=self.__class__.__name__,
                                             data=', '.join(('{}={}'.format(k, v) for k, v in self.__dict__.items())))

    def to_dict(self):
        """Получаем словарь полей класса с переименованием."""
        dict_copy = copy.deepcopy(self.__dict__)

        # переименование ключей
        dict_copy['parameters'] = dict_copy.pop('attributes')
        dict_copy['class'] = dict_copy.pop('name')

        return dict_copy

    def update_attributes(self, attribute: AggregationElement) -> None:
        """Обновляем аттрибуты тега Aggregation"""
        self.attributes.append({"name": attribute.source, "type": "class"})

    def update_min_max(self, attribute: AggregationElement) -> None:
        """Обновляем min, max тега Aggregation"""
        if self.__DELIMETER in attribute.sourceMultiplicity:
            min_src, max_src = map(int, attribute.sourceMultiplicity.split(self.__DELIMETER))
        else:
            min_src, max_src = int(attribute.sourceMultiplicity), int(attribute.sourceMultiplicity)
        self.min, self.max = str(min_src * attribute.targetMultiplicity), str(max_src * attribute.targetMultiplicity)


class XMLParser:
    """Парсер xml файла. Извлекает необходимые аттрибуты."""

    def __init__(self, file_path: str):
        """
        :param file_path: абсолютный путь до файла
        """
        self.root = ET.parse(file_path).getroot()

    def extract_classes_and_aggregations(self) -> Tuple[List[ClassElement], List[AggregationElement]]:
        """
        Извлекает из документа классы и свойства.

        :return: (список элементов тэга Class, список элементов тэга Aggregation)
        """
        classes = []
        aggregations = []

        for element in self.root:
            if element.tag.lower() == Types.CLASS.value:
                classes.append(ClassElement(element))
            elif element.tag.lower() == Types.AGGREGATION.value:
                aggregations.append(AggregationElement(element))
        return classes, aggregations


def main():
    PATH_TO_XML = Path(__file__).parent.joinpath('input', 'impulse_test_input.xml')
    parser = XMLParser(PATH_TO_XML)
    classes, aggregations = parser.extract_classes_and_aggregations()

    for class_ in classes:
        for aggregation in aggregations:
            if class_.name == aggregation.target:
                class_.update_attributes(aggregation)
            if class_.name == aggregation.source:
                class_.update_min_max(aggregation)

    for class_ in classes:
        print("________")
        pprint(class_.to_dict())
        print("________")


if __name__ == '__main__':
    main()
