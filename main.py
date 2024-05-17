import copy
import distutils
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Self


class XMLTagsEnum(Enum):
    """Енам тегов xml."""

    CLASS = 'class'
    ATTRIBUTE = 'attribute'
    AGGREGATION = 'aggregation'


@dataclass(slots=True, frozen=True)
class Attribute:
    """Датакласс тэга Attribute."""

    name: str
    """Имя"""
    type: str
    """Тип"""


@dataclass(slots=True, frozen=True)
class AggregationElement:
    """Класс, отвечающий за тэг Aggregation."""

    source: str
    """Класс источник"""
    target: str
    """Целевой класс"""
    sourceMultiplicity: str
    """Мощность источника"""
    targetMultiplicity: int
    """Мощность цели"""

    @classmethod
    def from_xml_element(cls, element: ET.Element) -> Self:
        """
        Получаем объект класса из XML элемента.

        :param element: xml элемент
        :return: инстанс класса
        """
        return cls(
            source=element.get('source'),
            target=element.get('target'),
            sourceMultiplicity=element.get('sourceMultiplicity'),
            targetMultiplicity=int(element.get('targetMultiplicity')),
        )


@dataclass
class ClassElement:
    """Класс, отвечающий за тэг Class."""

    name: str
    """Имя"""
    isRoot: bool
    """Корень"""
    documentation: str
    """Документация"""
    attributes: list[Attribute] = field(default_factory=list)
    """Аттрибуты"""
    max: str = ""
    """Максимальное значение"""
    min: str = ""
    """Минимальное значение"""
    __DELIMETER = '..'
    """Разделитель поля sourceMultiplicity"""

    @classmethod
    def from_xml_element(cls, element: ET.Element) -> Self:
        """
        Получаем объект класса из XML элемента.

        :param element: xml элемент
        :return: инстанс класса
        """
        attributes = [
            Attribute(child.attrib.get('name'), child.attrib.get('type'))
            for child in element
            if child.tag.lower() == XMLTagsEnum.ATTRIBUTE.value
        ]
        return cls(
            name=element.get('name'),
            isRoot=bool(distutils.util.strtobool(element.get('isRoot'))),
            documentation=element.get('documentation'),
            attributes=attributes
        )

    def to_dict(self) -> dict:
        """Получаем словарь полей класса с переименованием."""
        dict_copy = copy.deepcopy(asdict(self))

        # переименование ключей
        dict_copy['parameters'] = dict_copy.pop('attributes')
        dict_copy['class'] = dict_copy.pop('name')

        return dict_copy

    def update_attributes(self, attribute: AggregationElement) -> None:
        """Обновляем аттрибуты тега Aggregation"""
        self.attributes.append(Attribute(name=attribute.source, type="class"))

    def update_min_max(self, attribute: AggregationElement) -> None:
        """Обновляем min, max тега Aggregation"""
        if self.__DELIMETER in attribute.sourceMultiplicity:
            min_src, max_src = map(int, attribute.sourceMultiplicity.split(self.__DELIMETER))
        else:
            min_src, max_src = int(attribute.sourceMultiplicity), int(attribute.sourceMultiplicity)
        self.min, self.max = str(min_src * attribute.targetMultiplicity), str(max_src * attribute.targetMultiplicity)


class XMLParser:
    """Парсер xml файла. Извлекает необходимые аттрибуты."""

    classes: dict[str, ClassElement] = {}
    """Словарь классов тэга Class"""

    def __init__(self, file_path: Path):
        """
        :param file_path: абсолютный путь до файла
        """
        self.root = ET.parse(file_path).getroot()

    def _extract_classes_and_aggregations(self) -> tuple[list[ClassElement], list[AggregationElement]]:
        """
        Извлекает из документа классы и свойства.

        :return: (список элементов тэга Class, список элементов тэга Aggregation)
        """
        classes = []
        aggregations = []

        for element in self.root:
            if element.tag.lower() == XMLTagsEnum.CLASS.value:
                classes.append(ClassElement.from_xml_element(element))
            elif element.tag.lower() == XMLTagsEnum.AGGREGATION.value:
                aggregations.append(AggregationElement.from_xml_element(element))
        return classes, aggregations

    def parse(self):
        """Получаем классы с дополненными полями из тэга Aggregation."""
        classes, aggregations = self._extract_classes_and_aggregations()

        for class_ in classes:
            for aggregation in aggregations:
                if class_.name == aggregation.target:
                    class_.update_attributes(aggregation)
                if class_.name == aggregation.source:
                    class_.update_min_max(aggregation)
        self.classes = {class_.name: class_ for class_ in classes}

    def to_meta(self) -> list[dict[str, str | bool | list[dict]]]:
        """Получаем список классов для загрузки в meta.json."""
        return [class_.to_dict() for class_ in self.classes.values()]

    def _add_attributes_to_element(self, element: ET.Element, attributes: list) -> None:
        """
        Рекурсивно добавляет аттрибуты к элементу.

        :param element: xml элемент к которому добавляем аттрибуты
        :param attributes: список аттрибутов
        """
        for attribute in attributes:
            if attribute.type != XMLTagsEnum.CLASS.value:
                param_elem = ET.SubElement(element, attribute.name)
                param_elem.text = attribute.type
            else:
                class_elem = ET.SubElement(element, attribute.name)
                nested_class = self.classes[attribute.name]
                self._add_attributes_to_element(class_elem, nested_class.attributes)

    def to_config(self) -> ET.Element:
        """
        Получаем дерево xml элементов для загрузки в config.xml.

        :return: элемент с заполненными данными
        """
        try:
            root_class = next(class_ for class_ in self.classes.values() if class_.isRoot)
        except StopIteration:
            raise ValueError("В XML-документе не обнаружен корневой класс.")

        root_element = ET.Element(root_class.name)
        self._add_attributes_to_element(root_element, root_class.attributes)

        return root_element


def main():
    from xml.dom import minidom
    PATH_TO_XML = Path(__file__).parent.joinpath('input', 'impulse_test_input.xml')
    parser = XMLParser(PATH_TO_XML)
    parser.parse()
    pprint(parser.to_meta())


if __name__ == '__main__':
    main()
